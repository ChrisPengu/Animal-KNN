"""Các lệnh thí nghiệm; tên lệnh giữ ổn định, hướng dẫn hiển thị tiếng Việt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import ROOT


def main():
    parser = argparse.ArgumentParser(description="Animal K-NN · Phân loại sáu nhóm động vật từ STL-10")
    parser.add_argument("--root", type=Path, default=ROOT, help="Thư mục dữ liệu/mô hình/kết quả; đặt trước tên lệnh")
    sub = parser.add_subparsers(dest="command", required=True, title="Các lệnh")
    prep = sub.add_parser("prepare", help="Tải, kiểm tra và chia dữ liệu cố định")
    prep.add_argument("--download", action="store_true", help="Tải dữ liệu nếu chưa có")
    prep.add_argument("--ranged", action="store_true", help="Tải phần dữ liệu có nhãn bằng các khoảng HTTP (curl trên Windows)")
    sub.add_parser("audit", help="Tìm ảnh gần trùng giữa các tập dữ liệu")
    features = sub.add_parser("extract", help="Trích và lưu vector đặc trưng ảnh")
    features.add_argument("--feature", required=True, help="Tên nhánh, ví dụ hsv_hog hoặc resnet18")
    features.add_argument("--checkpoint", type=Path, help="Tệp trọng số CNN đã lưu")
    features.add_argument("--batch-size", type=int, default=16, help="Số ảnh xử lý mỗi lượt")
    train = sub.add_parser("train-knn", help="Khảo sát K-NN/PCA, chỉ chọn bằng validation")
    train.add_argument("--feature", required=True, help="Tên nhánh đã trích đặc trưng")
    train.add_argument("--quick", action="store_true", help="Bỏ khảo sát PCA; vẫn khảo sát k/khoảng cách/bỏ phiếu")
    ft = sub.add_parser("finetune", help="Tinh chỉnh CNN thắng, bỏ đầu phân loại tạm rồi trích đặc trưng")
    ft.add_argument("--backbone", choices=["resnet18", "efficientnet_b0"], help="Kiến trúc CNN cần tinh chỉnh")
    ft.add_argument("--batch-size", type=int, default=16, help="Số ảnh mỗi lượt; giảm xuống 8 khi thiếu VRAM")
    ft.add_argument("--head-epochs", type=int, default=5, help="Số vòng học đầu phân loại tạm")
    ft.add_argument("--fine-epochs", type=int, default=10, help="Số vòng tối đa tinh chỉnh khối cuối")
    sub.add_parser("select", help="Khóa mô hình cuối theo kết quả validation")
    ev = sub.add_parser("evaluate", help="Đánh giá mô hình đã khóa trên test")
    ev.add_argument("--all-models", action="store_true", help="Đánh giá mọi nhánh đã huấn luyện")
    pr = sub.add_parser("predict", help="Phân loại một ảnh trên máy")
    pr.add_argument("image", type=Path, help="Đường dẫn ảnh JPG/PNG")
    pr.add_argument("--device", choices=["cpu", "cuda"], help="Ép dùng CPU hoặc GPU NVIDIA; mặc định tự chọn")
    sub.add_parser("illustrations", help="Tạo ảnh minh họa tiền xử lý/phân đoạn")
    args = parser.parse_args()
    args.root = args.root.resolve()
    cmd = args.command
    if cmd == "prepare":
        from .data import prepare
        prepare(args.root, args.download, args.ranged)
    elif cmd == "audit":
        from .data import audit_near_duplicates
        audit_near_duplicates(args.root)
    elif cmd == "extract":
        from .features import extract
        extract(args.root, args.feature, args.checkpoint, args.batch_size)
    elif cmd == "train-knn":
        from .training import tune
        tune(args.root, args.feature, args.quick)
    elif cmd == "finetune":
        from .finetune import finetune
        finetune(args.root, args.backbone, args.batch_size, args.head_epochs, args.fine_epochs)
    elif cmd == "select":
        from .training import select
        select(args.root)
    elif cmd == "evaluate":
        from .evaluation import evaluate
        evaluate(args.root, args.all_models)
    elif cmd == "predict":
        from .inference import Predictor
        print(json.dumps(Predictor(args.root, device=args.device).predict(args.image), ensure_ascii=False, indent=2))
    elif cmd == "illustrations":
        from .evaluation import illustrations
        illustrations(args.root)


if __name__ == "__main__":
    main()
