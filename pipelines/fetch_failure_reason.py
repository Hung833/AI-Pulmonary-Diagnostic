# -*- coding: utf-8 -*-
import logging
import sys
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_diagnostics():
    endpoint_name = "pulmonary-densenet121-diagnostic-rt-endpoint"
    sm_client = boto3.client("sagemaker")
    logs_client = boto3.client("logs")

    logger.info(f"=== BƯỚC 1: Truy vấn FailureReason của Endpoint '{endpoint_name}' ===")
    try:
        res = sm_client.describe_endpoint(EndpointName=endpoint_name)
        status = res.get("EndpointStatus", "Unknown")
        failure_reason = res.get("FailureReason", "Không có thông tin FailureReason.")
        
        logger.info(f"Trạng thái Endpoint: {status}")
        logger.critical(f"LÝ DO THẤT BẠI TỪ AWS SAGEMAKER:\n{failure_reason}\n")
    except ClientError as e:
        logger.error(f"Lỗi khi gọi describe_endpoint: {e}")
        sys.exit(1)

    log_group_name = f"/aws/sagemaker/Endpoints/{endpoint_name}"
    logger.info(f"=== BƯỚC 2: Truy vấn CloudWatch Log Group '{log_group_name}' ===")
    
    try:
        streams_res = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy="LastEventTime",
            descending=True,
            limit=1
        )
        streams = streams_res.get("logStreams", [])
        if not streams:
            logger.warning("Không tìm thấy Log Stream nào trong Log Group này.")
            return

        stream_name = streams[0]["logStreamName"]
        logger.info(f"Đã tìm thấy Log Stream: {stream_name}")

        events_res = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=stream_name,
            startFromHead=True
        )
        events = events_res.get("events", [])
        
        logger.info("=== NỘI DUNG LOG CHI TIẾT TỪ CONTAINER ===")
        for ev in events:
            print(ev.get("message", "").strip())

    except ClientError as e:
        logger.error(f"Lỗi khi đọc CloudWatch Logs: {e}")

if __name__ == "__main__":
    fetch_diagnostics()
