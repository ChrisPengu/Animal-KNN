"""Collect a fixed, source-attributed Wikimedia holdout before seeing model results."""
from __future__ import annotations

import hashlib
import html
import io
import re
import time
import sys
from pathlib import Path

import pandas as pd
import requests
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    "bird": ["Passer domesticus", "Erithacus rubecula", "Columba livia", "Ara ararauna", "Haliaeetus"],
    "cat": ["Felis catus", "domestic cat", "tabby cat", "British Shorthair", "Siamese cat"],
    "deer": ["Cervus elaphus", "Dama dama", "Capreolus capreolus", "Cervus nippon", "Odocoileus"],
    "dog": ["domestic dog", "Labrador retriever", "German Shepherd", "Golden retriever", "Beagle"],
    "horse": ["Equus caballus", "domestic horse", "Arabian horse", "Icelandic horse", "Friesian horse"],
    "monkey": ["Macaca mulatta", "Macaca fascicularis", "Cebus capucinus", "Saimiri sciureus", "Chlorocebus"],
}
BAD = ["skull", "skeleton", "squelett", "squelette", "distribution", "map.", "drawing", "painting", "stamp", "statue", "logo", "engraving", "diagram", "fur coat", "mhnt", "eggs", "egg specimen"]


def clean(text):
    return html.unescape(re.sub("<[^>]+>", "", str(text or ""))).strip()


def main():
    folder = ROOT / "data/external"
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.csv"
    rows = pd.read_csv(manifest_path).to_dict("records") if manifest_path.exists() else []
    session = requests.Session()
    session.headers["User-Agent"] = "AnimalKNNResearch/1.0 (educational project; source attribution preserved)"
    api = "https://commons.wikimedia.org/w/api.php"
    known_titles = {r["title"] for r in rows}
    known_hashes = {r["sha256"] for r in rows}
    for label, (class_name, queries) in enumerate(QUERIES.items()):
        current = sum(r["class_name"] == class_name for r in rows)
        if current >= 10:
            continue
        for query in queries:
            current = sum(r["class_name"] == class_name for r in rows)
            if current >= 10:
                break
            params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                      "gsrsearch": f'intitle:"{query}" filetype:bitmap', "gsrlimit": 12,
                      "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 640}
            response = session.get(api, params=params, timeout=40)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {}).values()
            added = 0
            for page in sorted(pages, key=lambda p: p.get("index", 0)):
                title = page["title"]
                if title in known_titles or any(word in title.lower() for word in BAD):
                    continue
                info = page.get("imageinfo", [{}])[0]
                if not title.lower().endswith((".jpg", ".jpeg")) or min(info.get("width", 0), info.get("height", 0)) < 300:
                    continue
                meta = {k: clean(v.get("value", "")) for k,v in info.get("extmetadata", {}).items()}
                if any(word in (title + " " + meta.get("ImageDescription", "")).lower() for word in BAD):
                    continue
                license_name = meta.get("LicenseShortName", "")
                if not any(s in license_name.lower() for s in ["cc by", "cc0", "public domain"]):
                    continue
                url = info.get("thumburl", info.get("url"))
                r = session.get(url, timeout=40)
                if r.status_code == 429:
                    raise RuntimeError("Wikimedia rate limit: stop and resume later, preserving completed samples")
                if r.status_code != 200:
                    print(f"skip {r.status_code}: {title}", flush=True)
                    continue
                try:
                    image = Image.open(io.BytesIO(r.content)).convert("RGB")
                    image.load()
                except Exception:
                    continue
                digest = hashlib.sha256(image.tobytes()).hexdigest()
                if digest in known_hashes:
                    continue
                i = sum(row["class_name"] == class_name for row in rows)
                used = [int(p.stem.split("_")[-1]) for p in (folder / class_name).glob("*.jpg")]
                file_index = max(used, default=-1) + 1
                destination = folder / class_name / f"{class_name}_{file_index:02d}.jpg"
                destination.parent.mkdir(exist_ok=True)
                image.save(destination, quality=95)
                rows.append({"filename": str(destination.relative_to(ROOT)).replace("\\", "/"), "label": label,
                    "class_name": class_name, "title": title, "source_page": info.get("descriptionurl"),
                    "download_url": url, "author": meta.get("Artist", ""), "license": license_name,
                    "license_url": meta.get("LicenseUrl", ""), "date_original": meta.get("DateTimeOriginal", ""),
                    "description": meta.get("ImageDescription", ""), "sha256": digest,
                    "visual_review": "pending"})
                known_titles.add(title)
                known_hashes.add(digest)
                pd.DataFrame(rows).to_csv(manifest_path, index=False)
                print(f"{class_name} {i+1}/10: {title}", flush=True)
                added += 1
                time.sleep(2)
                if added >= 2 or i >= 9:
                    break
            time.sleep(2)
        print(f"Total {class_name}: {sum(r['class_name'] == class_name for r in rows)}", flush=True)


if __name__ == "__main__":
    main()
