"""Dùng chung cho cửa sổ Windows và CLI: trích đặc trưng rồi phân loại bằng K-NN."""
from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from .common import CLASSES, ROOT, VI, read_image
from .features import Extractor, canonical, segment


class Predictor:
    """Nạp encoder, các phép biến đổi và ảnh train tham chiếu một lần để dùng lại."""
    def __init__(self, root=ROOT, model="best", device=None):
        self.root = Path(root)
        self.bundle = joblib.load(self.root / "models" / f"{model}.joblib")
        checkpoint = self.bundle.get("checkpoint")
        self.extractor = Extractor(self.bundle["feature"], checkpoint=self.root / checkpoint if checkpoint else None, device=device)
        self.pipeline = self.bundle["pipeline"]
        with np.load(self.root / "models/reference_images.npz") as refs:
            self.reference_images = refs["images"].copy()

    def predict(self, image):
        """Nhận ảnh/đường dẫn; trả nhãn Việt, điểm bỏ phiếu và năm láng giềng."""
        image = read_image(image)
        start = time.perf_counter()
        feature, bad = self.extractor.batch([canonical(image)])
        with threadpool_limits(limits=2):
            probabilities = self.pipeline.predict_proba(feature)[0]
            transformed = self.pipeline[:-1].transform(feature)
            distance, index = self.pipeline[-1].kneighbors(transformed, n_neighbors=min(5, len(self.bundle["reference_ids"])))
        scores = np.zeros(6)
        scores[self.pipeline[-1].classes_.astype(int)] = probabilities
        label = int(scores.argmax())
        return {"label": label, "class_name": CLASSES[label], "class_name_vi": VI[label],
                "vote_scores": scores.tolist(), "elapsed_ms": (time.perf_counter() - start) * 1000,
                "segmentation_fallback": bool(bad[0]), "feature": self.bundle["feature"],
                "neighbors": [{"id": self.bundle["reference_ids"][i], "distance": float(d), "reference_index": int(i)}
                              for i, d in zip(index[0], distance[0])]}
