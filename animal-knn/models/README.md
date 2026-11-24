# Mô hình dùng chung

Trọng số và ảnh tham chiếu được giữ trên máy và bỏ qua bằng `.gitignore`. Clone GitHub chỉ lấy mã và tài liệu, chưa đủ để phân loại ngay.

Để chạy mô hình đã đánh giá, nhận ba tệp sau từ thành viên đang giữ bản mô hình chuẩn và chép đúng đường dẫn (không cần ZIP):

```text
models/best.joblib
models/reference_images.npz
models/backbones/efficientnet_b0_finetuned.pt
```

Giữ `models/selection.json` từ kho Git để đối chiếu cấu hình. SHA-256 của `best.joblib` phải khớp `best_model_sha256` trong `results/test_access_receipt.json`. Chỉ nạp tệp joblib từ thành viên/nguồn tin cậy vì định dạng này có thể thực thi mã khi nạp.

Mô hình dùng EfficientNet-B0 đã tinh chỉnh → PCA 128 → K-NN, k = 7, Euclid, bỏ phiếu theo khoảng cách. Tập tham chiếu có 2.385 ảnh train. Ứng dụng không cần các mô hình nhánh còn lại hoặc dữ liệu thô để suy luận.

Nhóm có thể chia sẻ riêng từng tệp bằng kênh nội bộ hoặc GitHub Releases sau khi thống nhất. Chưa có đường dẫn tải công khai tự động. Để tái lập toàn bộ nghiên cứu thay vì dùng mô hình có sẵn, làm theo README và chuẩn bị dữ liệu mới.
