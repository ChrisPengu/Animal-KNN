# Làm quen với mã nguồn

Tài liệu này dành cho người mới đọc Python và đồ án thị giác máy tính. Bắt đầu bằng việc chạy ứng dụng, sau đó lần theo một ảnh từ lúc chọn tệp đến lúc có kết quả. Các nhãn, thông báo và hướng dẫn dùng tiếng Việt. Tên hàm/biến giữ quy ước Python và thuật ngữ của thư viện để dễ tìm tài liệu chính thức, tránh đổi tên API đang được dùng.

## Chạy thử trong vài phút

1. Nhấp đúp `run-desktop.bat`. Nếu chưa có môi trường Python, làm bước cài đặt trong `README.md` trước.
2. Trong tab **Phân loại ảnh**, chọn **Mở ảnh…** hoặc một **Ảnh mẫu**.
3. Nhấn **Phân loại ảnh**. Lần đầu cần nạp mô hình; thanh tiến trình cho biết chương trình đang làm việc.
4. Xem nhãn dự đoán, điểm bỏ phiếu của sáu nhóm và năm ảnh huấn luyện gần nhất. Khoảng cách nhỏ hơn nghĩa là vector đặc trưng gần hơn theo cấu hình đã chọn.
5. Tab **Thông tin & kết quả** giải thích mô hình và bảng đánh giá. Kết quả một ảnh có thể sai: ảnh mẫu ngựa hiện có bị dự đoán thành hươu; không sửa nhãn hay mô hình để che ví dụ này.

Phím tắt: **Ctrl+O** chọn ảnh; **Ctrl+Enter** phân loại. Tệp ảnh hỏng sẽ có thông báo để chọn lại, không tiếp tục giữ kết quả của ảnh cũ. Không cần Internet khi phân loại ảnh.

## Những khái niệm cần biết

| Từ trong mã nguồn | Nghĩa trong đồ án |
| --- | --- |
| `feature` / đặc trưng | Dãy số mô tả màu, hình dạng hoặc nội dung ảnh. K-NN so sánh các dãy số này. |
| HSV, HOG, Hu moments | Đặc trưng màu, phân bố hướng cạnh và hình dạng. Đây là các nhánh cơ sở. |
| `backbone` / CNN | Mạng trích đặc trưng, như EfficientNet-B0. Đầu phân loại CNN đã bỏ; CNN không quyết định nhãn cuối. |
| `PCA` | Giảm số chiều của vector; bộ biến đổi chỉ được học từ train. |
| `k` | Số láng giềng tham gia bỏ phiếu. Mô hình cuối dùng k = 7. Giao diện chỉ hiển thị năm ảnh gần nhất để tiện xem. |
| `metric` | Cách đo khoảng cách: Euclid, Manhattan hoặc Cosin. |
| `weights` | Cách bỏ phiếu: đều nhau hoặc ảnh gần có trọng số lớn hơn. |
| `vote_scores` | Điểm bỏ phiếu của sáu nhóm, tổng bằng 1. Không phải xác suất đã được hiệu chuẩn. |
| `train` / `val` / `test` | Tập học / tập chọn cấu hình / tập đánh giá cuối. Không đưa ảnh val/test vào kho láng giềng. |
| `checkpoint` | Tệp trọng số CNN đã lưu, để suy luận lại mà không tải mạng. |
| `manifest` | Bảng ghi mã ảnh, nhãn và tập dữ liệu của từng mẫu. |

## Đọc tệp nào trước

