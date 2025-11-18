"""
Face recognition access control for Proteus VSM simulation.

This version sends commands via serial to Proteus, which handles the
LCD and motor control in the simulation environment.

Usage:
    python recognize_and_control_proteus.py --proteus-port COM1

For real hardware, use recognize_and_control.py instead.
"""

from __future__ import annotations

import argparse
import atexit
import json
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import cv2
import serial

# ======================== Configuration =========================
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
MODEL_PATH = Path("trainer.yml")
LABELS_PATH = Path("labels.json")
PASSWORDS_PATH = Path("passwords.json")
CONFIDENCE_THRESHOLD = 70.0  # Lower == stricter
STABILITY_FRAMES = 3  # Require N consecutive predictions before acting
DOOR_OPEN_SECONDS = 5.0
UNKNOWN_COOLDOWN_SECONDS = 5.0
PASSWORD_TIMEOUT_SECONDS = 10.0  # Time to enter password
# =================================================================


@dataclass
class Prediction:
    label: int
    confidence: float


class ProteusFaceAccessController:
    """Face recognition controller that communicates with Proteus via serial."""
    
    def __init__(self, camera_index: int = 0, proteus_port: str = "COM1", baudrate: int = 115200):
        # Camera setup
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar cascade")
        
        # Face recognition
        if not hasattr(cv2, "face"):
            raise ImportError("cv2.face module missing. Install opencv-contrib-python.")
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}. Run train_model.py first.")
        self.recognizer.read(str(MODEL_PATH))
        self.labels: Dict[int, str] = self._load_labels(LABELS_PATH)
        
        # Load passwords
        self.passwords: Dict[str, str] = self._load_passwords(PASSWORDS_PATH)
        
        # Proteus serial connection
        try:
            self.serial_conn = serial.Serial(proteus_port, baudrate, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            print(f"[INFO] Connected to Proteus on {proteus_port}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Proteus on {proteus_port}: {e}")
        
        # Send initialization
        self._send_command("INIT:Systeme Pret")
        time.sleep(0.5)
        
        # Stability tracking
        self._streak_label: Optional[int] = None
        self._streak_count = 0
        self._last_unknown_time = 0.0
        self._last_recognized_user: Optional[str] = None
        
        # Password authentication state
        self._password_pending: Optional[str] = None  # Username waiting for password
        self._password_start_time: float = 0.0
        self._password_lock = threading.Lock()
        self._password_input_thread: Optional[threading.Thread] = None
        
    @staticmethod
    def _load_labels(path: Path) -> Dict[int, str]:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(k): v for k, v in data.items()}
    
    @staticmethod
    def _load_passwords(path: Path) -> Dict[str, str]:
        """Load passwords from JSON file."""
        if not path.exists():
            print(f"[WARN] Passwords file not found: {path}. Creating default file.")
            default_passwords = {"hassen": "1234", "zied": "5678"}
            with path.open("w", encoding="utf-8") as f:
                json.dump(default_passwords, f, indent=2)
            return default_passwords
        
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def _send_command(self, command: str) -> None:
        """Send command to Proteus via serial."""
        try:
            self.serial_conn.write(f"{command}\n".encode('utf-8'))
            self.serial_conn.flush()
        except Exception as e:
            print(f"[WARN] Failed to send command to Proteus: {e}")
    
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
                if username != self._last_recognized_user:
                    # Request password instead of immediately granting access
                    self._request_password(username)
                    self._last_recognized_user = username
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
                if user_label == -1:
                    self._handle_unknown()
                    self._last_recognized_user = None
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
            # Check password timeout
            with self._password_lock:
                if self._password_pending is not None:
                    elapsed = time.time() - self._password_start_time
                    if elapsed > PASSWORD_TIMEOUT_SECONDS:
                        self._password_pending = None
                        self._send_command("LCD:Systeme Pret|")
            self._last_recognized_user = None
        
        cv2.imshow("Access Control (Proteus)", frame)
    
    def _update_stability(self, label: int) -> None:
        if label == self._streak_label:
            self._streak_count += 1
        else:
            self._streak_label = label
            self._streak_count = 1
    
    def _reset_stability(self) -> None:
        self._streak_label = None
        self._streak_count = 0
    
    def _request_password(self, username: str) -> None:
        """Request password for recognized user."""
        with self._password_lock:
            if self._password_pending is not None:
                return  # Already waiting for password
            
            self._password_pending = username
            self._password_start_time = time.time()
            
            # Show password prompt on LCD
            self._send_command(f"LCD:Mot de passe|{username[:12]}")
            print(f"\n[PASSWORD] Enter password for {username} (or 'q' to cancel):")
            
            # Start password input thread
            if self._password_input_thread is None or not self._password_input_thread.is_alive():
                self._password_input_thread = threading.Thread(
                    target=self._password_input_handler,
                    daemon=True
                )
                self._password_input_thread.start()
    
    def _password_input_handler(self) -> None:
        """Handle password input in background thread."""
        while True:
            with self._password_lock:
                if self._password_pending is None:
                    time.sleep(0.1)
                    continue
                
                username = self._password_pending
                elapsed = time.time() - self._password_start_time
                
                # Check timeout
                if elapsed > PASSWORD_TIMEOUT_SECONDS:
                    print(f"[PASSWORD] Timeout for {username}")
                    self._send_command("LCD:Timeout|Acces refuse")
                    self._password_pending = None
                    time.sleep(2)
                    self._send_command("LCD:Systeme Pret|")
                    continue
            
            # Get password input (this blocks, but in separate thread)
            try:
                password = input().strip()
                
                with self._password_lock:
                    if self._password_pending != username:
                        continue  # User changed, ignore this input
                    
                    if password.lower() == 'q':
                        print(f"[PASSWORD] Cancelled for {username}")
                        self._send_command("LCD:Annule|")
                        self._password_pending = None
                        time.sleep(1)
                        self._send_command("LCD:Systeme Pret|")
                        continue
                    
                    # Verify password
                    if self._verify_password(username, password):
                        self._password_pending = None
                        self._grant_access(username)
                    else:
                        print(f"[PASSWORD] Incorrect password for {username}")
                        self._send_command("LCD:Mot de passe|Incorrect")
                        time.sleep(2)
                        # Reset to allow retry
                        self._password_start_time = time.time()
                        self._send_command(f"LCD:Mot de passe|{username[:12]}")
                        print(f"[PASSWORD] Enter password for {username} (or 'q' to cancel):")
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"[ERROR] Password input error: {e}")
                time.sleep(0.1)
    
    def _verify_password(self, username: str, password: str) -> bool:
        """Verify password for user."""
        stored_password = self.passwords.get(username)
        return stored_password is not None and stored_password == password
    
    def _grant_access(self, username: str) -> None:
        """Send access granted command to Proteus (after password verification)."""
        print(f"[ACCESS] Welcome {username} - Access granted!")
        # Send LCD command: "LCD:Bienvenue|username"
        self._send_command(f"LCD:Bienvenue|{username[:16]}")
        # Send door open command: "DOOR:OPEN:duration"
        self._send_command(f"DOOR:OPEN:{DOOR_OPEN_SECONDS:.1f}")
    
    def _handle_unknown(self) -> None:
        """Send access denied command to Proteus."""
        now = time.time()
        if now - self._last_unknown_time > UNKNOWN_COOLDOWN_SECONDS:
            print("[ACCESS] Unknown face - access denied")
            self._send_command("LCD:Acces refuse|")
            self._send_command("DOOR:CLOSE")
            self._last_unknown_time = now
    
    def cleanup(self) -> None:
        """Clean up all resources: camera, windows, serial connection, and threads."""
        print("[INFO] Cleaning up resources...")
        
        # Stop password input thread
        with self._password_lock:
            self._password_pending = None
        
        # Release camera
        if hasattr(self, 'cap') and self.cap.isOpened():
            print("[INFO] Releasing camera...")
            self.cap.release()
            time.sleep(0.1)  # Give camera time to release
        
        # Close all OpenCV windows
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Ensure windows are closed
        
        # Close serial connection
        if hasattr(self, 'serial_conn') and self.serial_conn.is_open:
            try:
                self._send_command("LCD:Arret|")
                time.sleep(0.2)
            except:
                pass
            finally:
                self.serial_conn.close()
                print("[INFO] Serial connection closed")
        
        print("[INFO] Cleanup complete")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Face recognition access control (Proteus)")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index")
    parser.add_argument("--proteus-port", type=str, default="COM1", 
                       help="Serial port for Proteus (e.g., COM1, COM3)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate (115200 recommended to prevent data loss)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    
    try:
        controller = ProteusFaceAccessController(
            camera_index=args.camera_index,
            proteus_port=args.proteus_port,
            baudrate=args.baudrate
        )
        # Register cleanup function to run on exit
        atexit.register(controller.cleanup)
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        return 1
    
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

