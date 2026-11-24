---
name: Animal K-NN
description: Giao diện Windows bằng Tkinter/ttk cho đồ án phân loại động vật bằng tiếng Việt.
colors:
  primary: "#176B45"
  primary-active: "#115236"
  background: "#FFFFFF"
  secondary-background: "#F1F6F3"
  ink: "#18352A"
  caption: "#496457"
  line: "#DCE6DF"
  error: "#A12323"
typography:
  headline:
    fontFamily: "Segoe UI"
    fontSize: "21pt"
    fontWeight: 700
  result:
    fontFamily: "Segoe UI"
    fontSize: "22pt"
    fontWeight: 700
  heading:
    fontFamily: "Segoe UI"
    fontSize: "13pt"
    fontWeight: 700
  body:
    fontFamily: "Segoe UI"
    fontSize: "10pt"
    fontWeight: 400
  table-heading:
    fontFamily: "Segoe UI"
    fontSize: "10pt"
    fontWeight: 700
spacing:
  compact: "3px"
  xs: "4px"
  field: "6px"
  sm: "8px"
  md: "12px"
  section: "14px"
  lg: "16px"
  panel: "20px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    typography: "{typography.body}"
    padding: "{spacing.sm} {spacing.md}"
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "{colors.background}"
  button-primary-disabled:
    backgroundColor: "{colors.line}"
    textColor: "{colors.caption}"
  button-secondary:
    backgroundColor: "{colors.secondary-background}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.sm} {spacing.md}"
  button-secondary-active:
    backgroundColor: "{colors.line}"
  sample-select:
    backgroundColor: "{colors.background}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.field}"
  notebook-tab:
    backgroundColor: "{colors.secondary-background}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.sm} {spacing.lg}"
  notebook-tab-selected:
    backgroundColor: "{colors.background}"
  image-preview:
    backgroundColor: "{colors.secondary-background}"
    textColor: "{colors.caption}"
    width: "306px"
    height: "205px"
  caption:
    textColor: "{colors.caption}"
    typography: "{typography.body}"
  vote-chart:
    backgroundColor: "{colors.background}"
    textColor: "{colors.caption}"
    typography: "{typography.body}"
    height: "170px"
  table-row:
    backgroundColor: "{colors.background}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    height: "32px"
---

# Design System: Animal K-NN

## Overview

**Creative North Star: "Bàn thực nghiệm tại máy"**

Giao diện dùng nền trắng, chữ xanh đậm và màu xanh nghiên cứu để người xem tập trung vào ảnh động vật cùng bằng chứng phân loại. Bản hiện tại là ứng dụng Windows bằng Tkinter/ttk, khởi động từ mã nguồn qua `run-desktop.bat`. Kiểu điều khiển dùng theme `clam`; không đồng nhất theme này với bộ điều khiển WinUI.

Nhãn tác vụ, hướng dẫn, thông báo và mô tả cấu hình dùng tiếng Việt. Ảnh đầu vào và ảnh huấn luyện là nội dung giải thích chính. Tài liệu ghi nhận mã đã triển khai trong `animal_knn/desktop.py`; `PRODUCT.md` và `.impeccable/surface-briefs/desktop.md` xác lập nền tảng và phạm vi. Người mới đọc mã bắt đầu tại `HUONG_DAN_MA_NGUON.md` và `README.md`.

**Key Characteristics:**

- Cửa sổ Windows với điều khiển Tkinter/ttk và theme `clam`.
- Nền trắng, bề mặt xanh nhạt, chữ xanh đậm và một màu xanh cho hành động chính.
- Segoe UI, nhãn tiếng Việt và các cấp chữ rõ ràng.
- Bố cục phẳng, ảnh thật và điểm bỏ phiếu lấy từ mô hình.

## Colors

Bảng màu kế thừa bản trước, bổ sung màu lỗi và màu nút chính ở trạng thái hoạt động vốn có trong mã Windows. Frontmatter giữ giá trị chuẩn; dải sắc độ trong sidecar chỉ phục vụ tra cứu, chưa được dùng trong giao diện.

