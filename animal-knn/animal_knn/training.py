"""Khảo sát K-NN/PCA trên train và validation; khóa mô hình trước khi mở test."""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer, StandardScaler
from threadpoolctl import threadpool_limits

from .common import CLASSES, ROOT, save_json, require_unopened_test
from .data import load

K_VALUES = [1, 3, 5, 7, 11, 15]
METRICS = ["euclidean", "manhattan", "cosine"]


def votes(distances, labels, k, weights, n_classes=6):
    """Cộng phiếu từng lớp; xử lý khoảng cách bằng 0 giống scikit-learn."""
    d, labels = distances[:, :k], labels[:, :k]
    if weights == "distance":
        zero = d == 0
        w = 1 / np.maximum(d, 1e-30)
        w[zero.any(axis=1)] = zero[zero.any(axis=1)].astype(float)
    else:
        w = np.ones_like(d)
    scores = np.stack([(w * (labels == c)).sum(axis=1) for c in range(n_classes)], axis=1)
    return scores / scores.sum(axis=1, keepdims=True)


def tune(root=ROOT, feature="resnet18", quick=False):
    """Chỉ fit biến đổi bằng train; validation chọn k/khoảng cách/bỏ phiếu/PCA."""
    root = Path(root)
    require_unopened_test(root)
    _, manifest = load(root)
    feature_file = root / "data/features" / f"{feature}.npz"
    meta = json.loads(feature_file.with_suffix(".json").read_text(encoding="utf-8"))
    with np.load(feature_file) as cache:
        if not np.array_equal(cache["ids"], manifest.sample_id.to_numpy()):
            raise ValueError("Feature cache sample IDs differ from manifest")
        x, y = cache["X"], cache["y"]
    tr = np.flatnonzero(manifest.split == "train")
    va = np.flatnonzero(manifest.split == "val")
    if not len(tr) or not len(va):
        raise ValueError("Train/validation split is empty")
    dimensions = [None] if quick else [None, 128, 256]
    candidates = []
    best, best_key = None, None
    with threadpool_limits(limits=4):
        for dim in dimensions:
            if dim is not None and dim >= min(len(tr), x.shape[1]):
                continue
            transforms = []
            if feature.startswith("hsv"):
                transforms.append(("scale", StandardScaler()))
            if dim:
                transforms.append(("pca", PCA(dim, svd_solver="randomized", random_state=42)))
            transforms.append(("normalize", Normalizer()))
            prep = Pipeline(transforms)
            a = prep.fit_transform(x[tr])
            b = prep.transform(x[va])
            for metric in METRICS:
                nn = NearestNeighbors(n_neighbors=min(15, len(tr)), metric=metric, algorithm="brute", n_jobs=2).fit(a)
                start = time.perf_counter()
                distances, indices = nn.kneighbors(b)
                per_image = (time.perf_counter() - start) / len(va)
                labels = y[tr][indices]
                for k in K_VALUES:
                    if k > len(tr):
                        continue
                    for weights in ("uniform", "distance"):
                        pred = votes(distances, labels, k, weights).argmax(axis=1)
                        acc = float(accuracy_score(y[va], pred))
                        f1 = float(f1_score(y[va], pred, labels=range(6), average="macro", zero_division=0))
                        row = {"feature": feature, "pca": dim or 0, "k": k, "metric": metric, "weights": weights,
                               "val_accuracy": acc, "val_macro_f1": f1, "distance_ms_per_image": per_image * 1000}
                        candidates.append(row)
                        key = (acc, f1, -per_image)
                        if best_key is None or key > best_key:
                            classifier = KNeighborsClassifier(k, weights=weights, metric=metric, algorithm="brute", n_jobs=2).fit(a, y[tr])
                            pipeline = Pipeline(prep.steps + [("knn", classifier)])
                            best, best_key = {"pipeline": pipeline, "config": row.copy(), "classes": CLASSES,
                                "feature": feature, "checkpoint": meta["checkpoint"], "feature_signature": meta["signature"],
                                "reference_ids": manifest.iloc[tr].sample_id.to_list(), "reference_indices": tr,
                                "train_sha256": manifest.iloc[tr].sha256.to_list(), "seed": 42,
                                "protocol": f"{len(tr)} train / {len(va)} validation; curated six-class transfer learning"}, key
                print(f"Tuned {feature}: PCA={dim}, metric={metric}, best val={best_key[0]:.4f}", flush=True)
    models = root / "models"
    models.mkdir(exist_ok=True)
    out = root / "results/tuning"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(candidates).to_csv(out / f"{feature}.csv", index=False)
    joblib.dump(best, models / f"{feature}.joblib", compress=3)
    save_json(out / f"{feature}_best.json", best["config"])
    return best["config"]


def select(root=ROOT):
    root = Path(root)
    require_unopened_test(root)
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in (root / "results/tuning").glob("*_best.json")]
    if not rows:
        raise ValueError("No tuned models. Run train-knn first.")
    table = pd.DataFrame(rows).sort_values(["val_accuracy", "val_macro_f1", "distance_ms_per_image"], ascending=[False, False, True])
    table.to_csv(root / "results/validation_comparison.csv", index=False)
    best = table.iloc[0].to_dict()
    import shutil
    shutil.copyfile(root / "models" / f"{best['feature']}.joblib", root / "models/best.joblib")
    bundle = joblib.load(root / "models/best.joblib")
    images, _ = load(root)
    np.savez_compressed(root / "models/reference_images.npz", images=images[bundle["reference_indices"]])
    save_json(root / "models/selection.json", {"selected_by": ["validation accuracy", "validation macro-F1", "retrieval time"],
        "test_used_for_selection": False, "config": best})
    print(table.to_string(index=False), flush=True)
    return best