| Thứ tự | Tệp | Vai trò / chỗ nên đọc |
| --- | --- | --- |
| 1 | `run-desktop.bat`, `desktop.py` | Mở Python của dự án và khởi động cửa sổ, ghi lỗi khởi động nếu có. |
| 2 | `animal_knn/desktop.py` | Lớp `DesktopApp` dựng giao diện. `load_image` đọc ảnh; `classify` giao tác vụ cho luồng nền; `_poll` nhận và hiển thị kết quả. |
| 3 | `animal_knn/inference.py` | `Predictor` nạp bộ mô hình và xử lý một lần dự đoán. Đây là cầu nối chung cho giao diện và dòng lệnh. |
| 4 | `animal_knn/common.py` | Nhãn Anh/Việt, đường dẫn gốc và `read_image`: sửa hướng EXIF, chuyển RGB, ghép nền trắng cho ảnh trong suốt. |
| 5 | `animal_knn/features.py` | Chuẩn hóa kích thước, GrabCut và các bộ trích vector. |
| 6 | `animal_knn/training.py` | Khảo sát K-NN/PCA, chọn bằng validation và lưu mô hình. |
| 7 | `animal_knn/finetune.py` | Tinh chỉnh bộ trích CNN; bỏ đầu phân loại tạm rồi xây lại K-NN. |
| 8 | `animal_knn/data.py`, `evaluation.py` | Chuẩn bị dữ liệu, kiểm tra trùng và đánh giá test, tạo chỉ số/ma trận nhầm lẫn. |
| 9 | `animal_knn/cli.py` | Gắn các chức năng trên thành lệnh. Chạy `python -m animal_knn --help` để xem hướng dẫn tiếng Việt. |

## Một lần phân loại đi qua đâu

`Chọn tệp → read_image → DesktopApp.classify → luồng nền → Predictor.predict → Extractor.batch → chuẩn hóa/PCA → K-NN → hàng đợi → DesktopApp._poll → vẽ kết quả`

Luồng nền chỉ nhận ảnh, đường dẫn và mô hình. Nó không tạo hoặc sửa widget Tk. Tk gọi `_poll` định kỳ trên luồng chính; nhờ đó cửa sổ vẫn phản hồi khi mô hình đang nạp hoặc xử lý. Khi đang bận, nút mở ảnh và chọn ảnh mẫu bị khóa để kết quả không gắn vào nhầm ảnh.

Trong `Predictor.predict`, K-NN trả điểm bỏ phiếu và tìm năm láng giềng. `reference_index` trỏ vào ảnh tham chiếu đã lưu; `id` là mã mẫu train để kiểm tra nguồn. Thứ tự nhãn luôn là **chim, mèo, hươu, chó, ngựa, khỉ**; không tự đổi thứ tự này khi sửa giao diện.

## Tự gọi mô hình mà không mở cửa sổ

Mở PowerShell ở thư mục dự án:

```powershell
.\.venv\Scripts\python.exe -m animal_knn predict .\assets\examples\cat.jpg
```

Hoặc trong Python (dùng đúng môi trường của dự án):

```python
from animal_knn.common import ROOT
from animal_knn.inference import Predictor

bo_du_doan = Predictor(ROOT)  # Nạp một lần, dùng lại cho nhiều ảnh.
ket_qua = bo_du_doan.predict(ROOT / "assets/examples/cat.jpg")
print(ket_qua["class_name_vi"])
print(ket_qua["vote_scores"])
```

## Sửa và kiểm tra

- Đổi nhãn hiển thị/cách sắp xếp: sửa `animal_knn/desktop.py`, đặc biệt `_build`, `FEATURE_NAMES` và `_show_result`. Đừng đổi khóa cấu hình trong tệp mô hình chỉ để đổi chữ trên giao diện.
- Đổi thuật toán: làm thí nghiệm ở **thư mục nghiên cứu mới** theo README. Bộ hiện tại đã khóa sau test; các lệnh tune/select sẽ từ chối ghi lại để tránh chọn theo test.
- Kiểm tra mã: `.\.venv\Scripts\python.exe -m pytest -q`. Kiểm thử Tkinter chạy ẩn, không dùng chuột/bàn phím.
- Kiểm tra cửa sổ với mô hình thật: `.\.venv\Scripts\python.exe scripts\check_desktop.py`. Sáu ảnh mẫu được đối chiếu nhãn/điểm/láng giềng với backend; đây là kiểm tra tính nhất quán phần mềm, không phải một benchmark mới.
- Lỗi khởi động: xem `desktop-startup.log`. Lỗi suy luận: xem `results/desktop.log`. Cài Python Windows với thành phần Tcl/Tk; dùng `bootstrap.ps1` để cài đúng thư viện.

`models` chứa mô hình/encoder/ảnh tham chiếu. `data` chứa dữ liệu và danh sách mẫu. `results` chứa số đo gốc. `reports` chứa báo cáo, slide và [dự án tham khảo](reports/DU_AN_THAM_KHAO.md). Các ảnh ngoài đều có nguồn và giấy phép riêng, không thuộc giấy phép MIT của mã mới.
