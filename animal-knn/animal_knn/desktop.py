"""Cửa sổ Windows: chọn ảnh → chạy K-NN → xem điểm và năm láng giềng.

Đọc HUONG_DAN_MA_NGUON.md trước khi sửa. Luồng chính vẽ giao diện;
luồng nền chỉ chạy mô hình và gửi dữ liệu về qua hàng đợi, không đụng widget.
"""
from __future__ import annotations

import csv
import logging
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageOps, ImageTk

from .common import CLASSES, ROOT, VI, read_image

INK = "#18352A"
MUTED = "#496457"
GREEN = "#176B45"
PALE = "#F1F6F3"
LINE = "#DCE6DF"
ERROR = "#A12323"
FEATURE_NAMES = {
    "hsv_hog": "Màu HSV + HOG",
    "hsv_hog_segmented": "Màu HSV + HOG, tách nền",
    "hsv_hog_hu_segmented": "Màu HSV + HOG + Hu, tách nền",
    "resnet18": "ResNet18",
    "resnet18_segmented": "ResNet18, tách nền",
    "efficientnet_b0": "EfficientNet-B0",
    "efficientnet_b0_segmented": "EfficientNet-B0, tách nền",
    "efficientnet_b0_finetuned": "EfficientNet-B0 đã tinh chỉnh",
    "resnet18_finetuned": "ResNet18 đã tinh chỉnh",
}
METRIC_NAMES = {"euclidean": "Euclid", "manhattan": "Manhattan", "cosine": "Cosin"}
VOTING_NAMES = {"distance": "Theo khoảng cách", "uniform": "Đều nhau"}


def _predict_in_background(project, factory, engine, image, events):
    # Luồng nền chỉ nhận dữ liệu; mọi thao tác với Tk nằm ở _poll trên luồng chính.
    try:
        if engine is None:
            if factory:
                engine = factory(project)
            else:
                import torch
                from .inference import Predictor
                torch.set_num_threads(4)
                engine = Predictor(project)
        events.put(("result", (engine, engine.predict(image))))
    except Exception:
        logging.exception("Desktop prediction failed")
        events.put(("error", "Không nạp hoặc xử lý được mô hình. Kiểm tra thư mục models, "
                    "môi trường theo README, rồi nhấn Phân loại ảnh để thử lại. "
                    "Chi tiết: results/desktop.log."))


