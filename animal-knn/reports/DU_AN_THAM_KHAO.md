# Dự án mã nguồn tham khảo

Đối chiếu ngày 24/11/2026 bằng Agent Reach: tìm kiếm Exa, đọc README và hai tệp GUI qua Jina. Danh mục kiểm chứng ở `sources/desktop-research.json`. Đây là tài liệu tham khảo phương pháp và luồng sử dụng; mã ứng dụng Windows của đồ án được viết riêng. Chưa chạy lại thí nghiệm của các tác giả, không dùng độ chính xác họ công bố làm kết quả đồ án.

| Kho mã nguồn | Nội dung đã đọc và liên quan | Áp dụng cho đồ án / khác biệt |
| --- | --- | --- |
| [RANA-ATI/Animals-Classification-using-Feature-Extractors](https://github.com/RANA-ATI/Animals-Classification-using-Feature-Extractors) | README mô tả so sánh ảnh thô với HOG/SIFT/ORB, dùng các bộ phân loại gồm K-NN. | Đối chiếu cách tách nhánh đặc trưng và so sánh cùng bộ phân loại. Đồ án dùng HSV/HOG/Hu và CNN, có kiểm soát train/validation/test riêng. |
| [elfchildRichter/Animal_Image_Classification_Unsupervised](https://github.com/elfchildRichter/Animal_Image_Classification_Unsupervised) | README có histogram HSV, đặc trưng kết cấu và VGG16; bảng thí nghiệm có VGG16 + K-NN trên train/validation. | Tham khảo ý tưởng so sánh đặc trưng thủ công với embedding. Đồ án dùng STL-10 sáu lớp, ResNet18/EfficientNet-B0, khảo sát PCA/k/khoảng cách; không so sánh trực tiếp số liệu khác dữ liệu. |
| [AlvaroVasquezAI/Animal_Image_Classification](https://github.com/AlvaroVasquezAI/Animal_Image_Classification) | README và [Program/main.py](https://github.com/AlvaroVasquezAI/Animal_Image_Classification/blob/main/Program/main.py): Tkinter, hộp chọn tệp, hiển thị ảnh bằng Pillow và kết quả phân loại. | Tham khảo luồng mở ảnh → xem ảnh → xem kết quả trong cửa sổ Windows. Kho dùng ResNet50/Keras ba lớp; đồ án giữ K-NN sáu lớp, thêm láng giềng và luồng nền. Điểm bỏ phiếu được ghi đúng tên, không dùng tên probability như ví dụ nguồn. |
| [cyproto/image_classification-animals-with-gui](https://github.com/cyproto/image_classification-animals-with-gui) | README và [ImageClassifier.py](https://github.com/cyproto/image_classification-animals-with-gui/blob/master/ImageClassifier.py): Tkinter hiển thị ảnh, gọi mô hình và nhãn. | Chỉ tham khảo cách gắn kết quả suy luận vào cửa sổ. API TensorFlow 1.x và Pillow cũ trong kho không dùng cho môi trường hiện tại. Đồ án cho người dùng chọn tệp thay vì lấy ngẫu nhiên ảnh test. |

## Quyết định triển khai Windows

Tkinter/ttk có sẵn trong bản Python Windows chính thức, đáp ứng bản mã nguồn kèm `.bat` mà không thêm framework web hay cầu nối trình duyệt. Dùng Pillow để giữ tỷ lệ ảnh khi xem trước và chuyển ảnh sang RGB thống nhất với backend. Tác vụ nạp mô hình/chạy CNN ở luồng nền; chỉ luồng chính cập nhật widget, phù hợp mô hình sự kiện Tcl/Tk. Xem [tài liệu Tkinter Python 3.10](https://docs.python.org/3.10/library/tkinter.html).

Không nhập mô hình hoặc chạy mã từ các kho tham khảo. Không thay dữ liệu, thuật toán hay kết quả đã khóa sau khi xem các dự án khác. Khi tái sử dụng mã bên ngoài trong tương lai cần kiểm tra giấy phép của đúng phiên bản nguồn.
