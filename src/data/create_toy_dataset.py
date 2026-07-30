# -*- coding: utf-8 -*-
"""
Project: AI Pulmonary Diagnostic Suite (FCAJ Final Project)
Author: Nguyen Thai Hung 
Copyright © 2026. All rights reserved.
Description: Secure, concurrent, and reproducible extraction of Toy Dataset for MLOps pipeline.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import random
import shutil

# Cấu hình logging thay cho hàm print thông thường
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_toy_set(src_dir: str | Path, dest_dir: str | Path, sample_size: int = 60, seed: int = 42) -> None:
    """Trích xuất ngẫu nhiên, an toàn và song song các file ảnh từ src_dir sang dest_dir."""
    src_path = Path(src_dir).resolve()
    dest_path = Path(dest_dir).resolve()

    # 1. Bảo mật: Chống Path Traversal và validate đầu vào
    if not src_path.exists() or not src_path.is_dir():
        raise FileNotFoundError(f"Thư mục nguồn không tồn tại hoặc không hợp lệ: {src_path}")

    dest_path.mkdir(parents=True, exist_ok=True)

    # 2. Hiệu năng & MLOps: Dùng Generator (rglob) để tiết kiệm RAM + Cố định Seed
    valid_extensions = {".jpeg", ".jpg", ".png"}
    all_images = [f for f in src_path.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]

    if not all_images:
        logging.warning(f"Không tìm thấy file ảnh hợp lệ nào tại: {src_path}")
        return

    random.seed(seed)  # Đảm bảo tính tái lập (Reproducibility) trong MLOps
    selected_images = random.sample(all_images, min(sample_size, len(all_images)))

    # 3. Tối ưu hiệu năng: Sao chép đa luồng (Multi-threading) tối ưu I/O bound
    def _copy_file(img_path: Path) -> None:
        try:
            shutil.copy2(img_path, dest_path / img_path.name)  # copy2 giữ nguyên metadata của file y tế
        except IOError as e:
            logging.error(f"Lỗi khi sao chép file {img_path.name}: {e}")

    logging.info(f"Đang tiến hành sao chép song song {len(selected_images)} ảnh vào {dest_path}...")
    with ThreadPoolExecutor() as executor:
        executor.map(_copy_file, selected_images)

    logging.info(f"Đã hoàn thành phân đoạn dữ liệu cho: {dest_path.name}")


if __name__ == "__main__":
    # 1. Định vị vùng an toàn của thư mục gốc dữ liệu
    BASE_PROJECT_DIR = Path(__file__).parent.resolve()
    DATASET_SEARCH_DIR = BASE_PROJECT_DIR / "dataset"
    TOY_BASE_DIR = BASE_PROJECT_DIR / "toy_dataset"

    SAMPLE_COUNT = 60
    RANDOM_SEED = 2026

    logging.info(f"Đang tự động rà soát cấu trúc thư mục tại: {DATASET_SEARCH_DIR}")

    # 2. Cơ chế Auto-Detect tầng dữ liệu: Tìm kiếm thông minh các thư mục chứa ảnh gốc
    # Giải quyết triệt để vấn đề lệch tầng do giải nén file zip từ Kaggle
    target_categories = ["NORMAL", "PNEUMONIA"]
    resolved_paths = {}

    try:
        if not DATASET_SEARCH_DIR.exists():
            raise FileNotFoundError(f"Không tìm thấy thư mục 'dataset' tại root: {BASE_PROJECT_DIR}")

        # Duyệt cây thư mục để tìm đường dẫn thực tế chứa nhãn dữ liệu y tế
        for category in target_categories:
            # Tìm kiếm thư mục con có tên trùng khớp và nằm trong nhánh 'train' (ưu tiên dữ liệu train gốc)
            found_paths = [
                p for p in DATASET_SEARCH_DIR.rglob(category) 
                if p.is_dir() and "train" in p.as_posix().lower()
            ]
            
            # Nếu không tìm thấy trong 'train', lấy bất kỳ thư mục nhãn nào hợp lệ đầu tiên tìm được
            if not found_paths:
                found_paths = [p for p in DATASET_SEARCH_DIR.rglob(category) if p.is_dir()]

            if not found_paths:
                raise FileNotFoundError(f"Hệ thống không thể định vị được thư mục nhãn dữ liệu y tế: {category}")
            
            # Lấy đường dẫn chuẩn hóa đầu tiên tìm được
            resolved_paths[category] = found_paths[0]
            logging.info(f"Đã ánh xạ thành công nhãn [{category}] -> {resolved_paths[category]}")

        # 3. Kích hoạt Pipeline trích xuất song song an toàn
        for category, src_path in resolved_paths.items():
            create_toy_set(
                src_dir=src_path,
                dest_dir=TOY_BASE_DIR / category,
                sample_size=SAMPLE_COUNT,
                seed=RANDOM_SEED
            )
        logging.info("=== HOÀN TẤT TRÍCH XUẤT TOY DATASET CHUẨN MLOPS ===")

    except Exception as error:
        logging.critical(f"Pipeline trích xuất thất bại: {error}")