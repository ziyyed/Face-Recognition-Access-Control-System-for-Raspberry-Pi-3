"""
Real-time face recognition and access control on Raspberry Pi 3.

This script replaces the mask/not-mask inference loop from the previous
project. The camera + face detection pipeline is the same, but instead
of calling the mask classifier we call the LBPH face recognizer trained
with train_model.py, and drive the LCD + door motor accordingly.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import cv2

from door_control import DEFAULT_OPEN_DURATION, init_door_controller
from lcd_display import init_lcd, show_message

# ======================== Configuration =========================
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
MODEL_PATH = Path("trainer.yml")
LABELS_PATH = Path("labels.json")
CONFIDENCE_THRESHOLD = 70.0  # Lower == stricter; adjust per lighting/angle
STABILITY_FRAMES = 3  # Require N consecutive predictions before acting
DOOR_OPEN_SECONDS = DEFAULT_OPEN_DURATION
UNKNOWN_COOLDOWN_SECONDS = 5.0  # Avoid spamming LCD for unknown faces
# =================================================================


@dataclass
class Prediction:
    label: int
    confidence: float


class FaceAccessController:
    def __init__(self, camera_index: int = 0, mock_hardware: bool = False):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        self.face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar cascade")

        if not hasattr(cv2, "face"):
            raise ImportError("cv2.face module missing. Install opencv-contrib-python.")

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.read(str(MODEL_PATH))
        self.labels: Dict[int, str] = self._load_labels(LABELS_PATH)

        self.lcd = init_lcd(force_mock=mock_hardware)
        self.door = init_door_controller(force_mock=mock_hardware)

        self._streak_label: Optional[int] = None
        self._streak_count = 0
        self._last_unknown_time = 0.0

    @staticmethod
    def _load_labels(path: Path) -> Dict[int, str]:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(k): v for k, v in data.items()}

    def predict_face(self, gray_roi) -> Optional[Prediction]:
        label, confidence = self.recognizer.predict(gray_roi)
        return Prediction(label=label, confidence=confidence)

    def process_frame(self, frame) -> None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        recognized = False

        for (x, y, w, h) in faces:
            roi_gray = gray[y : y + h, x : x + w]
            prediction = self.predict_face(roi_gray)

            if prediction and prediction.confidence < CONFIDENCE_THRESHOLD:
                label = prediction.label
            else:
                label = -1

            self._update_stability(label)

            user_label = self._streak_label if self._streak_count >= STABILITY_FRAMES else None
            if user_label is not None and user_label != -1:
                username = self.labels.get(user_label, "Inconnu")
                self._grant_access(username)
                recognized = True
                cv2.putText(
                    frame,
                    f"{username} ({prediction.confidence:.1f})",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
            else:
                self._handle_unknown()
                cv2.putText(
                    frame,
                    "Inconnu",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if len(faces) == 0:
            self._reset_stability()

        cv2.imshow("Access Control", frame)

    def _update_stability(self, label: int) -> None:
        if label == self._streak_label:
            self._streak_count += 1
        else:
            self._streak_label = label
            self._streak_count = 1

    def _reset_stability(self) -> None:
        self._streak_label = None
        self._streak_count = 0

    def _grant_access(self, username: str) -> None:
        # This block replaces the old "mask detected" branch.
        print(f"[ACCESS] Welcome {username}")
        show_message(self.lcd, "Bienvenue", username[:16])
        self.door.open_door(DOOR_OPEN_SECONDS)

    def _handle_unknown(self) -> None:
        # Replaces the "no mask" branch; keep door closed.
        now = time.time()
        if now - self._last_unknown_time > UNKNOWN_COOLDOWN_SECONDS:
            print("[ACCESS] Unknown face - access denied")
            show_message(self.lcd, "Acces refuse")
            self.door.close_door()
            self._last_unknown_time = now

    def cleanup(self) -> None:
        print("[INFO] Cleaning up")
        self.cap.release()
        cv2.destroyAllWindows()
        if self.door:
            self.door.cleanup()
        if self.lcd:
            self.lcd.clear()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Face recognition access control")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--mock-hardware", action="store_true", help="Use console mocks for LCD/motor")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    controller = FaceAccessController(camera_index=args.camera_index, mock_hardware=args.mock_hardware)

    def _signal_handler(sig, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while True:
            ret, frame = controller.cap.read()
            if not ret:
                print("[WARN] Empty frame")
                time.sleep(0.1)
                continue
            controller.process_frame(frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
    finally:
        controller.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())


