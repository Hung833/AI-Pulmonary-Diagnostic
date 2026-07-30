# -*- coding: utf-8 -*-
import logging, os, sys, boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
API_NAME = os.environ.get("API_NAME", "Pulmonary-Diagnostic-API")
ALARM_EMAIL = os.environ.get("ALARM_EMAIL")

def get_api_id(api_name):
    try:
        for api in boto3.client("apigateway", region_name=AWS_REGION).get_rest_apis().get("items", []):
            if api.get("name") == api_name: return api.get("id")
        logger.error(f"Không tìm thấy API: {api_name}")
    except ClientError as e: logger.error(f"Lỗi truy vấn API Gateway: {e}")
    return None

def setup_sns_topic(topic_name, email):
    sns = boto3.client("sns", region_name=AWS_REGION)
    try:
        topic_arn = sns.create_topic(Name=topic_name)["TopicArn"]
        logger.info(f"Đã tạo/Lấy SNS Topic ARN: {topic_arn}")
        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
        if not any(sub["Endpoint"] == email for sub in subs):
            logger.info(f"Đang gửi yêu cầu đăng ký tới email: {email}...")
            sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
            logger.warning(f"VUI LÒNG KIỂM TRA HỘP THƯ {email} VÀ CLICK 'CONFIRM SUBSCRIPTION' ĐỂ NHẬN CẢNH BÁO!")
        else:
            logger.info(f"Email {email} đã được đăng ký.")
        return topic_arn
    except ClientError as e:
        logger.critical(f"Lỗi thiết lập SNS: {e}")
        sys.exit(1)

def setup_api_5xx_alarm(api_id, stage_name, topic_arn):
    cw = boto3.client("cloudwatch", region_name=AWS_REGION)
    alarm_name = f"APIGateway-5XX-Errors-{api_id}"
    try:
        logger.info(f"Đang thiết lập CloudWatch Alarm: {alarm_name}...")
        cw.put_metric_alarm(
            AlarmName=alarm_name, AlarmDescription="Cảnh báo lỗi 5XX API Gateway.",
            ActionsEnabled=True, AlarmActions=[topic_arn], MetricName="5XXError",
            Namespace="AWS/ApiGateway", Statistic="Sum",
            Dimensions=[{"Name": "ApiName", "Value": API_NAME}, {"Name": "Stage", "Value": stage_name}],
            Period=60, EvaluationPeriods=1, Threshold=1.0, ComparisonOperator="GreaterThanOrEqualToThreshold",
            TreatMissingData="notBreaching"
        )
        logger.info("=== THIẾT LẬP CLOUDWATCH ALARM THÀNH CÔNG! ===")
    except ClientError as e:
        logger.critical(f"Lỗi tạo Alarm: {e}")
        sys.exit(1)

def main():
    if not ALARM_EMAIL:
        logger.critical("Vui lòng cung cấp email: export ALARM_EMAIL='email_cua_ban@example.com'")
        sys.exit(1)
    api_id = get_api_id(API_NAME)
    if api_id: setup_api_5xx_alarm(api_id, "prod", setup_sns_topic("Pulmonary-Diagnostic-Alerts", ALARM_EMAIL))

if __name__ == "__main__":
    main()