### Primary

- **Xanh nghiên cứu** (`primary`): nút phân loại, nhãn kết quả và phần đã đạt của thanh điểm bỏ phiếu.
- **Xanh nhấn nút** (`primary-active`): nền nút phân loại khi ttk báo trạng thái `active`.

### Neutral

- **Nền trắng** (`background`): cửa sổ, khung nội dung, vùng nhập của hộp chọn và biểu đồ.
- **Xanh nền nhạt** (`secondary-background`): nút phụ, tab chưa chọn, nền ảnh xem trước và toàn chiều dài thanh điểm.
- **Mực xanh đậm** (`ink`): tiêu đề, nội dung và tên sáu lớp trên biểu đồ.
- **Xanh chú thích** (`caption`): trạng thái, chú thích ảnh, thông số mô hình và số điểm trên biểu đồ; cũng dùng cho chữ nút bị khóa.
- **Xanh đường phân cách** (`line`): nền nút phụ khi `active` và nền nút chính bị khóa. Mã hiện tại không vẽ lưới biểu đồ bằng màu này.

Màu **đỏ lỗi** (`error`) dành cho lỗi đọc ảnh hoặc nạp/chạy mô hình. Thông báo có nội dung chỉ cách khắc phục, thay vì chỉ đổi màu.

**The Chú thích rõ chữ Rule.** Dùng Xanh chú thích ở nguyên độ đậm cho nội dung hỗ trợ; không giảm thêm độ rõ của chữ trên nền sáng.

Màu chọn dòng, đường viền, dấu focus và thanh tiến trình còn lại do theme `clam` cung cấp; mã không định nghĩa thêm token màu cho chúng.

## Typography

**Phông chữ:** Segoe UI cho nhãn, điều khiển, bảng và chữ vẽ trên Canvas. Cỡ dương trong khai báo font Tk là point; các token `pt` ghi lại đơn vị này. Mã không định nghĩa phông thay thế, khoảng cách ký tự hoặc chiều cao dòng riêng.

### Hierarchy

- **Headline:** tiêu đề nội dung qua `Title.TLabel`.
- **Result:** nhãn kết quả nổi bật qua `Result.TLabel`, dùng Xanh nghiên cứu.
- **Heading:** tiêu đề khu vực qua `Heading.TLabel`.
- **Body:** nội dung thường, nút, chú thích, nhãn biểu đồ và dòng dữ liệu trong bảng.
- **Table heading:** đầu cột `Treeview.Heading`, cùng cỡ chữ nội dung nhưng đậm.

Lời nhắc trên vùng ảnh trống dùng Segoe UI 11 point trong Canvas. Nhãn nguồn ảnh có chiều rộng xuống dòng bằng vùng xem trước; thời gian suy luận và cấu hình tự cập nhật `wraplength` theo chiều rộng khung kết quả. Không có một cơ chế xuống dòng chung cho mọi nhãn.

**The Tiếng Việt trước Rule.** Giữ dấu tiếng Việt và tên tác vụ dễ hiểu trên giao diện; tên API và khóa cấu hình trong mã tiếp tục theo thư viện đang dùng.

## Layout

Cửa sổ khởi tạo ở 1240 × 840, có mức tối thiểu được đặt trong mã là 1080 × 760. Khung ngoài có lề ngang theo token `xl`, lề dọc theo `lg`. Notebook có hai tab **Phân loại ảnh** và **Thông tin & kết quả**. Không có mục tiêu giao diện di động hoặc quy tắc chuyển cột kiểu trang web.

Tab phân loại đặt hàng chọn tệp, ảnh mẫu, nút phân loại, trạng thái và tiến trình phía trên. Vùng làm việc bên dưới dùng hai cột: cột trái có `minsize=330` và không nhận trọng số giãn; cột phải có trọng số giãn 1. Khoảng cách sau cột trái theo `xl`. Đây là bố cục màn hình phân loại hiện tại, không phải lưới bắt buộc cho mọi màn hình tương lai.

