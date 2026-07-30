# -*- coding: utf-8 -*-
import logging, os, sys, boto3
from botocore.exceptions import ClientError

os.environ["SAGEMAKER_SUPPRESS_V2_WARNING"] = "1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_GROUP_NAME = "Pulmonary-Diagnostic-Models"
EXECUTION_ROLE_NAME = "SageMaker-PulmonarySuite-ExecutionRole"
MODEL_NAME = "pulmonary-densenet121-serverless-v2-model"
ENDPOINT_CONFIG_NAME = "pulmonary-densenet121-serverless-v2-config"
ENDPOINT_NAME = "pulmonary-densenet121-serverless-v2-endpoint"
MEMORY_MB = 3072
MAX_CONCURRENCY = 5

def delete_if_exists(fn, **kwargs):
    try:
        fn(**kwargs)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code not in ("ValidationException", "ResourceNotFound"):
            logger.warning(f"Lỗi khi xóa: {e}")

def main():
    boto_session = boto3.Session()
    sts_client = boto_session.client("sts")
    sm_client = boto_session.client("sagemaker")
    account_id = sts_client.get_caller_identity()["Account"]
    role_arn = f"arn:aws:iam::{account_id}:role/{EXECUTION_ROLE_NAME}"

    logger.info("Đang dọn dẹp tàn dư V2 cũ (nếu có) trước khi tạo lại...")
    delete_if_exists(sm_client.delete_endpoint, EndpointName=ENDPOINT_NAME)
    delete_if_exists(sm_client.delete_endpoint_config, EndpointConfigName=ENDPOINT_CONFIG_NAME)
    delete_if_exists(sm_client.delete_model, ModelName=MODEL_NAME)

    packages = sm_client.list_model_packages(
        ModelPackageGroupName=MODEL_GROUP_NAME,
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
    )
    model_package_arn = packages.get("ModelPackageSummaryList", [])[0]["ModelPackageArn"]

    logger.info(f"Đang tạo SageMaker Model V2 '{MODEL_NAME}'...")
    sm_client.create_model(ModelName=MODEL_NAME, ExecutionRoleArn=role_arn, Containers=[{"ModelPackageName": model_package_arn}])

    logger.info(f"Đang tạo Serverless Config V2 '{ENDPOINT_CONFIG_NAME}'...")
    sm_client.create_endpoint_config(
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        ProductionVariants=[{"VariantName": "AllTraffic", "ModelName": MODEL_NAME, "ServerlessConfig": {"MemorySizeInMB": MEMORY_MB, "MaxConcurrency": MAX_CONCURRENCY}}]
    )

    logger.info(f"Đang kích hoạt Deploy Endpoint V2 '{ENDPOINT_NAME}'...")
    sm_client.create_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
    logger.info("=== KÍCH HOẠT SERVERLESS ENDPOINT V2 THÀNH CÔNG! ===")

if __name__ == "__main__":
    main()
