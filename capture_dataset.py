"""
Capture face images for the Raspberry Pi access-control project.

This replaces the "mask / no mask" data collection step in the previous
project: we still use the Pi camera + Haar cascade detector, but now we
store cropped face samples per user for the recognition model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2

DEFAULT_DATASET_DIR = Path("dataset")
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
PASSWORDS_PATH = Path("passwords.json")
DEFAULT_PASSWORD = "1234"  # Default password for new users


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture face dataset on Raspberry Pi")
    parser.add_argument("--username", type=str, help="User name to enroll")
    parser.add_argument("--num-images", type=int, default=80, help="Number of face images to capture")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index (0=Pi cam / default USB)")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR, help="Dataset root directory")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_password_from_user(username: str) -> str:
    """Prompt user to enter their password."""
    import getpass
    while True:
        password = getpass.getpass(f"Enter password for '{username}': ")
        if not password:
            print("[WARN] Password cannot be empty. Please try again.")
            continue
        
        # Confirm password
        password_confirm = getpass.getpass(f"Confirm password for '{username}': ")
        if password != password_confirm:
            print("[WARN] Passwords do not match. Please try again.")
            continue
        
        return password


def update_passwords_file(username: str, password: Optional[str] = None) -> None:
    """Add or update password entry for a user in passwords.json."""
    # Load existing passwords
    if PASSWORDS_PATH.exists():
        try:
            with PASSWORDS_PATH.open("r", encoding="utf-8") as f:
                passwords = json.load(f)
        except (json.JSONDecodeError, IOError):
            passwords = {}
    else:
        passwords = {}
    
    # Add user if not exists
    if username not in passwords:
        if password is None:
            # Prompt user to set their password
            password = get_password_from_user(username)
        passwords[username] = password
        print(f"[INFO] Password set for user '{username}'")
    else:
        print(f"[INFO] User '{username}' already has a password (not changed)")
        if password is not None:
            # Allow updating password if provided
            response = input(f"Do you want to change password for '{username}'? (y/n): ").strip().lower()
            if response == 'y':
                new_password = get_password_from_user(username)
                passwords[username] = new_password
                print(f"[INFO] Password updated for user '{username}'")
    
    # Save passwords file
    try:
        with PASSWORDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(passwords, f, indent=2)
        print(f"[INFO] Passwords file updated: {PASSWORDS_PATH}")
    except IOError as e:
        print(f"[WARN] Failed to update passwords file: {e}")


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
            # Improved face detection parameters for better quality
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,      # Smaller scale = more detection passes (slower but better)
                minNeighbors=6,       # Higher = fewer false positives
                minSize=(100, 100),   # Minimum face size (filter small faces)
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            for (x, y, w, h) in faces:
                # Extract face region with padding
                padding = 10
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(gray.shape[1], x + w + padding)
                y2 = min(gray.shape[0], y + h + padding)
                roi_gray = gray[y1:y2, x1:x2]
                
                # Quality check: ensure minimum size
                if roi_gray.shape[0] < 100 or roi_gray.shape[1] < 100:
                    continue
                
                # Apply histogram equalization for better contrast
                roi_gray = cv2.equalizeHist(roi_gray)
                
                img_path = user_dir / f"img_{captured+1:03d}.jpg"
                cv2.imwrite(str(img_path), roi_gray)
                captured += 1
                draw_label(frame, f"{captured}/{args.num_images}", (x, y - 10))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                print(f"[INFO] Saved {img_path} ({roi_gray.shape[1]}x{roi_gray.shape[0]})")
                time.sleep(0.1)  # Small delay to avoid capturing too fast
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
    
    # Automatically update passwords.json - prompt user to set their password
    if captured > 0:
        print(f"\n[SETUP] Setting up password for '{username}'...")
        update_passwords_file(username)
        print(f"[INFO] User '{username}' is ready!")
        print(f"[INFO] You can change the password later by editing {PASSWORDS_PATH}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


