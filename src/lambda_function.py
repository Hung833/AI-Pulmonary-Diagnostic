# -*- coding: utf-8 -*-
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sagemaker_runtime = boto3.client("sagemaker-runtime")
ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", "pulmonary-densenet121-serverless-endpoint")

def lambda_handler(event, context):
    logger.info("Tiếp nhận Request từ API Gateway...")

    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"message": "CORS preflight OK"})}

    try:
        body = event.get("body", "")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body

        if "image_bytes" not in payload:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Payload thiếu trường bắt buộc 'image_bytes'"})
            }

        logger.info(f"Đang chuyển tiếp Payload sang SageMaker Endpoint: {ENDPOINT_NAME}")
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Accept="application/json",
            Body=json.dumps({"image_bytes": payload["image_bytes"]})
        )

        result_str = response["Body"].read().decode("utf-8")
        result_json = json.loads(result_str)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(result_json)
        }

    except ClientError as e:
        logger.error(f"Lỗi khi gọi SageMaker Endpoint: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Lỗi nội bộ server suy luận: {str(e)}"})
        }
    except Exception as e:
        logger.error(f"Lỗi không xác định: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Lỗi xử lý payload: {str(e)}"})
        }
