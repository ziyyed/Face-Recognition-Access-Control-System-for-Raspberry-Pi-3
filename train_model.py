"""
Train LBPH face recognizer for the Pi access-control project.

Reuses the dataset captured with capture_dataset.py and replaces the
previous "mask classifier" training step from the mask detection project.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

DEFAULT_DATASET_DIR = Path("dataset")
MODEL_PATH = Path("trainer.yml")
LABELS_PATH = Path("labels.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train LBPH face recognizer")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--labels-path", type=Path, default=LABELS_PATH)
    return parser.parse_args()


def load_dataset(dataset_dir: Path) -> Tuple[List[np.ndarray], List[int], Dict[int, str]]:
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory '{dataset_dir}' not found")

    faces: List[np.ndarray] = []
    labels: List[int] = []
    id_to_name: Dict[int, str] = {}

    for user_id, user_dir in enumerate(sorted(p for p in dataset_dir.iterdir() if p.is_dir())):
        id_to_name[user_id] = user_dir.name
        for img_path in sorted(user_dir.glob("*.jpg")):
            img_gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img_gray is None:
                print(f"[WARN] Could not read {img_path}")
                continue
            faces.append(img_gray)
            labels.append(user_id)

    if not faces:
        raise RuntimeError("No face images found. Capture dataset first.")

    return faces, labels, id_to_name


def main() -> int:
    args = parse_args()

    if not hasattr(cv2, "face"):
        raise ImportError(
            "cv2.face module not available. Install opencv-contrib-python on the Pi."
        )

    print("[INFO] Loading dataset...")
    faces, labels, id_to_name = load_dataset(args.dataset_dir)

    print(f"[INFO] Training on {len(faces)} images / {len(id_to_name)} users")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    recognizer.write(str(args.model_path))
    print(f"[INFO] Saved model to {args.model_path}")

    with args.labels_path.open("w", encoding="utf-8") as f:
        json.dump(id_to_name, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved label map to {args.labels_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