Ảnh đầu vào nằm giữa Canvas theo kích thước token `image-preview`. Bên dưới là ảnh tiền xử lý 96 × 96 pixel. Khung kết quả chứa nhãn dự đoán, thời gian, biểu đồ và cấu hình. Hàng bằng chứng dưới cùng chia năm cột có cùng trọng số; mỗi ảnh tham chiếu được hiển thị 90 × 90, kèm tên lớp, khoảng cách và mã ảnh train. Tab thông tin có văn bản và bảng `Treeview` với tám dòng hiển thị.

Khoảng cách frontmatter phản ánh các số đã dùng trong `padding`, `padx` và `pady`. Đây là khoảng cách Tk trong mã, không phải cam kết kích thước vật lý ở mọi mức DPI. Hàng công cụ, các nhãn chưa có `wraplength` và bảng không có cơ chế tự xếp lại toàn bộ.

`results/desktop_checks.json` ghi nhận sáu ảnh mẫu khớp backend trong kiểm tra Tkinter ẩn. Tệp này ghi rõ việc điều khiển màn hình đã được người dùng dừng và việc duyệt cửa sổ kết quả còn chờ. Chưa xác minh trực quan cửa sổ kết quả, DPI hoặc cắt chữ/điều khiển ở mức tối thiểu; các kích thước trong mã không thay thế bằng chứng đó.

## Elevation & Depth

Các khung ttk và Canvas dùng bề mặt phẳng, không có bóng đổ do ứng dụng thêm. Nền xanh nhạt, khoảng cách, dấu phân cách và các cấp chữ phân vùng nội dung. Viền và dấu focus do theme `clam` xử lý; không có màu hoặc độ dày focus riêng được khai báo trong ứng dụng.

**The Trạng thái theo ttk Rule.** Giữ trạng thái `active`, `disabled`, `readonly` và `selected` của điều khiển ttk; chỉ ghi đè các giá trị đã khai báo trong `_styles`.

Ứng dụng không định nghĩa chuyển động trang trí. Thanh tiến trình bất định chạy trong lúc nạp hoặc suy luận; chu kỳ nhận dữ liệu từ luồng nền thuộc cơ chế phản hồi của ứng dụng, không phải token chuyển động thị giác.

## Shapes

Khung và điều khiển có dáng phẳng theo theme `clam`. Mã không đặt bán kính góc, nên frontmatter không có nhóm `rounded`. Nút có `borderwidth=1`, Notebook có `borderwidth=0`; Canvas ảnh và biểu đồ tắt `highlightthickness`. Không suy ra một hệ góc bo từ bản nền tảng cũ.

Ảnh đầu vào dùng `ImageOps.contain` để vừa vùng xem trước và giữ tỉ lệ. Ảnh tiền xử lý được đưa về hình vuông theo pipeline, khác mục đích với ảnh xem trước. Ảnh tham chiếu trong kho được đổi kích thước về ô vuông khi hiển thị. Các thanh điểm là hình chữ nhật Canvas không có viền.

## Components

### Nút thao tác

**Mở ảnh…** là `ttk.Button` phụ; **Phân loại ảnh** dùng `Action.TButton`. Padding trong frontmatter viết theo thứ tự dọc/ngang, tương ứng `(12, 8)` trong ttk. Màu nền `active` và chữ/nền bị khóa lấy từ các biến thể đã ghi. Nút phân loại bị khóa khi chưa có ảnh hợp lệ hoặc đang xử lý. Khi đang bận, nút mở ảnh và hộp ảnh mẫu cũng bị khóa.

### Chọn tệp và ảnh mẫu

Chọn tệp dùng hộp thoại Windows qua `filedialog.askopenfilename`, có bộ lọc JPG/PNG. Ảnh mẫu dùng `ttk.Combobox` rộng 15 đơn vị ký tự, trạng thái `readonly` khi rảnh. Không có vùng kéo thả hoặc ô nhập văn bản độc lập. **Ctrl+O** mở hộp thoại; **Ctrl+Enter** phân loại ảnh.

### Điều hướng

