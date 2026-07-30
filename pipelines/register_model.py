# -*- coding: utf-8 -*-
import argparse
import logging
import os
import sys
import boto3
from botocore.exceptions import ClientError

os.environ["SAGEMAKER_SUPPRESS_V2_WARNING"] = "1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_register_pipeline(auto_approve=False, tf_version="2.13.0"):
    try:
        boto_session = boto3.Session()
        sts_client = boto_session.client("sts")
        sm_client = boto_session.client("sagemaker")
        
        account_id = sts_client.get_caller_identity()["Account"]
        region = boto_session.region_name or "us-east-1"
        logging.info(f"Xác thực AWS thành công! Account ID: {account_id} | Region: {region}")
    except Exception as e:
        logging.critical(f"Lỗi xác thực AWS Context: {e}")
        sys.exit(1)

    bucket_name = os.getenv("PULMONARY_S3_BUCKET", "fcaj-pulmonary-suite-data-hung2026")
    model_group_name = os.getenv("PULMONARY_MODEL_GROUP", "Pulmonary-Diagnostic-Models")
    model_s3_uri = f"s3://{bucket_name}/output/hpo-best-model.tar.gz"

    container_image_uri = f"763104351884.dkr.ecr.{region}.amazonaws.com/tensorflow-inference:{tf_version}-cpu"

    approval_status = "Approved" if auto_approve else "PendingManualApproval"

    model_package_input = {
        "ModelPackageGroupName": model_group_name,
        "ModelPackageDescription": f"DenseNet121 - TensorFlow {tf_version} DLC",
        "ModelApprovalStatus": approval_status,
        "InferenceSpecification": {
            "Containers": [
                {
                    "Image": container_image_uri,
                    "ModelDataUrl": model_s3_uri,
                }
            ],
            "SupportedContentTypes": ["application/json", "image/jpeg", "image/png"],
            "SupportedResponseMIMETypes": ["application/json"],
            "SupportedRealtimeInferenceInstanceTypes": ["ml.t2.medium", "ml.m5.large"],
        }
    }

    try:
        logging.info(f"Đang đăng ký Model Package (Trạng thái: {approval_status})...")
        create_res = sm_client.create_model_package(**model_package_input)
        model_package_arn = create_res["ModelPackageArn"]
        logging.info(f"=== ĐĂNG KÝ THÀNH CÔNG: {model_package_arn} ===")
    except ClientError as err:
        logging.critical(f"Lỗi đăng ký mô hình: {err}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto-approve", action="store_true", help="Tự động Approve mô hình")
    parser.add_argument("--tf-version", default="2.13.0", help="Phiên bản TensorFlow Container DLC")
    args = parser.parse_args()
    
    run_register_pipeline(auto_approve=args.auto_approve, tf_version=args.tf_version)
