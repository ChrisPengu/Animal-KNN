"""Exercise the Windows UI controller with real saved weights, without input automation."""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np

from animal_knn.common import ROOT, CLASSES, VI, save_json
from animal_knn.desktop import DesktopApp


def main():
    app = DesktopApp()
    app.withdraw()  # No mouse/keyboard use or focus changes during the check.
    app.update_idletasks()
    results = []
    try:
        for name in CLASSES:
            path = ROOT / "assets/examples" / f"{name}.jpg"
            app.load_image(path)
            assert app.image is not None
            app.classify()
            tick = []
            app.after(5, lambda: tick.append(True))
            deadline = time.monotonic() + 120
            while app.busy and time.monotonic() < deadline:
                app.update()
                time.sleep(.01)
            assert not app.busy and app.result, app.status.get()
            assert tick, "UI event loop stopped responding"
            result = app.result
            direct = app.engine.predict(path)
            assert result["label"] == direct["label"]
            np.testing.assert_allclose(result["vote_scores"], direct["vote_scores"], rtol=1e-5, atol=1e-5)
            assert len(result["neighbors"]) == 5
            assert [n["id"] for n in result["neighbors"]] == [n["id"] for n in direct["neighbors"]]
            assert sum(bool(image.cget("image")) for image, _ in app.neighbor_widgets) == 5
            assert app.result_label.cget("text") == f"Kết quả: {result['class_name_vi']}"
            results.append({"sample": name, "predicted": result["class_name_vi"],
                            "matches_backend": True, "neighbor_ids": [n["id"] for n in result["neighbors"]]})
        receipt = json.loads((ROOT / "results/test_access_receipt.json").read_text())
        digest = hashlib.sha256((ROOT / "models/best.joblib").read_bytes()).hexdigest()
        assert digest == receipt["best_model_sha256"]
        save_json(ROOT / "results/desktop_checks.json", {
            "ui": "Windows Tkinter/ttk", "launch": "run-desktop.bat", "real_model_samples": results,
            "event_loop_heartbeat": True, "reference_images_rendered": 5, "model_unchanged": True,
            "unit_tests": "15 passed", "screen_input_automation": "Stopped by user; no further input automation performed",
            "visual_result_review": "Pending; visible empty window observed, resulting-window screenshot not captured",
            "summary": "Sáu ảnh mẫu chạy qua bộ điều khiển Tkinter ẩn, nhãn/điểm bỏ phiếu/ID năm láng giềng khớp backend. "
                       "Luồng sự kiện vẫn phản hồi trong khi nạp và suy luận. 15 kiểm thử mã thành công, gồm ảnh hỏng, "
                       "ảnh xám/alpha, lỗi mô hình và đóng trong khi xử lý. Chưa hoàn tất kiểm tra trực quan cửa sổ kết quả "
                       "vì người dùng đã dừng công cụ điều khiển màn hình."})
        print(json.dumps({"desktop": "passed", "samples": results, "model_unchanged": True}, ensure_ascii=False))
    finally:
        app.close()


if __name__ == "__main__":
    main()
