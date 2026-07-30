# -*- coding: utf-8 -*-
import logging, os, shutil, sys, tarfile, boto3
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ.get("PULMONARY_S3_BUCKET", "fcaj-pulmonary-suite-data-hung2026")
MODEL_KEY = os.environ.get("PULMONARY_MODEL_KEY", "output/hpo-best-model.tar.gz")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
LOCAL_INFERENCE_SCRIPT = os.environ.get("INFERENCE_SCRIPT_PATH", str(Path(__file__).parent.parent / "src" / "inference.py"))

def validate_saved_model(target_dir: Path):
    saved_model_path = target_dir / "1" if (target_dir / "1").exists() else target_dir
    if not (saved_model_path / "saved_model.pb").exists():
        sys.exit(1)
    logging.info("✔ Validation thành công! Phát hiện cấu trúc chuẩn TFS C++ Engine.")

def repack_and_deploy():
    repack_dir = Path("/tmp/repack")
    if repack_dir.exists(): shutil.rmtree(repack_dir)
    repack_dir.mkdir(parents=True, exist_ok=True)
    
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    local_tar = Path("/tmp/hpo-best-model.tar.gz")

    try:
        logger.info(f"Đang tải {MODEL_KEY} từ S3...")
        s3_client.download_file(BUCKET_NAME, MODEL_KEY, str(local_tar))
    except ClientError as e:
        logger.critical(f"Lỗi tải model từ S3: {e}")
        sys.exit(1)

    logger.info("Đang giải nén mô hình an toàn (Vá lỗ hổng Path Traversal)...")
    with tarfile.open(local_tar, "r:gz") as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=repack_dir, filter="data")
        else:
            tar.extractall(path=repack_dir)

    root_pb = repack_dir / "saved_model.pb"
    version_1_dir = repack_dir / "1"
    if root_pb.exists():
        version_1_dir.mkdir(exist_ok=True)
        for item in list(repack_dir.iterdir()):
            if item.name not in ["code", "1"]: shutil.move(str(item), str(version_1_dir / item.name))

    validate_saved_model(repack_dir)

    code_dir = repack_dir / "code"
    code_dir.mkdir(exist_ok=True)
    src_inference = Path(LOCAL_INFERENCE_SCRIPT)
    shutil.copy(src_inference, code_dir / "inference.py")
    
    req_file = code_dir / "requirements.txt"
    with open(req_file, "w") as f:
        f.write("numpy==1.24.3\n")
        f.write("Pillow==10.0.0\n")
        f.write("requests==2.31.0\n")
    logger.info("✔ Đã chèn thành công requirements.txt (chứa numpy, Pillow, requests) vào code/.")

    new_tar = Path("/tmp/hpo-best-model-repacked.tar.gz")
    with tarfile.open(new_tar, "w:gz") as tar:
        for item in repack_dir.iterdir(): tar.add(item, arcname=item.name)

    try:
        logger.info("Đang upload Model Artifact đã chuẩn hóa lên S3...")
        s3_client.upload_file(str(new_tar), BUCKET_NAME, MODEL_KEY)
        logger.info("=== HOÀN TẤT ĐÓNG GÓI MODEL ARTIFACT! ===")
    except ClientError as e:
        logger.critical(f"Lỗi upload S3: {e}")
        sys.exit(1)

if __name__ == "__main__":
    repack_and_deploy()
