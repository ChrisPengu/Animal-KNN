# Phân loại động vật bằng K-NN

Đồ án xử lý ảnh và thị giác máy tính cho sáu nhóm **chim, mèo, hươu, chó, ngựa, khỉ**. K-NN luôn đưa ra quyết định phân loại cuối. CNN chỉ trích đặc trưng.

Nếu mới tiếp cận dự án, đọc **[HUONG_DAN_MA_NGUON.md](HUONG_DAN_MA_NGUON.md)**: giải thích từ vựng, sơ đồ tệp và đường đi của một lần phân loại bằng tiếng Việt.

## Chạy ứng dụng Windows

Nhấp đúp **run-desktop.bat** để mở cửa sổ ứng dụng Windows (Tkinter/ttk). Chọn **Mở ảnh…** hoặc ảnh mẫu, rồi nhấn **Phân loại ảnh**. Ứng dụng hiển thị ảnh tiền xử lý, điểm bỏ phiếu của sáu lớp và năm ảnh train gần nhất. Tab **Thông tin & kết quả** chứa cấu hình và bảng thí nghiệm. Phím tắt: **Ctrl+O** mở ảnh, **Ctrl+Enter** phân loại.

Ứng dụng chạy từ mã nguồn Python, không cần trình duyệt, cổng localhost hay kết nối Internet khi phân loại. Mô hình đã lưu đầy đủ. Việc nạp và chạy mô hình diễn ra ở luồng nền để cửa sổ vẫn phản hồi. Đây là bản mã nguồn kèm `.bat` theo yêu cầu, chưa đóng gói `.exe`.

