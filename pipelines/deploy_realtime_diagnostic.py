# -*- coding: utf-8 -*-
import logging
import os
import sys
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_GROUP_NAME = os.environ.get("PULMONARY_MODEL_GROUP", "Pulmonary-Diagnostic-Models")
EXECUTION_ROLE_NAME = os.environ.get("PULMONARY_EXECUTION_ROLE", "SageMaker-PulmonarySuite-ExecutionRole")
MODEL_NAME = "pulmonary-densenet121-diagnostic-rt-model"
ENDPOINT_CONFIG_NAME = "pulmonary-densenet121-diagnostic-rt-config"
ENDPOINT_NAME = "pulmonary-densenet121-diagnostic-rt-endpoint"
INSTANCE_TYPE = os.environ.get("PULMONARY_RT_INSTANCE_TYPE", "ml.m5.large")

def delete_if_exists(sm_client, delete_fn, **kwargs):
    try:
        delete_fn(**kwargs)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code not in ("ValidationException", "ResourceNotFound"):
            logger.error(f"Lỗi khi xóa tài nguyên: {e}")

def main():
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
        packages = sm_client.list_model_packages(
            ModelPackageGroupName=MODEL_GROUP_NAME,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            SortOrder="Descending",
        )
        package_list = packages.get("ModelPackageSummaryList", [])
        if not package_list:
            logger.critical("Không tìm thấy Model Package Approved nào.")
            sys.exit(1)
            
        model_package_arn = package_list[0]["ModelPackageArn"]
        logger.info(f"Đã chọn Model Package Approved mới nhất: {model_package_arn}")
    except ClientError as err:
        logger.critical(f"Lỗi khi truy vấn Model Registry: {err}")
        sys.exit(1)

    delete_if_exists(sm_client, sm_client.delete_model, ModelName=MODEL_NAME)
    
    try:
        sm_client.create_model(
            ModelName=MODEL_NAME,
            ExecutionRoleArn=role_arn,
            Containers=[{"ModelPackageName": model_package_arn}],
        )
    except ClientError as err:
        logger.critical(f"Lỗi khi tạo Real-Time Model: {err}")
        sys.exit(1)

    delete_if_exists(sm_client, sm_client.delete_endpoint_config, EndpointConfigName=ENDPOINT_CONFIG_NAME)
    
    try:
        sm_client.create_endpoint_config(
            EndpointConfigName=ENDPOINT_CONFIG_NAME,
            ProductionVariants=[{
                "VariantName": "AllTraffic",
                "ModelName": MODEL_NAME,
                "InstanceType": INSTANCE_TYPE,
                "InitialInstanceCount": 1,
            }],
        )
    except ClientError as err:
        logger.critical(f"Lỗi khi tạo Real-Time Endpoint Config: {err}")
        sys.exit(1)

    try:
        logger.info(f"Kích hoạt Deploy Real-Time Endpoint '{ENDPOINT_NAME}' ({INSTANCE_TYPE})...")
        try:
            sm_client.create_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
        except ClientError as err:
            if "already existing" in str(err):
                sm_client.update_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
            else:
                raise err

        logger.info("Đang chờ Real-Time Endpoint InService (Thời gian khởi tạo khoảng 5–8 phút)...")
        waiter = sm_client.get_waiter("endpoint_in_service")
        waiter.wait(EndpointName=ENDPOINT_NAME, WaiterConfig={"Delay": 15, "MaxAttempts": 60})
        logger.info("=== REAL-TIME ENDPOINT ĐÃ 'InService' THÀNH CÔNG! ===")
    except ClientError as err:
        logger.critical(f"Lỗi khi Deploy Real-Time Endpoint: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
