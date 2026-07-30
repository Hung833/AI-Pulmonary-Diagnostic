# -*- coding: utf-8 -*-
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def inspect_all_sagemaker_logs():
    logs_client = boto3.client("logs")
    logger.info("Đang quét toàn bộ CloudWatch Log Groups chứa từ khóa 'sagemaker'...")

    try:
        paginator = logs_client.get_paginator("describe_log_groups")
        found_groups = []
        
        for page in paginator.paginate():
            for group in page.get("logGroups", []):
                name = group.get("logGroupName", "")
                if "sagemaker" in name.lower() or "pulmonary" in name.lower():
                    found_groups.append(name)

        if found_groups:
            logger.info("=== DANH SÁCH CLOUDWATCH LOG GROUPS NGHĨA VỤ ===")
            for g in found_groups:
                logger.info(f"  └── {g}")
        else:
            logger.warning("KHÔNG TÌM THẤY bất kỳ Log Group nào của SageMaker trên CloudWatch.")
            logger.warning("Xác nhận: Container bị tiêu diệt trước khi Logging Daemon kịp khởi tạo.")

    except ClientError as e:
        logger.error(f"Lỗi khi truy vấn CloudWatch Logs: {e}")

if __name__ == "__main__":
    inspect_all_sagemaker_logs()
