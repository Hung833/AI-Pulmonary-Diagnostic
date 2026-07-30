# -*- coding: utf-8 -*-
import logging, boto3
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_all_crash_logs():
    logs_client = boto3.client("logs")
    log_group_name = "/aws/sagemaker/Endpoints/pulmonary-densenet121-serverless-v2-endpoint"
    logger.info(f"Đang càn quét mọi Log Stream trong: {log_group_name}")
    try:
        streams = logs_client.describe_log_streams(logGroupName=log_group_name, orderBy="LastEventTime", descending=True, limit=5).get("logStreams", [])
        if not streams:
            logger.warning(f"Log Group tồn tại nhưng trống rỗng.")
            return
        logger.info(f"TÌM THẤY {len(streams)} LOG STREAMS. Đang tổng hợp dữ liệu...")
        for idx, stream in enumerate(streams):
            stream_name = stream["logStreamName"]
            logger.info(f"\n--- ĐỌC STREAM [{idx + 1}]: {stream_name} ---")
            events = logs_client.get_log_events(logGroupName=log_group_name, logStreamName=stream_name, startFromHead=True).get("events", [])
            for ev in events: print(ev.get("message", "").strip())
        logger.info("\n--- KẾT THÚC CÀN QUÉT LOG ---")
    except Exception as e:
        logger.error(f"Lỗi truy xuất CloudWatch: {e}")

if __name__ == "__main__":
    fetch_all_crash_logs()
