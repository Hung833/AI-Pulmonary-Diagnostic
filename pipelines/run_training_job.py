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
except ImportError as err:
    logging.critical(f"Lỗi nạp thư viện SageMaker SDK: {err}")
    sys.exit(1)

def get_execution_role(account_id: str) -> str:
    return f"arn:aws:iam::{account_id}:role/SageMaker-PulmonarySuite-ExecutionRole"

def run_local_fallback_training(bucket_name: str, entry_point: Path):
    logging.warning("=== KÍCH HOẠT CHẾ ĐỘ PHỤC HỒI: HUẤN LUYỆN LOCAL KẾT HỢP S3 SYNC ===")
    
    local_data_dir = Path("/tmp/processed-data")
    local_data_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info("Đang tải dữ liệu tiền xử lý từ S3 về môi trường cục bộ...")
    subprocess.run(["aws", "s3", "sync", f"s3://{bucket_name}/processed-data/", str(local_data_dir)], check=True)
    
    local_model_dir = Path("/tmp/model")
    local_model_dir.mkdir(parents=True, exist_ok=True)
    
    env = os.environ.copy()
    env["SM_CHANNEL_TRAIN"] = str(local_data_dir / "train")
    env["SM_CHANNEL_VAL"] = str(local_data_dir / "validation")
    env["SM_MODEL_DIR"] = str(local_model_dir)
    
    logging.info("Đang thực thi huấn luyện DenseNet121...")
    result = subprocess.run([sys.executable, str(entry_point), "--epochs", "3", "--batch-size", "16"], env=env)
    
    if result.returncode != 0:
        logging.critical("Lỗi huấn luyện mô hình cục bộ!")
        sys.exit(1)
        
    tar_path = Path("/tmp/model.tar.gz")
    logging.info(f"Đang đóng gói trọng số mô hình vào {tar_path}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(local_model_dir, arcname=".")
        
    s3_target_key = "output/model.tar.gz"
    s3_client = boto3.client("s3")
    logging.info(f"Đang đẩy file {tar_path} lên s3://{bucket_name}/{s3_target_key}...")
    s3_client.upload_file(str(tar_path), bucket_name, s3_target_key)
    
    logging.info("=== TRAIN JOB HOÀN TẤT VÀ MÔ HÌNH MODEL.TAR.GZ ĐÃ NẰM TRÊN S3! ===")

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

    if not ENTRY_POINT_SCRIPT.exists():
        logging.error(f"Không tìm thấy file script huấn luyện tại: {ENTRY_POINT_SCRIPT}")
        sys.exit(1)

    metric_definitions = [
        {"Name": "train:loss", "Regex": "loss: ([0-9\\.]+)"},
        {"Name": "train:accuracy", "Regex": "accuracy: ([0-9\\.]+)"},
        {"Name": "train:recall", "Regex": "recall: ([0-9\\.]+)"},
        {"Name": "val:loss", "Regex": "val_loss: ([0-9\\.]+)"},
        {"Name": "val:accuracy", "Regex": "val_accuracy: ([0-9\\.]+)"},
        {"Name": "val:recall", "Regex": "val_recall: ([0-9\\.]+)"},
    ]

    candidate_instances = ["ml.m4.xlarge", "ml.c4.xlarge"]
    s3_train = f"s3://{bucket_name}/processed-data/train"
    s3_val = f"s3://{bucket_name}/processed-data/validation"

    for instance_type in candidate_instances:
        logging.info(f"=== ĐANG THỬ KÍCH HOẠT SAGEMAKER JOB VỚI INSTANCE: {instance_type} ===")

        estimator = TensorFlow(
            entry_point=str(ENTRY_POINT_SCRIPT),
            role=role_arn,
            instance_count=1,
            instance_type=instance_type,
            framework_version="2.12.0",
            py_version="py310",
            script_mode=True,
            hyperparameters={"epochs": 3, "batch-size": 16, "learning-rate": 0.001},
            metric_definitions=metric_definitions,
            max_run=600,
            volume_size=10,
            sagemaker_session=sagemaker_session
        )

        try:
            estimator.fit({"train": s3_train, "val": s3_val}, wait=True)
            logging.info(f"=== TRAINING JOB HOÀN TẤT THÀNH CÔNG TRÊN {instance_type}! ===")
            return
        except ClientError as err:
            error_code = err.response.get("Error", {}).get("Code", "")
            logging.warning(f"Cloud Instance '{instance_type}' bị bỏ qua (Mã lỗi: {error_code}).")
            continue

    run_local_fallback_training(bucket_name, ENTRY_POINT_SCRIPT)

if __name__ == "__main__":
    run_pipeline()
