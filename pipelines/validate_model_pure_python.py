# -*- coding: utf-8 -*-
import sys
from pathlib import Path

def validate_saved_model_structure(target_dir: str) -> bool:
    print(f"=== Kiểm tra Cấu trúc SavedModel tại: {target_dir} ===\n")
    path = Path(target_dir)
    
    pb_file = path / "saved_model.pb"
    variables_dir = path / "variables"
    var_data = variables_dir / "variables.data-00000-of-00001"
    var_index = variables_dir / "variables.index"

    checks = [
        ("File saved_model.pb", pb_file.exists()),
        ("Thư mục variables/", variables_dir.is_dir()),
        ("File weights variables.data", var_data.exists()),
        ("File index variables.index", var_index.exists()),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✔ PASS" if passed else "❌ FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✔ Cấu trúc SavedModel hoàn toàn đầy đủ và đạt chuẩn TFS Engine!")
    else:
        print("\n❌ Cấu trúc SavedModel bị thiếu tệp nghiêm trọng!")

    return all_passed

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/tmp/repack/1"
    ok = validate_saved_model_structure(target)
    sys.exit(0 if ok else 1)
