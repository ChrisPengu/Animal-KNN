"""Full study. Validation chooses all configurations before test is opened."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STUDY_ROOT = ROOT


def run(*args):
    subprocess.run([sys.executable, "-u", "-m", "animal_knn", "--root", str(STUDY_ROOT), *args], cwd=ROOT, check=True)


def main():
    global STUDY_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--skip-finetune", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT, help="Use a fresh output directory to reproduce a frozen study")
    parser.add_argument("--ranged", action="store_true")
    args = parser.parse_args()
    STUDY_ROOT = args.root.resolve()
    if (STUDY_ROOT / "results/test_access_receipt.json").exists():
        raise SystemExit("This study is frozen after test access. Use a fresh project copy for a new study.")
    if not (STUDY_ROOT / "data/processed/manifest.csv").exists():
        run("prepare", *(["--download"] if args.download else []), *(["--ranged"] if args.ranged else []))
    run("audit")
    run("illustrations")
    for feature in ["hsv_hog", "hsv_hog_segmented", "hsv_hog_hu_segmented", "resnet18", "efficientnet_b0",
                    "resnet18_segmented", "efficientnet_b0_segmented"]:
        if not (STUDY_ROOT / "results/tuning" / f"{feature}_best.json").exists():
            run("extract", "--feature", feature)
            run("train-knn", "--feature", feature)
    if not args.skip_finetune:
        if not list((STUDY_ROOT / "results/tuning").glob("*_finetuned_best.json")):
            run("finetune")
            ft = next((STUDY_ROOT / "data/features").glob("*_finetuned.npz")).stem
            run("train-knn", "--feature", ft)
    run("select")
    run("evaluate", "--all-models")


if __name__ == "__main__":
    main()
