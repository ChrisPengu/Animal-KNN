from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ["bird", "cat", "deer", "dog", "horse", "monkey"]
VI = ["Chim", "Mèo", "Hươu", "Chó", "Ngựa", "Khỉ"]
STL_LABELS = [2, 4, 5, 6, 7, 8]  # Official binary labels are one-based.


def paths(root: Path | str = ROOT) -> dict[str, Path]:
    root = Path(root).resolve()
    return {key: root / key for key in ["data", "models", "results", "reports"]}


def save_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=_json), encoding="utf-8")


def require_unopened_test(root):
    if (Path(root) / "results/test_access_receipt.json").exists():
        raise RuntimeError("Study is frozen after test access. Use a fresh project copy for new tuning or selection.")


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_num_threads(min(4, os.cpu_count() or 1))


def read_image(source) -> Image.Image:
    """Đọc ảnh, sửa hướng EXIF, ghép nền trắng cho alpha và trả ảnh RGB."""
    try:
        image = source.copy() if isinstance(source, Image.Image) else Image.open(source)
        image.load()
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, rgba)
        return image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("Không đọc được ảnh. Hãy chọn tệp JPG/PNG hợp lệ.") from exc
