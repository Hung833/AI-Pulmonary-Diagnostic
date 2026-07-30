# -*- coding: utf-8 -*-
import argparse
import logging
import os
import sys
import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="SageMaker DenseNet121 HPO Training Job")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN"))
    parser.add_argument("--val", type=str, default=os.environ.get("SM_CHANNEL_VAL"))
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/tmp/model"))
    return parser.parse_args()

def build_model():
    base_model = DenseNet121(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    base_model.trainable = False
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.5)(x)
    predictions = Dense(1, activation="sigmoid")(x)
    return Model(inputs=base_model.input, outputs=predictions)

def main():
    args = parse_args()
    logger.info("=== BẮT ĐẦU HUẤN LUYỆN DENSENET121 HPO TRIAL ===")
    logger.info(f"Hyperparameters -> Epochs: {args.epochs} | Batch Size: {args.batch_size} | Learning Rate: {args.learning_rate}")

    if not args.train or not os.path.exists(args.train):
        logger.error(f"Kênh dữ liệu Train không tồn tại: {args.train}")
        sys.exit(1)

    try:
        train_datagen = ImageDataGenerator(rescale=1.0 / 255.0, horizontal_flip=True)
        val_datagen = ImageDataGenerator(rescale=1.0 / 255.0)

        train_generator = train_datagen.flow_from_directory(
            args.train, target_size=(224, 224), batch_size=args.batch_size, class_mode="binary"
        )
        val_generator = val_datagen.flow_from_directory(
            args.val, target_size=(224, 224), batch_size=args.batch_size, class_mode="binary"
        )

        model = build_model()
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate),
            loss="binary_crossentropy",
            metrics=["accuracy", tf.keras.metrics.Recall(name="recall")],
        )

        model.fit(train_generator, epochs=args.epochs, validation_data=val_generator)

        save_version_dir = os.path.join(args.model_dir, "1")
        os.makedirs(save_version_dir, exist_ok=True)

        if hasattr(model, "export"):
            model.export(save_version_dir)
        else:
            keras_file_path = os.path.join(save_version_dir, "model.keras")
            model.save(keras_file_path)

        logger.info(f"=== ĐÃ LƯU MÔ HÌNH TRIAL THÀNH CÔNG VÀO {save_version_dir} ===")

    except Exception as e:
        logger.error(f"Lỗi huấn luyện mô hình HPO Trial: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