Khi chuyển sang máy Windows khác, cài Python 3.10 từ python.org (bật thành phần **Tcl/Tk and IDLE**), mở PowerShell tại thư mục này và chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
.\run-desktop.bat
```

`requirements.lock.txt` khóa phiên bản thư viện. PyTorch dùng wheel CUDA 12.6; vẫn suy luận bằng CPU khi máy không có GPU NVIDIA. Thư mục `.venv` được Git bỏ qua và được tạo lại trên máy mới. `run-demo.cmd` là tên gọi tương thích, cũng mở ứng dụng Windows.

## Làm việc qua GitHub

Workspace hiện tại: `D:\Xu li anh va thi giac may tinh\BTL`. Có thể mở `run-desktop.bat` ở workspace hoặc trong thư mục `animal-knn` từ vị trí bất kỳ.

Nếu chuyển nguyên `.venv` sang đường dẫn khác, các lệnh `.exe` và activation có thể còn trỏ về đường dẫn cũ. Cách khuyến nghị trên máy mới là tạo lại môi trường bằng bootstrap. Trên cùng máy, có thể sửa môi trường đã chuyển bằng:

```powershell
.\.venv\Scripts\python.exe scripts\repair_workspace.py
.\.venv\Scripts\python.exe -m pip install -e .
```

Luôn dùng `python -m pip` khi sửa môi trường vừa di chuyển. Đường dẫn dữ liệu/mô hình trong ứng dụng được tính từ thư mục mã nguồn, không phụ thuộc thư mục đang mở terminal. Tệp trung gian dựng slide nằm trong `.cache/slides` của dự án.

Thư mục gốc của kho là **thư mục chứa README này**, cùng cấp với `pyproject.toml` và `run-desktop.bat`. Xem [CONTRIBUTING.md](CONTRIBUTING.md) về nhánh, kiểm tra và cách phối hợp nhóm.

Mã, tài liệu, kết quả và danh sách mẫu được đưa vào Git. Dữ liệu thô, cache, môi trường và các tệp trọng số lớn được bỏ qua, vẫn giữ trên máy hiện tại. Sau khi clone, thành viên cần nhận riêng ba tệp trong [models/README.md](models/README.md) để chạy mô hình có sẵn; cài thư viện bằng bootstrap chưa tự tải bộ mô hình đồ án.

Mã và bộ điều khiển giao diện đã được kiểm tra tự động. Kiểm tra trực quan cửa sổ kết quả, tỷ lệ DPI và bố cục khi thu nhỏ chưa hoàn tất do người dùng đã dừng công cụ điều khiển màn hình; chi tiết được ghi trong `results/desktop_checks.json`.

Để xem lỗi trong console, chạy `.\.venv\Scripts\python.exe desktop.py`. Lỗi khởi động được ghi vào `desktop-startup.log`; lỗi nạp mô hình/suy luận vào `results/desktop.log`. Chờ vài giây ở lần phân loại đầu để nạp trọng số. Nếu thiếu `models/best.joblib`, backbone hoặc ảnh tham chiếu, khôi phục đầy đủ thư mục `models` từ bộ bàn giao.

## Kết quả và tài liệu

- `reports/BAO_CAO.html` và `reports/BAO_CAO.md`: phương pháp, số liệu đo thật, phân tích lỗi và giới hạn.
- `reports/THUYET_TRINH.pptx`: slide có biểu đồ và bảng chỉnh sửa được.
- `results/validation_comparison.csv`: so sánh cấu hình bằng validation.
- `results/test_comparison.csv`: kết quả test sau khi khóa lựa chọn.
- `results/tuning/`: toàn bộ khảo sát k, khoảng cách, bỏ phiếu và PCA.
- `results/finetune_history.json`: lịch sử học của CNN.
- `results/external_metrics.json`: kiểm tra riêng 60 ảnh Wikimedia.
- `data/external/manifest.csv`: nguồn, tác giả và giấy phép từng ảnh bên ngoài.
- `data/curation/near_duplicate_review.csv`: quyết định loại ảnh gần trùng trước huấn luyện.
- `reports/DU_AN_THAM_KHAO.md`: các kho mã nguồn liên quan, điểm học hỏi và khác biệt của đồ án.
- `results/desktop_checks.json`: kiểm tra giao diện Windows với mô hình đã lưu.

## Dữ liệu và giao thức

STL-10 có ảnh màu 96 × 96. Chọn nhãn `bird, cat, deer, dog, horse, monkey` theo đúng thứ tự trên, ánh xạ thành 0–5. Chia train/validation theo lớp với seed 42. Các ảnh gần trùng đã xác nhận trực quan được loại khỏi train/validation, giữ toàn bộ 4.800 ảnh test. Số liệu sau làm sạch: **2.385 train, 595 validation, 4.800 test**.

Bốn tệp nhị phân tải từ Stanford được kiểm tra MD5 theo mã nguồn Torchvision. Không dùng 100.000 ảnh không nhãn. Bộ tải theo HTTP range khắc phục kết nối streaming không ổn định trên máy hiện tại.

Đây là **tập con sáu lớp với transfer learning**, khác giao thức STL-10 10-fold chính thức. STL-10 lấy ảnh từ ImageNet và backbone cũng tiền huấn luyện trên ImageNet-1K. Không diễn giải số liệu như một phép thử học hoàn toàn từ STL-10 hoặc như bằng chứng đã loại hết trùng lặp với dữ liệu tiền huấn luyện.

## Tái lập toàn bộ thí nghiệm

Nghiên cứu đã bàn giao được khóa sau khi mở test, nên lệnh tune/select cố ý từ chối thay đổi nó. Để tái lập, dùng một thư mục mới và sao chép danh sách làm sạch đã kiểm chứng:

```powershell
New-Item -ItemType Directory -Force .\reproduction\data\curation
Copy-Item .\data\curation\near_duplicate_review.csv .\reproduction\data\curation\
.\.venv\Scripts\python.exe .\scripts\run_study.py --root .\reproduction --download --ranged
```

Quy trình tự động: chuẩn bị dữ liệu, kiểm tra ảnh gần trùng, chạy các nhánh đặc trưng thủ công/CNN và có/không phân đoạn, khảo sát K-NN/PCA, fine-tune backbone thắng trên validation, chọn mô hình, rồi mới chấm test. Kết quả số thực có thể lệch nhẹ theo phần cứng và phiên bản driver.

Để tái lập bộ ảnh bên ngoài, sao chép `data/external` vào thư mục nghiên cứu mới, rồi chạy `scripts/external_check.py --help` để xem lệnh audit/evaluate.

## Các lệnh riêng

```powershell
.\.venv\Scripts\python.exe -m animal_knn --help
.\.venv\Scripts\python.exe -m animal_knn prepare --download --ranged
.\.venv\Scripts\python.exe -m animal_knn audit
.\.venv\Scripts\python.exe -m animal_knn extract --feature resnet18
.\.venv\Scripts\python.exe -m animal_knn train-knn --feature resnet18
.\.venv\Scripts\python.exe -m animal_knn finetune
.\.venv\Scripts\python.exe -m animal_knn select
.\.venv\Scripts\python.exe -m animal_knn evaluate --all-models
.\.venv\Scripts\python.exe -m animal_knn predict .\assets\examples\cat.jpg
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_desktop.py
```

Các lệnh train, fine-tune và select dành cho nghiên cứu mới chưa mở test. Xem `--root` để chuyển thư mục dữ liệu/kết quả. Đầu CNN tạm thời chỉ dùng trong fine-tune và được bỏ trước khi xây K-NN.

## Đặc trưng và lựa chọn mô hình

Nhánh thủ công dùng histogram HSV 8 × 8 × 8, HOG 9 hướng với cell 8 × 8 và block 2 × 2; nhánh phân đoạn bổ sung 7 Hu moments. GrabCut khởi tạo cố định, chạy 5 vòng, mở/đóng hình thái 3 × 3 và quay về ảnh gốc nếu mặt nạ không hợp lệ. Cặp `hsv_hog`/`hsv_hog_segmented` đo riêng ảnh hưởng tách nền.

ResNet18 và EfficientNet-B0 dùng vector sau pooling. Khảo sát k = 1, 3, 5, 7, 11, 15; Euclidean, Manhattan, cosine; uniform/distance; PCA không dùng/128/256 chiều. Scaler và PCA chỉ fit train. CNN tốt hơn trên validation được fine-tune đầu tạm 5 epoch và khối cuối tối đa 10 epoch, batch 16, mixed precision, dừng sớm sau 3 epoch không cải thiện validation loss.

Quy tắc chọn: validation accuracy, rồi macro-F1, rồi thời gian tìm láng giềng khi hòa điểm. Tập tham chiếu K-NN chỉ chứa train. `models/selection.json` và `results/test_access_receipt.json` ghi lại lựa chọn trước khi mở test.

## Agent Reach

Đã cài Agent Reach từ gói phát hành GitHub chính thức vào `.venv`, xác minh `version`, `doctor`, tìm kiếm và đọc trang web. Các kết quả kiểm tra nằm trong `reports/sources`. Lệnh v1.6 xuất JSON mặc định:

```powershell
.\.venv\Scripts\agent-reach.exe version
.\.venv\Scripts\agent-reach.exe web search "STL10 animal classification KNN" --limit 5
.\.venv\Scripts\agent-reach.exe web read "https://cs.stanford.edu/~acoates/stl10/"
```

Chỉ kênh web được dùng cho đồ án. Không cần đăng nhập mạng xã hội hay API key để chạy demo.

## Giới hạn

Mô hình chọn trong sáu nhóm đã biết, không nhận biết lớp “không phải động vật”. Ảnh nhiều đối tượng, che khuất mạnh, nền lạ và khác biệt ánh sáng có thể gây sai. Điểm bỏ phiếu không phải xác suất hiệu chuẩn. Bộ ngoài 60 ảnh nhỏ và được tuyển chọn bằng truy vấn, nên không đại diện đầy đủ cho ảnh thực tế. Mặt nạ GrabCut không có ground truth trong nghiên cứu này, vì vậy không báo cáo IoU phân đoạn.

Một số ví dụ test có dấu hiệu nhiễu nhãn hoặc ảnh loài ngoài sáu nhóm. Đã đối chiếu ảnh và nhãn với tệp nguồn để loại trừ lỗi ghép dữ liệu; không thay đổi nhãn test sau khi xem kết quả. Accuracy được tính theo nhãn công bố của STL-10.

## Nguồn

- [STL-10, Stanford](https://cs.stanford.edu/~acoates/stl10/)
- [Torchvision STL-10 source](https://github.com/pytorch/vision/blob/v0.24.1/torchvision/datasets/stl10.py)
- [PyTorch transfer learning](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
- [K-NN, scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html)
- [GrabCut, OpenCV](https://docs.opencv.org/4.x/d8/d83/tutorial_py_grabcut.html)
- [Agent Reach](https://github.com/Panniantong/Agent-Reach)

Mã nguồn mới của dự án mang giấy phép MIT. STL-10, trọng số tiền huấn luyện và ảnh Wikimedia có điều khoản riêng; giữ nguyên thông tin nguồn/giấy phép khi tái sử dụng.
