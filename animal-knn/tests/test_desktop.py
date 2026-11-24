import threading
import time
import tkinter as tk
import gc
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from animal_knn.common import ROOT
from animal_knn.desktop import DesktopApp


def pump(app, predicate, timeout=4):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.update()
        time.sleep(.01)
    assert predicate(), "Desktop worker did not finish"
    app.update()


class FakeEngine:
    def __init__(self, gate=None):
        self.gate = gate
        self.bundle = {"config": {"k": 7, "metric": "euclidean", "weights": "distance"}}
        self.reference_images = np.zeros((5, 96, 96, 3), dtype=np.uint8)
        self.pipeline = [type("KNN", (), {"classes_": np.arange(6), "_y": np.ones(5, dtype=int)})()]

    def predict(self, image):
        if self.gate:
            assert self.gate.wait(3)
        return {"class_name_vi": "Mèo", "elapsed_ms": 12, "feature": "efficientnet_b0_finetuned",
                "segmentation_fallback": False, "vote_scores": [0, 1, 0, 0, 0, 0],
                "neighbors": [{"id": f"train_{i:05}", "distance": .1, "reference_index": i} for i in range(5)]}


@pytest.fixture(scope="module")
def desktop_window():
    window = DesktopApp(predictor_factory=lambda _root: FakeEngine())
    window.withdraw()
    window.update()
    yield window
    try:
        if window.winfo_exists():
            window.close()
    except tk.TclError:
        pass  # The close-during-work case already destroyed its Tcl interpreter.
    window.photos.clear()
    del window
    gc.collect()  # Tcl interpreters must be finalized on the GUI thread.


@pytest.fixture
def app(desktop_window):
    desktop_window.engine = None
    desktop_window.image = None
    desktop_window.predictor_factory = lambda _root: FakeEngine()
    desktop_window._clear_result()
    return desktop_window


def test_file_dialog_cancel_and_bad_image_clear_old_result(app, tmp_path):
    with patch("animal_knn.desktop.filedialog.askopenfilename", return_value=""):
        app.choose_file()
    assert app.image is None
    app.load_image(ROOT / "assets/examples/cat.jpg")
    app.classify()
    pump(app, lambda: not app.busy)
    assert app.result_label.cget("text") == "Kết quả: Mèo"
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not a png")
    with patch("animal_knn.desktop.filedialog.askopenfilename", return_value=str(bad)):
        app.choose_file()
    assert app.image is None and app.result is None
    assert "disabled" in app.classify_button.state()
    assert "JPG/PNG" in app.source_label.cget("text")
    assert all(label.cget("text") == "—" for _, label in app.neighbor_widgets)


def test_worker_keeps_event_loop_live_and_locks_source(app):
    gate = threading.Event()
    app.engine = FakeEngine(gate)
    app.load_image(ROOT / "assets/examples/cat.jpg")
    original = app.image
    app.classify()
    heartbeat = []
    app.after(10, lambda: heartbeat.append(True))
    pump(app, lambda: bool(heartbeat))
    assert app.busy and "disabled" in app.open_button.state()
    app.load_image(ROOT / "assets/examples/dog.jpg")
    assert app.image is original
    gate.set()
    pump(app, lambda: not app.busy)
    assert app.result["class_name_vi"] == "Mèo"
    assert sum(bool(image.cget("image")) for image, _ in app.neighbor_widgets) == 5
    assert "disabled" not in app.open_button.state()


def test_model_failure_can_retry(app):
    def missing(_root):
        raise FileNotFoundError("missing checkpoint")
    app.predictor_factory = missing
    app.load_image(ROOT / "assets/examples/cat.jpg")
    app.classify()
    pump(app, lambda: not app.busy)
    assert app.result is None
    assert "models" in app.config_label.cget("text")
    app.predictor_factory = lambda _root: FakeEngine()
    app.classify()
    pump(app, lambda: not app.busy)
    assert app.result["class_name_vi"] == "Mèo"


def test_grayscale_alpha_and_close_during_work(app, tmp_path):
    for mode, color in [("L", 100), ("RGBA", (10, 20, 30, 0))]:
        path = tmp_path / f"{mode}.png"
        Image.new(mode, (20, 30), color).save(path)
        app.load_image(path)
        assert app.image.mode == "RGB"
    assert app.image.getpixel((0, 0)) == (255, 255, 255)
    gate = threading.Event()
    app.engine = FakeEngine(gate)
    app.classify()
    app.close()
    assert app.closing and app.busy
    gate.set()
    pump(app, lambda: not app.busy)
