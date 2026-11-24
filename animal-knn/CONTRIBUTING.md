# Làm việc cùng nhóm

## Chuẩn bị máy

Clone kho, cài Python 3.10 Windows có Tcl/Tk, rồi chạy `bootstrap.ps1` theo README. Mỗi người tự tạo `.venv`; không sao chép môi trường của máy khác. Đọc `HUONG_DAN_MA_NGUON.md` để làm quen luồng xử lý.

Git chỉ chứa mã, tài liệu, ảnh mẫu, danh sách dữ liệu và số đo thí nghiệm. Các tệp mô hình lớn được giữ ngoài Git; xem `models/README.md` để nhận đúng bộ mô hình từ thành viên phụ trách. Sau khi chép các tệp này vào đúng vị trí, mở `run-desktop.bat`.

## Thay đổi mã

1. Tạo nhánh riêng, ví dụ `git switch -c ten-ban/sua-giao-dien`.
2. Sửa phần liên quan, giữ nhãn và thông báo cho người dùng bằng tiếng Việt. Tên API Python vẫn theo quy ước thư viện.
3. Chạy `.\.venv\Scripts\python.exe -m pytest -q`. Khi sửa suy luận/giao diện, chạy thêm `scripts/check_desktop.py` sau khi có mô hình.
4. Kiểm tra `git status` và `git diff` trước khi commit; không thêm dữ liệu, môi trường, log, mật khẩu hoặc trọng số bằng `git add -f`.
5. Push nhánh của mình và mở Pull Request, ghi rõ thay đổi và cách kiểm tra. Nhờ thành viên khác đọc trước khi gộp.

## Bảo toàn thí nghiệm

Không thay `results/test_access_receipt.json`, nhãn test hoặc số đo cũ để phù hợp mô hình mới. Bộ hiện tại đã khóa sau test. Thí nghiệm mới dùng thư mục `--root` riêng theo README; thống nhất với nhóm trước khi cập nhật kết quả chuẩn. Không đổi thứ tự sáu nhãn trong mô hình chỉ để đổi cách hiển thị.

## Phân công theo tệp

- Giao diện: `animal_knn/desktop.py`.
- Trích đặc trưng/suy luận: `features.py`, `inference.py`.
- Dữ liệu/thí nghiệm: `data.py`, `training.py`, `finetune.py`, `evaluation.py`.
- Tài liệu: README, hướng dẫn đọc mã, báo cáo trong `reports`.

Khi chia sẻ dữ liệu hoặc mô hình qua kênh khác, giữ tên tệp, đường dẫn và thông tin nguồn/giấy phép. Không commit bộ trọng số mới khi chưa thống nhất cách phân phối với nhóm.
