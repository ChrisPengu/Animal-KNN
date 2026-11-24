from __future__ import annotations

import hashlib
import json
import inspect
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from skimage.feature import hog

from .common import ROOT, save_json
from .data import load

FEATURES = ["hsv_hog", "hsv_hog_segmented", "hsv_hog_hu_segmented", "resnet18", "efficientnet_b0",
            "resnet18_segmented", "efficientnet_b0_segmented"]


def canonical(image):
    if not isinstance(image, Image.Image):
        image = Image.fromarray(np.asarray(image, dtype=np.uint8))
    return np.asarray(image.convert("RGB").resize((96, 96), Image.Resampling.LANCZOS)).copy()


def segment(pixels):
    pixels = canonical(pixels)
    mask = np.zeros(pixels.shape[:2], np.uint8)
    try:
        cv2.setRNGSeed(42)
        cv2.grabCut(cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR), mask, (3, 3, 90, 90),
                    np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64), 5, cv2.GC_INIT_WITH_RECT)
        binary = np.isin(mask, [cv2.GC_FGD, cv2.GC_PR_FGD]).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        fraction = float(binary.mean())
        if not .05 <= fraction <= .95:
            return pixels, np.ones_like(binary), True
        output = pixels.copy()
        output[binary == 0] = 127
        return output, binary, False
    except cv2.error:
        return pixels, np.ones(mask.shape, np.uint8), True


def handcrafted(pixels, segmented=False, hu=False, precomputed=None):
    image = canonical(pixels)
    failed = False
    mask = np.ones((96, 96), np.uint8)
    if segmented:
        image, mask, failed = precomputed if precomputed is not None else segment(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], mask, [8, 8, 8], [0, 180, 0, 256, 0, 256]).ravel()
    hist /= max(float(hist.sum()), 1)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gradients = hog(gray, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2),
                    block_norm="L2-Hys", transform_sqrt=True)
    parts = [hist, gradients]
    if hu:
        moments = cv2.HuMoments(cv2.moments(mask)).ravel()
        moments = -np.sign(moments) * np.log10(np.maximum(np.abs(moments), 1e-30))
        if failed:
            moments[:] = 0
        parts.append(moments)
    vector = np.concatenate(parts).astype(np.float32)
    if not np.isfinite(vector).all():
        raise ValueError("Non-finite handcrafted features")
    return vector, failed


def make_backbone(name, checkpoint=None, device="cpu", pretrained=True):
    import torch
    from torchvision import models
    torch.hub.set_dir(str(ROOT / "data/raw/torch"))
    name = name.replace("_segmented", "").replace("_finetuned", "")
    if name == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights if pretrained and checkpoint is None else None)
        model.fc = torch.nn.Identity()
    elif name == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights if pretrained and checkpoint is None else None)
        model.classifier = torch.nn.Identity()
    else:
        raise ValueError(f"Unsupported backbone: {name}")
    if checkpoint:
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        model.load_state_dict(state.get("state_dict", state))
    return model.to(device).eval(), weights.transforms()


class Extractor:
    def __init__(self, feature, checkpoint=None, device=None, pretrained=True):
        self.feature = feature
        self.checkpoint = checkpoint
        self.deep = not feature.startswith("hsv")
        if self.deep:
            import torch
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            self.model, self.transform = make_backbone(feature, checkpoint, self.device, pretrained)
        else:
            self.device = "cpu"

    def batch(self, images, precomputed=None):
        failed = []
        if not self.deep:
            results = [handcrafted(x, "segmented" in self.feature, "hu" in self.feature,
                                  precomputed=tuple(a[i] for a in precomputed) if precomputed is not None else None)
                       for i,x in enumerate(images)]
            return np.stack([r[0] for r in results]), np.array([r[1] for r in results])
        import torch
        prepared = []
        for i,image in enumerate(images):
            pixels = canonical(image)
            bad = False
            if "segmented" in self.feature:
                pixels, _, bad = tuple(a[i] for a in precomputed) if precomputed is not None else segment(pixels)
            prepared.append(self.transform(Image.fromarray(pixels)))
            failed.append(bad)
        batch = torch.stack(prepared).to(self.device)
        with torch.inference_mode():
            # FP32 extraction keeps CPU and GPU retrieval scores close.
            result = self.model(batch).float().cpu().numpy().astype(np.float32)
        if not np.isfinite(result).all():
            raise ValueError("Non-finite CNN features")
        return result, np.array(failed)