`ttk.Notebook` chuyển giữa hai tab; tab được chọn có nền trắng, tab còn lại có nền xanh nhạt. Padding tab dùng các token đã ghi. Thao tác focus và phím điều hướng còn lại do ttk cung cấp, chưa có xác nhận duyệt trực quan riêng trong lần đối chiếu tài liệu này.

### Ảnh và bằng chứng láng giềng

Canvas ảnh trống có lời nhắc bắt đầu. Khi chọn ảnh hợp lệ, giao diện hiển thị ảnh và tên/kích thước tệp. Thay ảnh hoặc chọn tệp hỏng đều xóa kết quả, thanh điểm và năm ảnh tham chiếu cũ. Nhóm láng giềng dùng `ttk.Label` cho ảnh và chú thích, không thêm khung thẻ riêng. Khoảng cách hiển thị ba chữ số thập phân; mã ảnh giữ nguyên từ backend.

### Biểu đồ điểm bỏ phiếu

Biểu đồ do `tk.Canvas` vẽ lại khi khung thay đổi kích thước. Mỗi lớp có tên bên trái, nền thanh xanh nhạt, phần điểm xanh nghiên cứu và số bên phải. Thứ tự giữ **Chim, Mèo, Hươu, Chó, Ngựa, Khỉ**. Thanh có chiều rộng tỷ lệ với điểm từ 0 đến 1; số có ba chữ số thập phân, còn trạng thái chưa có kết quả hiển thị dấu gạch ngang. Không có trục, lưới hoặc tooltip được lập trình cho biểu đồ này.

Chú thích luôn nêu **điểm bỏ phiếu không phải xác suất đã được hiệu chuẩn**. K-NN quyết định nhãn cuối; CNN chỉ trích đặc trưng. Năm ảnh minh họa gần nhất không đồng nghĩa với giá trị `k` của mô hình.

### Trạng thái, lỗi và bảng thông tin

`ttk.Progressbar` ở chế độ bất định báo đang nạp/chạy mô hình; nhãn trạng thái đi kèm giải thích công việc. Luồng nền không sửa widget. Luồng Tk nhận dữ liệu qua hàng đợi, cập nhật kết quả và mở lại điều khiển. Đóng cửa sổ khi đang xử lý sẽ chờ tác vụ trả về trước khi hủy Tk.

Lỗi tệp hiển thị cạnh ảnh; lỗi mô hình hiển thị trong khung kết quả cùng cách thử lại và đường dẫn log. Thông báo dùng lại ảnh gốc khi phân đoạn không ổn định nằm trong cấu hình. Bảng ở tab thông tin đọc `results/test_comparison.csv`, có đầu cột tiếng Việt và định dạng phần trăm; tài liệu không tự tạo lại số liệu đánh giá.

Sidecar schema v2 bổ sung mô tả widget và nguồn mã. Các mục thành phần mô tả bản Tkinter thực tế, không cung cấp bản dựng giao diện bằng công nghệ khác.

## Do's and Don'ts

### Do:

- Do dùng Tkinter/ttk, theme `clam` và Segoe UI theo mã Windows hiện tại.
- Do giữ nhãn tác vụ, thông báo và hướng dẫn dùng tiếng Việt dễ hiểu.
- Do giữ chú thích rõ chữ, ảnh thật, tên lớp, khoảng cách và mã ảnh train.
- Do duy trì trạng thái khóa điều khiển, tiến trình và thông báo lỗi có cách khắc phục.
- Do phân biệt bằng chứng kiểm tra ẩn với việc duyệt trực quan cửa sổ Windows.

### Don't:

- Don't chuyển màn hình này thành ứng dụng web hoặc thay đổi nhận diện đã được giữ lại.
- Don't thêm góc bo, bóng đổ hay chuyển động trang trí không có trong bản triển khai.
- Don't gọi điểm bỏ phiếu là xác suất đã hiệu chuẩn hoặc nhầm năm ảnh minh họa với giá trị k.
- Don't công bố DPI hoặc bố cục ở kích thước tối thiểu đã đạt khi chưa có kiểm tra trực quan.
