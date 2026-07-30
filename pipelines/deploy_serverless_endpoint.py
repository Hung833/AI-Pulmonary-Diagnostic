# -*- coding: utf-8 -*-
import logging
import os
import sys
import boto3
from botocore.exceptions import ClientError

os.environ["SAGEMAKER_SUPPRESS_V2_WARNING"] = "1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_GROUP_NAME = os.environ.get("PULMONARY_MODEL_GROUP", "Pulmonary-Diagnostic-Models")
MODEL_NAME = os.environ.get("PULMONARY_MODEL_NAME", "pulmonary-densenet121-serverless-model")
ENDPOINT_CONFIG_NAME = os.environ.get("PULMONARY_ENDPOINT_CONFIG", "pulmonary-densenet121-serverless-config")
ENDPOINT_NAME = os.environ.get("PULMONARY_ENDPOINT_NAME", "pulmonary-densenet121-serverless-endpoint")
EXECUTION_ROLE_NAME = os.environ.get("PULMONARY_EXECUTION_ROLE", "SageMaker-PulmonarySuite-ExecutionRole")
MEMORY_MB = int(os.environ.get("PULMONARY_SERVERLESS_MEMORY_MB", "3072"))
MAX_CONCURRENCY = int(os.environ.get("PULMONARY_MAX_CONCURRENCY", "5"))

def delete_if_exists(delete_fn, not_found_codes=("ValidationException",), **kwargs):
    try:
        delete_fn(**kwargs)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_msg = e.response.get("Error", {}).get("Message", "")
        if error_code in not_found_codes or "does not exist" in error_msg.lower():
            logger.info(f"Resource chưa tồn tại (bỏ qua): {kwargs}")
        else:
            logger.critical(f"Lỗi khi xóa resource ({error_code}): {error_msg}")
            raise

def deploy_serverless():
    try:
        boto_session = boto3.Session()
        sts_client = boto_session.client("sts")
        sm_client = boto_session.client("sagemaker")
        account_id = sts_client.get_caller_identity()["Account"]
        region = boto_session.region_name or "us-east-1"
        logger.info(f"Xác thực AWS thành công! Account ID: {account_id} | Region: {region}")
    except Exception as e:
        logger.critical(f"Lỗi xác thực AWS Context: {e}")
        sys.exit(1)

    role_arn = f"arn:aws:iam::{account_id}:role/{EXECUTION_ROLE_NAME}"

    try:
        logger.info(f"Đang tìm Model Package đã Approved trong '{MODEL_GROUP_NAME}'...")
        packages = sm_client.list_model_packages(
            ModelPackageGroupName=MODEL_GROUP_NAME,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            SortOrder="Descending",
        )
        package_list = packages.get("ModelPackageSummaryList", [])
        if not package_list:
            logger.critical("Không tìm thấy Model Package nào có trạng thái 'Approved'!")
            sys.exit(1)
        model_package_arn = package_list[0]["ModelPackageArn"]
        logger.info(f"Đã chọn Model Package Approved: {model_package_arn}")
    except ClientError as err:
        logger.critical(f"Lỗi khi truy vấn Model Registry: {err}")
        sys.exit(1)

    delete_if_exists(sm_client.delete_model, ModelName=MODEL_NAME)

    try:
        logger.info(f"Đang tạo SageMaker Model '{MODEL_NAME}' (KHÔNG set SAGEMAKER_PROGRAM)...")
        sm_client.create_model(
            ModelName=MODEL_NAME,
            ExecutionRoleArn=role_arn,
            Containers=[{"ModelPackageName": model_package_arn}],
        )
    except ClientError as err:
        logger.critical(f"Lỗi tạo Model Object: {err}")
        sys.exit(1)

    delete_if_exists(sm_client.delete_endpoint_config, EndpointConfigName=ENDPOINT_CONFIG_NAME)

    try:
        logger.info(f"Đang tạo Serverless Endpoint Config '{ENDPOINT_CONFIG_NAME}' ({MEMORY_MB}MB)...")
        sm_client.create_endpoint_config(
            EndpointConfigName=ENDPOINT_CONFIG_NAME,
            ProductionVariants=[{
                "VariantName": "AllTraffic",
                "ModelName": MODEL_NAME,
                "ServerlessConfig": {"MemorySizeInMB": MEMORY_MB, "MaxConcurrency": MAX_CONCURRENCY},
            }],
        )
    except ClientError as err:
        logger.critical(f"Lỗi tạo Serverless Endpoint Config: {err}")
        sys.exit(1)

    try:
        logger.info(f"Đang triển khai Serverless Endpoint '{ENDPOINT_NAME}'...")
        try:
            sm_client.create_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
        except ClientError as err:
            if "Cannot create already existing endpoint" in str(err):
                sm_client.update_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
            else:
                raise
        logger.info(f"=== KÍCH HOẠT SERVERLESS ENDPOINT ({MEMORY_MB}MB RAM) THÀNH CÔNG! ===")
        logger.info(f"Endpoint Name: {ENDPOINT_NAME}")
    except ClientError as err:
        logger.critical(f"Lỗi khi Deploy Serverless Endpoint: {err}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_serverless()
