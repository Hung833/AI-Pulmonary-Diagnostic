# -*- coding: utf-8 -*-
import os, boto3, logging, sagemaker
from sagemaker.tensorflow import TensorFlow
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.parameters import ParameterString, ParameterInteger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ.get("PULMONARY_S3_BUCKET", "fcaj-pulmonary-suite-data-hung2026")
MODEL_GROUP_NAME = "Pulmonary-Diagnostic-Models"

def main():
    sagemaker_session = sagemaker.Session()
    role_arn = f"arn:aws:iam::{boto3.Session().client('sts').get_caller_identity()['Account']}:role/SageMaker-PulmonarySuite-ExecutionRole"

    logger.info("Đang khởi tạo cấu trúc Pipeline...")
    training_instance_type = ParameterString(name="TrainingInstanceType", default_value="ml.m5.xlarge")
    epochs = ParameterInteger(name="Epochs", default_value=1)

    tf_estimator = TensorFlow(
        entry_point="train.py", source_dir="src", role=role_arn, instance_count=1,
        instance_type=training_instance_type, framework_version="2.13.0", py_version="py310",
        hyperparameters={"epochs": epochs}, disable_profiler=True
    )

    step_train = TrainingStep(name="Pulmonary-Train-Model", estimator=tf_estimator, inputs={"train": f"s3://{BUCKET_NAME}/toy_data/"})
    step_register = RegisterModel(
        name="Pulmonary-Register-Model", estimator=tf_estimator,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["application/json"], response_types=["application/json"],
        inference_instances=["ml.m5.large", "ml.m5.xlarge"], transform_instances=["ml.m5.xlarge"],
        model_package_group_name=MODEL_GROUP_NAME, approval_status="Approved"
    )

    pipeline = Pipeline(name="Pulmonary-MLOps-Pipeline", parameters=[training_instance_type, epochs], steps=[step_train, step_register], sagemaker_session=sagemaker_session)
    pipeline.upsert(role_arn=role_arn)
    
    logger.info("=== KÍCH HOẠT CHẠY MLOPS PIPELINE TỰ ĐỘNG! ===")
    logger.info(f"Execution ARN: {pipeline.start().arn}")

if __name__ == "__main__":
    main()
