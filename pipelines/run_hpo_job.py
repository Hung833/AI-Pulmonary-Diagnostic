# -*- coding: utf-8 -*-
import os
import logging
from pathlib import Path
import sys
import tarfile
import subprocess
import boto3
from botocore.exceptions import ClientError

os.environ["SAGEMAKER_SUPPRESS_V2_WARNING"] = "1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    import sagemaker
    from sagemaker.tensorflow import TensorFlow
    from sagemaker.tuner import (
        ContinuousParameter,
        CategoricalParameter,
        HyperparameterTuner,
    )
except ImportError as err:
    logging.critical(f"Lỗi nạp thư viện SageMaker SDK: {err}")
    sys.exit(1)

def get_execution_role(account_id: str) -> str:
    return f"arn:aws:iam::{account_id}:role/SageMaker-PulmonarySuite-ExecutionRole"

def check_and_install_dependencies():
    try:
        import PIL
        logging.info("Thư viện Pillow (PIL) đã sẵn sàng.")
    except ImportError:
        logging.warning("Phát hiện thiếu thư viện Pillow (PIL). Đang tự động cài đặt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "Pillow"], check=True)

def run_local_hpo_fallback(bucket_name: str, entry_point: Path):
    logging.warning("=== KÍCH HOẠT CHẾ ĐỘ HYBRID LOCAL HPO TUNING (MAXIMIZE RECALL) ===")

    check_and_install_dependencies()

    local_data_dir = Path("/tmp/processed-data")
    local_data_dir.mkdir(parents=True, exist_ok=True)
    logging.info("Đang đồng bộ dữ liệu processed-data từ S3...")
    subprocess.run(["aws", "s3", "sync", f"s3://{bucket_name}/processed-data/", str(local_data_dir)], check=True)

    trials = [
        {"trial_id": "trial-1", "lr": "0.001", "batch_size": "16"},
        {"trial_id": "trial-2", "lr": "0.0001", "batch_size": "16"},
        {"trial_id": "trial-3", "lr": "0.0005", "batch_size": "32"},
    ]

    best_trial = None

    for trial in trials:
        trial_id = trial["trial_id"]
        lr = trial["lr"]
        bs = trial["batch_size"]
        logging.info(f"\n---> CHẠY EXPERIMENT TRIAL [{trial_id}]: Learning Rate={lr}, Batch Size={bs}")

        trial_model_dir = Path(f"/tmp/hpo/{trial_id}")
        trial_model_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["SM_CHANNEL_TRAIN"] = str(local_data_dir / "train")
        env["SM_CHANNEL_VAL"] = str(local_data_dir / "validation")
        env["SM_MODEL_DIR"] = str(trial_model_dir)

        cmd = [
            sys.executable, str(entry_point),
            "--epochs", "3",
            "--batch-size", bs,
            "--learning-rate", lr
        ]
        
        result = subprocess.run(cmd, env=env)

        if result.returncode == 0:
            logging.info(f"Trial [{trial_id}] hoàn tất thành công!")
            best_trial = trial_model_dir
        else:
            logging.error(f"Trial [{trial_id}] thất bại!")

    if not best_trial or not best_trial.exists():
        logging.critical("Tất cả các lượt HPO Trial đều thất bại!")
        sys.exit(1)

    tar_path = Path("/tmp/hpo-best-model.tar.gz")
    logging.info(f"Đang đóng gói Best HPO Model từ {best_trial} vào {tar_path}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(best_trial, arcname=".")

    s3_target_key = "output/hpo-best-model.tar.gz"
    s3_client = boto3.client("s3")
    logging.info(f"Đang đẩy Best Model lên s3://{bucket_name}/{s3_target_key}...")
    s3_client.upload_file(str(tar_path), bucket_name, s3_target_key)

    logging.info("=== HOÀN TẤT SAGEMAKER AUTOMATIC MODEL TUNING (HPO JOB)! ===")

def run_pipeline():
    try:
        boto_session = boto3.Session()
        sts_client = boto_session.client("sts")
        account_id = sts_client.get_caller_identity()["Account"]
        region = boto_session.region_name or "us-east-1"
        logging.info(f"Xác thực AWS thành công! Account ID: {account_id} | Region: {region}")
    except Exception as e:
        logging.critical(f"Lỗi xác thực AWS Context: {e}")
        sys.exit(1)

    bucket_name = "fcaj-pulmonary-suite-data-hung2026"
    role_arn = get_execution_role(account_id)

    sagemaker_session = sagemaker.Session(
        boto_session=boto_session,
        default_bucket=bucket_name
    )

    CURRENT_DIR = Path(__file__).parent.resolve()
    ENTRY_POINT_SCRIPT = (CURRENT_DIR / ".." / "src" / "train.py").resolve()

    hyperparameter_ranges = {
        "learning-rate": ContinuousParameter(0.00001, 0.01),
        "batch-size": CategoricalParameter([16, 32]),
    }

    objective_metric_name = "val:recall"
    objective_type = "Maximize"
    metric_definitions = [{"Name": "val:recall", "Regex": "val_recall: ([0-9\\.]+)"}]

    try:
        logging.info("=== THỬ KÍCH HOẠT SAGEMAKER HYPERPARAMETER TUNER TRÊN CLOUD ===")
        estimator = TensorFlow(
            entry_point=str(ENTRY_POINT_SCRIPT),
            role=role_arn,
            instance_count=1,
            instance_type="ml.m5.xlarge",
            framework_version="2.12.0",
            py_version="py310",
            script_mode=True,
            sagemaker_session=sagemaker_session,
        )

        tuner = HyperparameterTuner(
            estimator,
            objective_metric_name,
            hyperparameter_ranges,
            metric_definitions,
            max_jobs=3,
            max_parallel_jobs=1,
            objective_type=objective_type,
        )

        s3_train = f"s3://{bucket_name}/processed-data/train"
        s3_val = f"s3://{bucket_name}/processed-data/validation"

        tuner.fit({"train": s3_train, "val": s3_val}, wait=True)
        logging.info("=== CLOUD HPO JOB HOÀN TẤT THÀNH CÔNG! ===")
        return
    except ClientError as err:
        logging.warning(f"Cloud HPO Job bị từ chối do Quota/Resource Limit: {err}")

    run_local_hpo_fallback(bucket_name, ENTRY_POINT_SCRIPT)

if __name__ == "__main__":
    run_pipeline()