class DesktopApp(tk.Tk):
    """Ghép các phần giao diện và giữ trạng thái ảnh/kết quả đang xem."""
    def __init__(self, project=ROOT, predictor_factory=None):
        super().__init__()
        self.project = Path(project)
        self.predictor_factory = predictor_factory
        self.engine = None
        self.image = None
        self.result = None
        self.busy = False
        self.closing = False
        self.events = queue.Queue()
        self.photos = {}
        self.title("Animal K-NN — Phân loại động vật")
        self.geometry("1240x840+60+30")
        self.minsize(1080, 760)
        self.configure(bg="white")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._styles()
        self._build()
        self.bind("<Control-o>", lambda _event: self.choose_file())
        self.bind("<Control-Return>", lambda _event: self.classify())
        self.after_id = self.after(60, self._poll)

    def _styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=INK, background="white")
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white", foreground=INK)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 22, "bold"), foreground=GREEN)
        style.configure("TButton", padding=(12, 8), background=PALE, borderwidth=1)
        style.map("TButton", background=[("active", LINE)], foreground=[("disabled", MUTED)])
        style.configure("Action.TButton", foreground="white", background=GREEN)
        style.map("Action.TButton", background=[("disabled", LINE), ("active", "#115236")],
                  foreground=[("disabled", MUTED), ("!disabled", "white")])
        style.configure("TCombobox", padding=6, fieldbackground="white")
        style.configure("TNotebook", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", "white"), ("!selected", PALE)])
        style.configure("Treeview", rowheight=32, fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=8)

    def _build(self):
        shell = ttk.Frame(self, padding=(24, 16))
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="Phân loại động vật", style="Title.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Chim · Mèo · Hươu · Chó · Ngựa · Khỉ  |  Một động vật nổi bật trong ảnh",
                  style="Muted.TLabel").pack(anchor="w", pady=(3, 12))
        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True)
        page = ttk.Frame(notebook, padding=(0, 14, 0, 0))
        notebook.add(page, text="Phân loại ảnh")
        info = ttk.Frame(notebook, padding=20)
        notebook.add(info, text="Thông tin & kết quả")
        self._info(info)

        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x")
        self.open_button = ttk.Button(toolbar, text="Mở ảnh…", command=self.choose_file)
        self.open_button.pack(side="left", padx=(0, 12))
        ttk.Label(toolbar, text="Ảnh mẫu:").pack(side="left", padx=(0, 7))
        self.sample = tk.StringVar(value="Chọn ảnh mẫu")
        self.sample_box = ttk.Combobox(toolbar, textvariable=self.sample, state="readonly",
                                       values=["Chọn ảnh mẫu"] + VI, width=15)
        self.sample_box.pack(side="left")
        self.sample_box.bind("<<ComboboxSelected>>", self.choose_sample)
        self.classify_button = ttk.Button(toolbar, text="Phân loại ảnh", style="Action.TButton",
                                          command=self.classify, state="disabled")
        self.classify_button.pack(side="left", padx=12)
        self.progress = ttk.Progressbar(toolbar, mode="indeterminate", length=125)
        self.progress.pack(side="right", padx=(12, 0))
        self.status = tk.StringVar(value="Sẵn sàng · Chọn JPG hoặc PNG")
        self.status_label = ttk.Label(toolbar, textvariable=self.status, style="Muted.TLabel", wraplength=240)
        self.status_label.pack(side="right")

        area = ttk.Frame(page)
        area.pack(fill="both", expand=True, pady=(18, 0))
        area.columnconfigure(0, weight=0, minsize=330)
        area.columnconfigure(1, weight=1)
        area.rowconfigure(0, weight=1)
        left = ttk.Frame(area)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
        ttk.Label(left, text="Ảnh đầu vào", style="Heading.TLabel").pack(anchor="w")
        self.input_canvas = tk.Canvas(left, width=306, height=205, bg=PALE, highlightthickness=0)
        self.input_canvas.pack(pady=(8, 4), anchor="w")
        self.input_canvas.create_text(153, 102, text="Mở một ảnh để bắt đầu", fill=MUTED,
                                       font=("Segoe UI", 11), tags="placeholder")
        self.source_label = ttk.Label(left, text="JPG / PNG · Ctrl+O để chọn tệp", style="Muted.TLabel",
                                       wraplength=306)
        self.source_label.pack(anchor="w", pady=(0, 12))
        preview = ttk.Frame(left)
        preview.pack(fill="x")
        self.preprocess_canvas = tk.Canvas(preview, width=96, height=96, bg=PALE, highlightthickness=0)
        self.preprocess_canvas.pack(side="left", anchor="n")
        ttk.Label(preview, text="Ảnh tiền xử lý\nRGB · 96 × 96 pixel\ntrước khi trích đặc trưng",
                  style="Muted.TLabel", justify="left").pack(side="left", padx=12)

        right = ttk.Frame(area)
        right.grid(row=0, column=1, sticky="nsew")
        self.result_label = ttk.Label(right, text="Kết quả phân loại", style="Result.TLabel")
        self.result_label.pack(anchor="w")
        self.timing_label = ttk.Label(right, text="Chọn ảnh, sau đó nhấn “Phân loại ảnh”.", style="Muted.TLabel")
        self.timing_label.pack(anchor="w", pady=(3, 10))
        ttk.Label(right, text="Điểm bỏ phiếu K-NN", style="Heading.TLabel").pack(anchor="w")
        self.chart = tk.Canvas(right, height=170, bg="white", highlightthickness=0)
        self.chart.pack(fill="x", pady=(4, 3))
        self.chart.bind("<Configure>", lambda _event: self._draw_votes())
        ttk.Label(right, text="Điểm bỏ phiếu không phải xác suất đã được hiệu chuẩn.",
                  style="Muted.TLabel").pack(anchor="w")
        self.config_label = ttk.Label(right, text="K-NN dùng các ảnh train làm tập tham chiếu.\n"
                                     "Lần phân loại đầu cần thêm thời gian nạp mô hình.",
                                     wraplength=650, style="Muted.TLabel", justify="left")
        self.config_label.pack(anchor="w", pady=(14, 0))
        right.bind("<Configure>", lambda event: self._wrap_result(event.width))
        self._draw_votes()

        evidence = ttk.Frame(page)
        evidence.pack(fill="x", pady=(14, 0))
        ttk.Separator(evidence).pack(fill="x", pady=(0, 12))
        ttk.Label(evidence, text="Năm ảnh huấn luyện gần nhất", style="Heading.TLabel").pack(anchor="w")
        self.neighbor_frame = ttk.Frame(evidence)
        self.neighbor_frame.pack(fill="x", pady=(8, 0))
        self.neighbor_widgets = []
        for col in range(5):
            self.neighbor_frame.columnconfigure(col, weight=1, uniform="neighbor")
            box = ttk.Frame(self.neighbor_frame)
            box.grid(row=0, column=col, sticky="nw")
            image = ttk.Label(box)
            image.pack(anchor="w")
            label = ttk.Label(box, text="—", style="Muted.TLabel", justify="left")
            label.pack(anchor="w", pady=(3, 0))
            self.neighbor_widgets.append((image, label))

    def _info(self, page):
        ttk.Label(page, text="K-NN kết hợp đặc trưng ảnh", style="Heading.TLabel").pack(anchor="w")
        text = ("Ứng dụng Windows chạy hoàn toàn trên máy; ảnh không được gửi lên dịch vụ nào.\n\n"
                "Mô hình cuối: EfficientNet-B0 trích đặc trưng → PCA 128 → K-NN.\n"
                "CNN tiền huấn luyện ImageNet, fine-tune bằng train; K-NN quyết định nhãn cuối.\n"
                "Chỉ 2.385 ảnh train được dùng làm láng giềng; validation 595 ảnh; test 4.800 ảnh.\n\n"
                "Bảng dưới là kết quả test theo nhãn công bố STL-10, sau khi khóa cấu hình.\n"
                "Đây là tập con sáu lớp với transfer learning, khác giao thức STL-10 chính thức.")
        ttk.Label(page, text=text, justify="left", wraplength=1000).pack(anchor="w", pady=12)
        table = ttk.Treeview(page, columns=("feature", "accuracy", "macro_f1"), show="headings", height=8)
        for col, title, width in [("feature", "Đặc trưng", 410), ("accuracy", "Độ chính xác", 170),
                                  ("macro_f1", "F1 trung bình (macro)", 205)]:
            table.heading(col, text=title)
            table.column(col, width=width, anchor="w")
        path = self.project / "results/test_comparison.csv"
        if path.exists():
            with path.open(encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    table.insert("", "end", values=(FEATURE_NAMES.get(row["feature"], row["feature"]), f'{float(row["accuracy"]):.2%}',
                                                      f'{float(row["macro_f1"]):.2%}'))
        table.pack(fill="x", pady=(0, 16))
        ttk.Label(page, text="Giới hạn: luôn chọn trong sáu nhóm đã biết, chưa phát hiện lớp lạ.\n"
                  "Ảnh nhiều động vật, che khuất hoặc nền khác biệt có thể bị phân loại sai.\n"
                  "Nguồn và giấy phép ảnh mẫu: assets/examples/sources.json.\n\n"
                  "Phím tắt: Ctrl+O mở ảnh · Ctrl+Enter phân loại ảnh.\n"
                  "Báo cáo và nguồn tham khảo nằm trong thư mục reports của dự án.\n"
                  "Mới đọc mã? Bắt đầu ở HUONG_DAN_MA_NGUON.md.",
                  style="Muted.TLabel", justify="left", wraplength=1000).pack(anchor="w")

    def choose_file(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(parent=self, title="Chọn ảnh động vật",
                                         filetypes=[("Ảnh JPG / PNG", "*.jpg *.jpeg *.png"), ("Tất cả tệp", "*.*")])
        if path:
            self.sample.set("Chọn ảnh mẫu")
            self.load_image(path)

    def choose_sample(self, _event=None):
        if not self.busy and self.sample.get() in VI:
            self.load_image(self.project / "assets/examples" / f"{CLASSES[VI.index(self.sample.get())]}.jpg")

    def _clear_result(self):
        self.result = None
        self.result_label.configure(text="Kết quả phân loại")
        self.timing_label.configure(text="Chọn ảnh, sau đó nhấn “Phân loại ảnh”.")
        self.config_label.configure(foreground=MUTED, text="K-NN dùng các ảnh train làm tập tham chiếu.\n"
                                     "Lần phân loại đầu cần thêm thời gian nạp mô hình.")
        for image, label in self.neighbor_widgets:
            image.configure(image="")
            label.configure(text="—")
        self._draw_votes()

    def load_image(self, path):
        """Đọc JPG/PNG và xóa dự đoán cũ để tránh gán kết quả cho nhầm ảnh."""
        if self.busy:
            return
        self._clear_result()
        self.image = None
        self.input_canvas.delete("all")
        self.preprocess_canvas.delete("all")
        self.classify_button.configure(state="disabled")
        try:
            self.image = read_image(path)
        except (ValueError, OSError) as exc:
            self.status.set("Không đọc được ảnh")
            self.status_label.configure(foreground=ERROR)
            self.source_label.configure(text=str(exc), foreground=ERROR)
            self.input_canvas.create_text(153, 102, text="Chọn lại tệp JPG / PNG hợp lệ", fill=ERROR,
                                           font=("Segoe UI", 10))
            return
        self.source_label.configure(text=f"{Path(path).name}\n{self.image.width} × {self.image.height} pixel",
                                    foreground=MUTED)
        self.status_label.configure(foreground=MUTED)
        self.status.set("Ảnh đã sẵn sàng")
        thumb = ImageOps.contain(self.image, (306, 205), Image.Resampling.LANCZOS)
        self.photos["input"] = ImageTk.PhotoImage(thumb, master=self)
        self.input_canvas.create_image(153, 102, image=self.photos["input"], anchor="center")
        self.show_preprocessed(self.image.resize((96, 96), Image.Resampling.LANCZOS))
        self.classify_button.configure(state="normal")

    def show_preprocessed(self, image):
        self.photos["preprocessed"] = ImageTk.PhotoImage(image, master=self)
        self.preprocess_canvas.delete("all")
        self.preprocess_canvas.create_image(0, 0, image=self.photos["preprocessed"], anchor="nw")

    def _controls(self, busy):
        self.busy = busy
        self.open_button.configure(state="disabled" if busy else "normal")
        self.sample_box.configure(state="disabled" if busy else "readonly")
        self.classify_button.configure(state="disabled" if busy or self.image is None else "normal")
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def classify(self):
        """Khóa thao tác chọn ảnh, rồi giao phần suy luận cho luồng nền."""
        if self.busy or self.image is None:
            return
        self._clear_result()
        self._controls(True)
        self.status_label.configure(foreground=MUTED)
        self.status.set("Đang xử lý ảnh…" if self.engine else "Đang nạp mô hình…")
        image = self.image.copy()
        threading.Thread(target=_predict_in_background,
                         args=(self.project, self.predictor_factory, self.engine, image, self.events),
                         daemon=True).start()

    def _poll(self):
        """Tk gọi định kỳ hàm này để nhận kết quả mà không chặn cửa sổ."""
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self._controls(False)
            if self.closing:
                self.destroy()
                return
            if kind == "result":
                self.engine, result = value
                self._show_result(result)
            else:
                self.engine = None
                self.status.set("Chưa xử lý được ảnh · Có thể thử lại")
                self.status_label.configure(foreground=ERROR)
                self.timing_label.configure(text="Chưa có kết quả.")
                self.config_label.configure(text=value, foreground=ERROR)
        self.after_id = self.after(60, self._poll)

    def _show_result(self, result):
        self.result = result
        self.result_label.configure(text=f"Kết quả: {result['class_name_vi']}")
        self.timing_label.configure(text=f"Thời gian suy luận: {result['elapsed_ms']:.0f} ms · Không gồm nạp mô hình / đọc tệp")
        config = self.engine.bundle["config"]
        feature = FEATURE_NAMES.get(result["feature"], result["feature"])
        metric = METRIC_NAMES.get(config["metric"], config["metric"])
        voting = VOTING_NAMES.get(config["weights"], config["weights"])
        self.config_label.configure(foreground=MUTED, text=(f"Đặc trưng: {feature}\n"
                                    f"Số láng giềng k = {config['k']} · Khoảng cách: {metric} · Bỏ phiếu: {voting}"))
        if result["segmentation_fallback"]:
            self.config_label.configure(text=self.config_label.cget("text") + "\nPhân đoạn chưa ổn định; đã dùng ảnh gốc.")
        if "segmented" in result["feature"]:
            from .features import canonical, segment
            pixels, _, _ = segment(canonical(self.image))
            self.show_preprocessed(Image.fromarray(pixels))
        self._draw_votes()
        for col, neighbor in enumerate(result["neighbors"]):
            i = neighbor["reference_index"]
            image = Image.fromarray(self.engine.reference_images[i]).resize((90, 90), Image.Resampling.LANCZOS)
            self.photos[f"neighbor{col}"] = ImageTk.PhotoImage(image, master=self)
            photo, label = self.neighbor_widgets[col]
            photo.configure(image=self.photos[f"neighbor{col}"])
            knn = self.engine.pipeline[-1]
            name = VI[int(knn.classes_[knn._y[i]])]
            label.configure(text=f"{name}\nKhoảng cách {neighbor['distance']:.3f}\nMã: {neighbor['id']}")
        self.status.set("Đã phân loại · Chọn ảnh khác để tiếp tục")

    def _draw_votes(self):
        self.chart.delete("all")
        width = max(250, self.chart.winfo_width())
        bar_width = width - 142
        scores = self.result["vote_scores"] if self.result else [0] * 6
        for i, (name, score) in enumerate(zip(VI, scores)):
            y = i * 27 + 4
            self.chart.create_text(0, y + 10, anchor="w", text=name, fill=INK, font=("Segoe UI", 10))
            self.chart.create_rectangle(64, y, 64 + bar_width, y + 20, fill=PALE, outline="")
            if score:
                self.chart.create_rectangle(64, y, 64 + bar_width * score, y + 20, fill=GREEN, outline="")
            self.chart.create_text(width - 2, y + 10, anchor="e", text=f"{score:.3f}" if self.result else "—",
                                   fill=MUTED, font=("Segoe UI", 10))

    def _wrap_result(self, width):
        """Cho câu tiếng Việt tự xuống dòng theo độ rộng thực tế của khung."""
        for label in (self.timing_label, self.config_label):
            label.configure(wraplength=max(250, width - 8))

    def close(self):
        if self.busy:
            self.closing = True
            self.status.set("Đang đóng sau khi xử lý xong…")
        else:
            self.after_cancel(self.after_id)
            self.destroy()


def main():
    (ROOT / "results").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "results/desktop.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    if __import__("sys").platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AnimalKNN.Desktop.1")
    app = DesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
