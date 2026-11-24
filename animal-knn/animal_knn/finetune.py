from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from .common import ROOT, save_json, seed_everything, require_unopened_test
from .data import load
from .features import canonical, extract, segment


def finetune(root=ROOT, backbone=None, batch_size=16, head_epochs=5, fine_epochs=10):
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import models, transforms
    root = Path(root)
    require_unopened_test(root)
    seed_everything()
    torch.hub.set_dir(str(root / "data/raw/torch"))
    if backbone is None:
        candidates = []
        for name in ("resnet18", "efficientnet_b0"):
            p = root / "results/tuning" / f"{name}_best.json"
            if p.exists():
                candidates.append(json.loads(p.read_text(encoding="utf-8")))
        if not candidates:
            raise ValueError("Tune the frozen CNN backbones before fine-tuning")
        backbone = max(candidates, key=lambda r: (r["val_accuracy"], r["val_macro_f1"], -r["distance_ms_per_image"]))["feature"]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    images, manifest = load(root)
    train_idx = np.flatnonzero(manifest.split == "train")
    val_idx = np.flatnonzero(manifest.split == "val")
    mean, std = [.485, .456, .406], [.229, .224, .225]
    augmentation = transforms.Compose([transforms.RandomResizedCrop(224, scale=(.75, 1)), transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(.15, .15, .1, .03), transforms.ToTensor(), transforms.Normalize(mean, std)])
    if backbone == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, 6)
        head, block = model.fc, model.layer4
    elif backbone == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 6)
        head, block = model.classifier, model.features[-2:]
    else:
        raise ValueError(backbone)
    evaluation = weights.transforms()

    class Images(Dataset):
        def __init__(self, indices, transform):
            self.indices, self.transform = indices, transform
        def __len__(self):
            return len(self.indices)
        def __getitem__(self, idx):
            i = self.indices[idx]
            return self.transform(Image.fromarray(canonical(images[i]))), int(manifest.iloc[i].label)

    train_loader = DataLoader(Images(train_idx, augmentation), batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(Images(val_idx, evaluation), batch_size=batch_size, shuffle=False, num_workers=0)
    model.to(device)
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in head.parameters():
        parameter.requires_grad = True
    scaler = torch.amp.GradScaler("cuda", enabled=device == "cuda")
    criterion = nn.CrossEntropyLoss()
    history, best_loss, best_state = [], float("inf"), None
    for phase, epochs in [("head", head_epochs), ("last_block", fine_epochs)]:
        if phase == "last_block":
            for parameter in block.parameters():
                parameter.requires_grad = True
        params = [{"params": head.parameters(), "lr": 1e-3 if phase == "head" else 1e-4}]
        if phase == "last_block":
            params.append({"params": block.parameters(), "lr": 1e-4})
        optimizer = torch.optim.AdamW(params, weight_decay=1e-4)
        stale = 0
        for epoch in range(epochs):
            # Frozen blocks stay in eval mode so their BatchNorm statistics cannot drift.
            model.eval()
            head.train()
            if phase == "last_block":
                block.train()
            train_loss, count = 0., 0
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type=device, enabled=device == "cuda"):
                    loss = criterion(model(inputs), labels)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
                train_loss += float(loss.item()) * len(labels)
                count += len(labels)
            model.eval()
            val_loss, correct, total = 0., 0, 0
            with torch.inference_mode():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device), labels.to(device)
                    logits = model(inputs)
                    val_loss += float(criterion(logits, labels).item()) * len(labels)
                    correct += int((logits.argmax(1) == labels).sum())
                    total += len(labels)
            row = {"phase": phase, "epoch": epoch + 1, "train_loss": train_loss / count,
                   "val_loss": val_loss / total, "val_accuracy": correct / total}
            history.append(row)
            print(json.dumps(row), flush=True)
            if row["val_loss"] < best_loss - 1e-5:
                best_loss = row["val_loss"]
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                stale = 0
            else:
                stale += 1
            save_json(root / "results/finetune_history.json", {"backbone": backbone, "history": history, "seed": 42})
            if phase == "last_block" and stale >= 3:
                break
    model.load_state_dict(best_state)
    if backbone == "resnet18":
        model.fc = nn.Identity()
    else:
        model.classifier = nn.Identity()
    feature = backbone + "_finetuned"
    checkpoint = root / "models/backbones" / (feature + ".pt")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": {k: v.cpu() for k, v in model.state_dict().items()}}, checkpoint)
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    extract(root, feature, checkpoint=checkpoint, batch_size=batch_size)
    return feature
