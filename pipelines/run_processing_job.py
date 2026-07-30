# -*- coding: utf-8 -*-
import os
import logging
from pathlib import Path
import sys
import boto3
from botocore.exceptions import ClientError

os.environ["SAGEMAKER_SUPPRESS_V2_WARNING"] = "1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    import sagemaker
    from sagemaker.processing import ProcessingInput, ProcessingOutput
    from sagemaker.sklearn.processing import SKLearnProcessor
except ImportError:
    logging.critical("Thư viện 'sagemaker' chưa được cài đặt!")
    sys.exit(1)

session = boto3.Session()
sts_client = session.client("sts")
account_id = sts_client.get_caller_identity()["Account"]
region = session.region_name or "us-east-1"

bucket_name = "fcaj-pulmonary-suite-data-hung2026"
role_arn = f"arn:aws:iam::{account_id}:role/SageMaker-PulmonarySuite-ExecutionRole"

sagemaker_session = sagemaker.Session(
    boto_session=session,
    default_bucket=bucket_name
)

CURRENT_DIR = Path(__file__).parent.resolve()
PREPROCESSING_SCRIPT = (CURRENT_DIR / ".." / "src" / "data" / "preprocessing.py").resolve()

PROCESSING_INSTANCE_TYPE = os.getenv("SAGEMAKER_INSTANCE_TYPE", "ml.t3.medium")

try:
    sklearn_processor = SKLearnProcessor(
        framework_version="1.2-1",
        role=role_arn,
        instance_type=PROCESSING_INSTANCE_TYPE,
        instance_count=1,
        volume_size_in_gb=10,
        sagemaker_session=sagemaker_session
    )

    logging.info(f"=== KÍCH HOẠT SAGEMAKER SKLEARN PROCESSING JOB ({PROCESSING_INSTANCE_TYPE}) ===")

    sklearn_processor.run(
        code=str(PREPROCESSING_SCRIPT),
        inputs=[
            ProcessingInput(
                source=f"s3://{bucket_name}/raw-data/",
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                source="/opt/ml/processing/output",
                destination=f"s3://{bucket_name}/processed-data/"
            )
        ],
        arguments=[
            "--image-size", "224",
            "--train-ratio", "0.7",
            "--val-ratio", "0.15",
            "--seed", "2026"
        ]
    )

    logging.info("=== HOÀN TẤT KÍCH HOẠT JOB TRÊN CLOUD ===")

except ClientError as err:
    logging.critical(f"Lỗi API SageMaker: {err}")
    sys.exit(1)
