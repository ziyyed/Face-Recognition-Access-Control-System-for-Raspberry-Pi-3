"""
Capture face images for the Raspberry Pi access-control project.

This replaces the "mask / no mask" data collection step in the previous
project: we still use the Pi camera + Haar cascade detector, but now we
store cropped face samples per user for the recognition model.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Tuple

import cv2

DEFAULT_DATASET_DIR = Path("dataset")
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture face dataset on Raspberry Pi")
    parser.add_argument("--username", type=str, help="User name to enroll")
    parser.add_argument("--num-images", type=int, default=80, help="Number of face images to capture")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index (0=Pi cam / default USB)")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR, help="Dataset root directory")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def draw_label(frame, text: str, origin: Tuple[int, int]) -> None:
    cv2.putText(
        frame,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )


def main() -> int:
    args = parse_args()
    username = args.username or input("Nom d'utilisateur: ").strip()
    if not username:
        print("Username is required.")
        return 1

    user_dir = args.dataset_dir / username
    ensure_dir(user_dir)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar cascade")

    # Try DirectShow backend on Windows for better camera compatibility
    import sys
    if sys.platform == 'win32':
        cap = cv2.VideoCapture(args.camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    captured = 0
    print(f"[INFO] Capturing {args.num_images} images for {username}. Press 'q' to abort.")

    try:
        while captured < args.num_images:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Empty frame, retrying...")
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

            for (x, y, w, h) in faces:
                roi_gray = gray[y : y + h, x : x + w]
                img_path = user_dir / f"img_{captured+1:03d}.jpg"
                cv2.imwrite(str(img_path), roi_gray)
                captured += 1
                draw_label(frame, f"{captured}/{args.num_images}", (x, y - 10))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                print(f"[INFO] Saved {img_path}")
                break

            cv2.imshow("Capture Dataset (press q to exit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"[DONE] Collected {captured} images for {username}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


