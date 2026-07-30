# -*- coding: utf-8 -*-
import io
import json
import logging
import os
import sys
import time
import zipfile
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_lambda_zip() -> bytes:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    lambda_script_path = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src", "lambda_function.py"))
    
    if not os.path.exists(lambda_script_path):
        logging.critical(f"Không tìm thấy file: {lambda_script_path}")
        sys.exit(1)
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(lambda_script_path, arcname="lambda_function.py")
    zip_buffer.seek(0)
    return zip_buffer.read()

def run_setup():
    try:
        boto_session = boto3.Session()
        sts_client = boto_session.client("sts")
        iam_client = boto_session.client("iam")
        lambda_client = boto_session.client("lambda")
        apigw_client = boto_session.client("apigateway")

        account_id = sts_client.get_caller_identity()["Account"]
        region = boto_session.region_name or "us-east-1"
        logging.info(f"Xác thực AWS thành công! Account ID: {account_id} | Region: {region}")
    except Exception as e:
        logging.critical(f"Lỗi xác thực AWS Context: {e}")
        sys.exit(1)

    function_name = "pulmonary-suite-predict-function"
    api_name = "Pulmonary-Diagnostic-API"
    role_name = "Lambda-SageMaker-Invoke-Role"
    endpoint_name = "pulmonary-densenet121-serverless-endpoint"

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }

    least_privilege_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "sagemaker:InvokeEndpoint",
                "Resource": f"arn:aws:sagemaker:{region}:{account_id}:endpoint/{endpoint_name}"
            }
        ]
    }

    try:
        logging.info(f"Đang kiểm tra/tạo IAM Role '{role_name}' cho Lambda...")
        role_res = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description="IAM Role for Lambda to invoke SageMaker Endpoint"
        )
        role_arn = role_res["Role"]["Arn"]
        
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="SageMakerInvokeLeastPrivilege",
            PolicyDocument=json.dumps(least_privilege_policy)
        )
        logging.info("Đã gán thành công Least Privilege Policy cho Lambda Role.")
        time.sleep(10)
    except ClientError as err:
        if err.response["Error"]["Code"] == "EntityAlreadyExists":
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            logging.info(f"IAM Role '{role_name}' đã tồn tại sẵn.")
        else:
            logging.critical(f"Lỗi tạo IAM Role: {err}")
            sys.exit(1)

    zip_bytes = create_lambda_zip()
    try:
        logging.info(f"Đang triển khai Lambda Function '{function_name}'...")
        try:
            lambda_res = lambda_client.create_function(
                FunctionName=function_name,
                Runtime="python3.10",
                Role=role_arn,
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Timeout=30,
                MemorySize=256,
                Environment={"Variables": {"ENDPOINT_NAME": endpoint_name}}
            )
            lambda_arn = lambda_res["FunctionArn"]
            logging.info(f"Đã tạo thành công Lambda Function: {lambda_arn}")
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceConflictException":
                logging.info("Lambda Function đã tồn tại. Tiến hành cập nhật code...")
                lambda_client.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
                lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{function_name}"
            else:
                raise err
    except Exception as e:
        logging.critical(f"Lỗi khởi tạo Lambda Function: {e}")
        sys.exit(1)

    try:
        logging.info(f"Đang kiểm tra/tạo REST API Gateway '{api_name}'...")
        apis = apigw_client.get_rest_apis().get("items", [])
        existing_api = next((item for item in apis if item["name"] == api_name), None)

        if existing_api:
            api_id = existing_api["id"]
            logging.info(f"REST API '{api_name}' đã tồn tại sẵn với ID: {api_id}")
        else:
            api_res = apigw_client.create_rest_api(
                name=api_name,
                description="REST API Gateway for AI Pulmonary Diagnostic Suite",
                endpointConfiguration={"types": ["REGIONAL"]}
            )
            api_id = api_res["id"]
            logging.info(f"Khởi tạo REST API thành công! API ID: {api_id}")

        resources = apigw_client.get_resources(restApiId=api_id)["items"]
        root_id = next(r["id"] for r in resources if r["path"] == "/")

        predict_resource = next((r for r in resources if r.get("path") == "/predict"), None)
        if not predict_resource:
            predict_resource = apigw_client.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart="predict"
            )
        resource_id = predict_resource["id"]

        try:
            apigw_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod="POST",
                authorizationType="NONE"
            )
        except ClientError:
            pass

        uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="POST",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=uri
        )

        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId="apigateway-invoke-permission",
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/*"
            )
        except ClientError:
            pass

        apigw_client.create_deployment(restApiId=api_id, stageName="prod")
        
        endpoint_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod/predict"
        logging.info("=== HOÀN TẤT TẠO SERVERLESS REST API GATEWAY! ===")
        logging.info(f"API GATEWAY ENDPOINT URL: {endpoint_url}")

    except Exception as e:
        logging.critical(f"Lỗi cấu hình API Gateway: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_setup()
