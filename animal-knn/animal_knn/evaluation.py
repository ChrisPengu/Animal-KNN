from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from threadpoolctl import threadpool_limits

from .common import CLASSES, ROOT, VI, save_json
from .data import load
from .features import segment


def evaluate(root=ROOT, all_models=False):
    root = Path(root)
    selection = root / "models/selection.json"
    if not selection.exists():
        raise ValueError("Select and freeze the model before accessing test metrics")
    selected = json.loads(selection.read_text(encoding="utf-8"))["config"]["feature"]
    features = [selected]
    if all_models:
        features = [p.stem.replace("_best", "") for p in (root / "results/tuning").glob("*_best.json")]
    images, manifest = load(root)
    indices = np.flatnonzero(manifest.split == "test")
    results = root / "results"
    results.mkdir(exist_ok=True)
    save_json(results / "test_access_receipt.json", {"selected_feature_before_test": selected,
        "selection_sha256": hashlib.sha256(selection.read_bytes()).hexdigest(),
        "best_model_sha256": hashlib.sha256((root / "models/best.joblib").read_bytes()).hexdigest(),
        "selection_rule": "validation only", "timestamp_utc": pd.Timestamp.now(tz="UTC").isoformat()})
    summary = []
    with threadpool_limits(limits=4):
        for feature in features:
            bundle = joblib.load(root / "models" / f"{feature}.joblib")
            with np.load(root / "data/features" / f"{feature}.npz") as cache:
                x, y = cache["X"][indices], cache["y"][indices]
            start = time.perf_counter()
            probabilities = np.concatenate([bundle["pipeline"].predict_proba(x[i:i+128]) for i in range(0, len(x), 128)])
            elapsed = time.perf_counter() - start
            pred = bundle["pipeline"][-1].classes_[probabilities.argmax(axis=1)].astype(int)
            report = classification_report(y, pred, labels=range(6), target_names=CLASSES, zero_division=0, output_dict=True)
            cm = confusion_matrix(y, pred, labels=range(6))
            acc = float(accuracy_score(y, pred))
            f1 = float(f1_score(y, pred, labels=range(6), average="macro", zero_division=0))
            se = np.sqrt(acc * (1-acc) / len(y))
            row = {"feature": feature, "accuracy": acc, "macro_f1": f1, "n_test": len(y),
                   "retrieval_ms_per_image_batched": elapsed * 1000 / len(y),
                   "accuracy_normal_95ci": [max(0., float(acc-1.96*se)), min(1., float(acc+1.96*se))],
                   "selected_on_validation": feature == selected}
            summary.append(row)
            save_json(results / f"{feature}_test_metrics.json", {**row, "classification_report": report, "confusion_matrix": cm})
            data = manifest.iloc[indices][["sample_id", "label", "class_name", "source_index"]].copy()
            data["prediction"] = pred
            data["prediction_name"] = [CLASSES[p] for p in pred]
            data["vote_score"] = probabilities.max(axis=1)
            for c, name in enumerate(CLASSES):
                data["vote_" + name] = probabilities[:, c]
            data.to_csv(results / f"{feature}_test_predictions.csv", index=False)
            _confusion(cm, feature, results / f"{feature}_confusion.png")
            if feature == selected:
                _errors(images[indices], y, pred, probabilities.max(axis=1), results / "error_gallery.png")
            print(f"TEST {feature}: accuracy={acc:.4f}, macro-F1={f1:.4f}", flush=True)
    table = pd.DataFrame(summary)
    table.to_csv(results / "test_comparison.csv", index=False)
    return summary


def _confusion(cm, feature, path):
    fig, ax = plt.subplots(figsize=(8, 7))
    image = ax.imshow(cm / np.maximum(cm.sum(1, keepdims=True), 1), cmap="Greens", vmin=0, vmax=1)
    for i in range(6):
        for j in range(6):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i,j] / max(cm[i].sum(),1) > .55 else "#152e26")
    ax.set(xticks=range(6), yticks=range(6), xticklabels=VI, yticklabels=VI,
           xlabel="Dự đoán", ylabel="Nhãn dữ liệu", title=f"Ma trận nhầm lẫn · {feature}")
    fig.colorbar(image, ax=ax, label="Tỷ lệ trong lớp thật")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _errors(images, truth, pred, score, path):
    wrong = np.flatnonzero(truth != pred)
    chosen = []
    for c in range(6):
        subset = wrong[truth[wrong] == c]
        chosen.extend(subset[np.argsort(score[subset])[::-1]][:2].tolist())
    if not chosen:
        return
    fig, axes = plt.subplots(3, 4, figsize=(12, 10))
    for ax in axes.ravel():
        ax.axis("off")
    for ax, i in zip(axes.ravel(), chosen):
        ax.imshow(images[i])
        ax.set_title(f"{VI[truth[i]]} / dự đoán {VI[pred[i]]}\nĐiểm bỏ phiếu {score[i]:.2f}", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def illustrations(root=ROOT):
    root = Path(root)
    images, manifest = load(root)
    fig, axes = plt.subplots(6, 3, figsize=(8, 13))
    for c in range(6):
        i = manifest.index[(manifest.label == c) & (manifest.split == "train")][0]
        masked, mask, fallback = segment(images[i])
        for j, (picture, label) in enumerate([(images[i], VI[c]), (mask, "Mặt nạ"), (masked, "Ảnh tách nền" + (" (fallback)" if fallback else ""))]):
            axes[c,j].imshow(picture, cmap="gray" if j == 1 else None)
            axes[c,j].set_title(label, fontsize=11)
            axes[c,j].axis("off")
    fig.tight_layout()
    (root / "results").mkdir(exist_ok=True)
    fig.savefig(root / "results/segmentation_examples.png", dpi=130)
    plt.close(fig)
