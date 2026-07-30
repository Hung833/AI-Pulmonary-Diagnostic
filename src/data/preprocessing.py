# -*- coding: utf-8 -*-
"""
Dự án: AI Pulmonary Diagnostic Suite (FCAJ 2026)
Tác giả: Nguyễn Thái Hưng 
Bản quyền © 2026 thuộc về tác giả. Bảo lưu mọi quyền.
Mô tả: Script tiền xử lý dữ liệu ảnh X-Quang phổi đa luồng & phân chia Train/Val/Test cho SageMaker Processing Job.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import random
from PIL import Image, ImageOps

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def process_single_image(args_tuple: tuple) -> bool:
    """Đọc ảnh, chuẩn hóa RGB, resize và lưu an toàn."""
    file_path, output_dir, size = args_tuple
    try:
        file_path = Path(file_path)
        with Image.open(file_path) as img:
            # Tự động xoay ảnh đúng chiều dựa trên EXIF metadata
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            output_dir.mkdir(parents=True, exist_ok=True)
            save_path = output_dir / file_path.name
            img.save(save_path, format="JPEG", quality=90)
            return True
    except Exception as e:
        logging.error(f"Lỗi khi xử lý ảnh {file_path}: {e}")
        return False


def main():
    args = parse_args()
    logging.info(f"=== BẮT ĐẦU TÁC VỤ TIỀN XỬ LÝ ẢNH (Size: {args.image_size}x{args.image_size}) ===")

    input_base = Path("/opt/ml/processing/input")
    output_base = Path("/opt/ml/processing/output")

    valid_extensions = {".jpeg", ".jpg", ".png"}
    categories = ["NORMAL", "PNEUMONIA"]

    random.seed(args.seed)

    for category in categories:
        # Tìm kiếm tất cả các file ảnh thuộc nhãn tương ứng
        cat_files = [
            p for p in input_base.rglob("*") 
            if p.is_file() and p.suffix.lower() in valid_extensions and category.lower() in p.as_posix().lower()
        ]

        if not cat_files:
            logging.warning(f"Không tìm thấy ảnh nào cho nhãn: {category}")
            continue

        # Xáo trộn dữ liệu có kiểm soát (Reproducible)
        random.shuffle(cat_files)

        # Tính toán chỉ số chia tập Train / Val / Test
        total = len(cat_files)
        train_end = int(total * args.train_ratio)
        val_end = train_end + int(total * args.val_ratio)

        splits = {
            "train": cat_files[:train_end],
            "validation": cat_files[train_end:val_end],
            "test": cat_files[val_end:]
        }

        # Chuẩn bị danh sách công việc cho Multithreading
        tasks = []
        for split_name, files in splits.items():
            split_dir = output_base / split_name / category
            for f in files:
                tasks.append((f, split_dir, args.image_size))

        # Tối ưu hiệu năng: Đa luồng xử lý I/O ảnh
        logging.info(f"Đang xử lý song song {len(tasks)} ảnh cho nhãn [{category}]...")
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_single_image, tasks))

        success_count = sum(results)
        logging.info(f"Đã xử lý xong nhãn [{category}]: {success_count}/{len(tasks)} ảnh thành công.")

    logging.info("=== HOÀN TẤT XỬ LÝ VÀ CHIA TẬP DỮ LIỆU LÊN S3 ===")


if __name__ == "__main__":
    main()