def segmentation_cache(root, images):
    folder = Path(root) / "data/processed"
    cache_path = folder / "segmentation.npz"
    signature = hashlib.sha256((inspect.getsource(canonical) + inspect.getsource(segment) +
                               (folder / "manifest.csv").read_text(encoding="utf-8")).encode()).hexdigest()
    metadata = folder / "segmentation.json"
    valid = cache_path.exists() and metadata.exists() and json.loads(metadata.read_text())["signature"] == signature
    if not valid:
        masks, masked, failed = [], [], []
        for i,pixels in enumerate(images):
            result, mask, bad = segment(pixels)
            masked.append(result)
            masks.append(mask)
            failed.append(bad)
            if i % 500 == 0:
                print(f"GrabCut cache: {i}/{len(images)}", flush=True)
        np.savez_compressed(cache_path, images=np.stack(masked), masks=np.stack(masks), failed=np.array(failed))
        save_json(metadata, {"signature": signature, "samples": len(images), "fallbacks": int(sum(failed))})
    with np.load(cache_path) as cached:
        if len(cached["images"]) != len(images):
            raise ValueError("Segmentation cache length differs from data; delete and rebuild cache")
        return cached["images"], cached["masks"], cached["failed"]


def extract(root=ROOT, feature="resnet18", checkpoint=None, batch_size=16):
    root = Path(root)
    images, manifest = load(root)
    folder = root / "data/features"
    folder.mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha256((manifest.to_csv(index=False) + feature).encode() + Path(__file__).read_bytes()).hexdigest()
    checkpoint = Path(checkpoint) if checkpoint else None
    if checkpoint:
        signature += hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    meta_path = folder / f"{feature}.json"
    array_path = folder / f"{feature}.npz"
    if meta_path.exists() and array_path.exists() and json.loads(meta_path.read_text(encoding="utf-8"))["signature"] == signature:
        print(f"Cached {feature}", flush=True)
        return array_path
    extractor = Extractor(feature, checkpoint=checkpoint)
    segmented = segmentation_cache(root, images) if "segmented" in feature else None
    vectors, failures = [], []
    for start in range(0, len(images), batch_size):
        batch, bad = extractor.batch(images[start:start + batch_size],
                                     tuple(a[start:start+batch_size] for a in segmented) if segmented is not None else None)
        vectors.append(batch)
        failures.extend(bad.tolist())
        if start % (batch_size * 25) == 0:
            print(f"{feature}: {start}/{len(images)} on {extractor.device}", flush=True)
    x = np.concatenate(vectors)
    np.savez_compressed(array_path, X=x, y=manifest.label.to_numpy(), ids=manifest.sample_id.to_numpy(dtype=str),
                        segmentation_failed=np.asarray(failures))
    if extractor.deep:
        checkpoint_out = root / "models/backbones" / (feature + ".pt")
        checkpoint_out.parent.mkdir(parents=True, exist_ok=True)
        import torch
        torch.save({"state_dict": {k: v.cpu() for k, v in extractor.model.state_dict().items()}}, checkpoint_out)
    else:
        checkpoint_out = None
    save_json(meta_path, {"feature": feature, "signature": signature, "shape": list(x.shape),
                         "checkpoint": str(checkpoint_out.relative_to(root)) if checkpoint_out else None,
                         "segmentation_failures": int(sum(failures)), "canonical_size": [96, 96],
                         "pretraining": "ImageNet-1K" if extractor.deep else None})
    print(f"Saved {feature}: {x.shape}, segmentation fallbacks={sum(failures)}", flush=True)
    return array_path
