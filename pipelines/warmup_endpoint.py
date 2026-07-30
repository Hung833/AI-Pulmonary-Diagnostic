# -*- coding: utf-8 -*-
import json, logging, os, time, boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
ENDPOINT_NAME = os.environ.get("PULMONARY_ENDPOINT_NAME", "pulmonary-densenet121-serverless-endpoint")

def warmup_serverless_endpoint():
    sm_runtime = boto3.client("sagemaker-runtime")
    dummy_payload = json.dumps({"image_bytes": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="})
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        logging.info(f"Đang gửi request mồi (Warm-up lần {attempt}/{max_retries}) tới Endpoint '{ENDPOINT_NAME}'...")
        start_time = time.time()
        try:
            response = sm_runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME, ContentType="application/json", Accept="application/json", Body=dummy_payload)
            elapsed = time.time() - start_time
            result = response["Body"].read().decode("utf-8")
            logging.info(f"=== WARM-UP THÀNH CÔNG! (Thời gian: {elapsed:.2f}s) ===")
            logging.info(f"Kết quả phản hồi từ Model: {result}")
            return
        except ClientError as err:
            logging.warning(f"Lần thử {attempt} chưa thành công: {err}")
            if attempt < max_retries:
                logging.info("Đang chờ 5 giây để container khởi động xong rồi thử lại...")
                time.sleep(5)
            else:
                logging.critical("Đã vượt quá số lần thử warm-up tối đa.")

if __name__ == "__main__":
    warmup_serverless_endpoint()
