# -*- coding: utf-8 -*-
import os
import sys
import tarfile
import logging
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_diagnostics():
    bucket_name = os.getenv("PULMONARY_S3_BUCKET", "fcaj-pulmonary-suite-data-hung2026")
    model_key = os.getenv("PULMONARY_MODEL_KEY", "output/hpo-best-model.tar.gz")
    local_tar = Path("/tmp/hpo-best-model.tar.gz")
    extract_dir = Path("/tmp/check_model")

    s3_client = boto3.client("s3")
    logs_client = boto3.client("logs")

    logging.info(f"=== BƯỚC 1: Tải {model_key} từ S3 Bucket '{bucket_name}' ===")
    try:
        s3_client.download_file(bucket_name, model_key, str(local_tar))
        logging.info("Tải tệp thành công từ S3!")
    except ClientError as e:
        logging.critical(f"Không thể tải tệp từ S3: {e}")
        sys.exit(1)

    logging.info("=== BƯỚC 2: Giải nén & Kiểm tra Cấu trúc Model Artifact ===")
    if extract_dir.exists():
        import shutil
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(local_tar, "r:gz") as tar:
        if hasattr(tarfile, 'data_filter'):
            tar.extractall(path=extract_dir, filter='data')
        else:
            tar.extractall(path=extract_dir)

    file_list = [str(p.relative_to(extract_dir)) for p in extract_dir.rglob("*")]
    logging.info("Danh sách tệp trong Model Artifact:")
    for f in file_list:
        logging.info(f"  └── {f}")

    has_pb = any("saved_model.pb" in f for f in file_list)
    has_code = any("code/inference.py" in f for f in file_list)

    if has_pb:
        logging.info("✔ Phát hiện saved_model.pb trong gói mô hình.")
    else:
        logging.error("❌ XUẤT HIỆN LỖI: Thiếu saved_model.pb!")

    if has_code:
        logging.info("✔ Phát hiện code/inference.py chuẩn Handler.")
    else:
        logging.warning("⚠️ CẢNH BÁO: Thiếu code/inference.py trong gói mô hình.")

    logging.info("=== BƯỚC 3: Quét Tìm CloudWatch Log Groups Liên Quan ===")
    try:
        res = logs_client.describe_log_groups(logGroupNamePrefix="/aws/sagemaker/Endpoints/")
        groups = [g["logGroupName"] for g in res.get("logGroups", [])]
        if groups:
            logging.info("Tìm thấy các Log Groups sau:")
            for g in groups:
                logging.info(f"  └── {g}")
        else:
            logging.warning("Chưa có Log Group nào được khởi tạo dưới đường dẫn /aws/sagemaker/Endpoints/")
    except ClientError as e:
        logging.error(f"Lỗi khi truy vấn CloudWatch Logs: {e}")

    logging.info("=== CHẨN ĐOÁN HOÀN TẤT ===")

if __name__ == "__main__":
    run_diagnostics()
