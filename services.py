"""
Service Layer for Face Recognition Access Control System.

This module provides service classes that handle camera operations,
model training, and access control logic. Designed to be called from
Flask views while maintaining thread safety.
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Generator
import cv2
import numpy as np

# Setup logging
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_DATASET_DIR = Path("dataset")
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
MODEL_PATH = Path("trainer.yml")
LABELS_PATH = Path("labels.json")
NUM_IMAGES_TO_CAPTURE = 50

# Thread lock for camera operations
_camera_lock = threading.Lock()


class FaceCaptureService:
    """Service for capturing face images from camera."""
    
    def __init__(self, camera_index: int = 0, dataset_dir: Path = DEFAULT_DATASET_DIR):
        self.camera_index = camera_index
        self.dataset_dir = dataset_dir
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self._camera = None
        self._face_cascade = None
    
    def _init_camera(self) -> bool:
        """Initialize camera with thread safety."""
        with _camera_lock:
            if self._camera is None or not self._camera.isOpened():
                # Try DirectShow on Windows for better compatibility
                if sys.platform == 'win32':
                    self._camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                else:
                    self._camera = cv2.VideoCapture(self.camera_index)
                
                if not self._camera.isOpened():
                    return False
            return True
    
    def _release_camera(self) -> None:
        """Release camera resources."""
        with _camera_lock:
            if self._camera is not None:
                self._camera.release()
                self._camera = None
                cv2.destroyAllWindows()
    
    def _init_cascade(self) -> bool:
        """Initialize face cascade classifier."""
        if self._face_cascade is None:
            self._face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
            if self._face_cascade.empty():
                return False
        return True
    
    def capture_faces(self, user_id: int, num_images: int = NUM_IMAGES_TO_CAPTURE) -> Dict[str, any]:
        """
        Capture face images for a user.
        
        Args:
            user_id: Employee ID from database
            num_images: Number of images to capture (default: 50)
        
        Returns:
            Dict with 'success', 'captured', 'message'
        """
        try:
            # Initialize components
            if not self._init_cascade():
                return {'success': False, 'captured': 0, 'message': 'Failed to load face cascade'}
            
            if not self._init_camera():
                return {'success': False, 'captured': 0, 'message': 'Cannot open camera'}
            
            # Create user directory
            user_dir = self.dataset_dir / f"User.{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            
            captured = 0
            start_time = time.time()
            
            logger.info(f"Starting face capture for User.{user_id}")
            
            # Capture loop
            while captured < num_images:
                ret, frame = self._camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces with improved parameters
                faces = self._face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=6,
                    minSize=(100, 100),
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
                    
                    # Quality check
                    if roi_gray.shape[0] < 100 or roi_gray.shape[1] < 100:
                        continue
                    
                    # Apply histogram equalization
                    roi_gray = cv2.equalizeHist(roi_gray)
                    
                    # Save image
                    img_path = user_dir / f"User.{user_id}.{captured+1}.jpg"
                    cv2.imwrite(str(img_path), roi_gray)
                    captured += 1
                    
                    logger.debug(f"Captured image {captured}/{num_images}")
                    time.sleep(0.1)  # Small delay
                    break
            
            elapsed = time.time() - start_time
            
            return {
                'success': True,
                'captured': captured,
                'message': f'Captured {captured} images in {elapsed:.1f}s',
                'path': str(user_dir)
            }
            
        except Exception as e:
            logger.error(f"Error capturing faces: {str(e)}")
            return {'success': False, 'captured': 0, 'message': f'Error: {str(e)}'}
        finally:
            self._release_camera()
    
    def capture_faces_with_progress(self, user_id: int, num_images: int = NUM_IMAGES_TO_CAPTURE) -> Generator[Dict, None, Dict]:
        """
        Capture faces with progress updates (for future WebSocket/SSE implementation).
        
        Yields progress updates, then returns final result.
        """
        # For now, just call capture_faces and yield final result
        result = self.capture_faces(user_id, num_images)
        yield result
        return result


class ModelTrainerService:
    """Service for training the face recognition model."""
    
    def __init__(self, dataset_dir: Path = DEFAULT_DATASET_DIR, 
                 model_path: Path = MODEL_PATH,
                 labels_path: Path = LABELS_PATH):
        self.dataset_dir = dataset_dir
        self.model_path = model_path
        self.labels_path = labels_path
    
    def train_recognizer(self) -> Dict[str, any]:
        """
        Train the LBPH face recognizer on all images in dataset.
        
        Returns:
            Dict with 'success', 'message', 'users_trained', 'images_trained'
        """
        try:
            if not hasattr(cv2, "face"):
                return {
                    'success': False,
                    'message': 'cv2.face module not available. Install opencv-contrib-python.',
                    'users_trained': 0,
                    'images_trained': 0
                }
            
            if not self.dataset_dir.exists():
                return {
                    'success': False,
                    'message': f'Dataset directory not found: {self.dataset_dir}',
                    'users_trained': 0,
                    'images_trained': 0
                }
            
            logger.info("Loading dataset for training...")
            
            faces: List[np.ndarray] = []
            labels: List[int] = []
            id_to_name: Dict[int, str] = {}
            
            # Load all images from dataset
            user_dirs = sorted([p for p in self.dataset_dir.iterdir() if p.is_dir()])
            
            if not user_dirs:
                return {
                    'success': False,
                    'message': 'No user directories found in dataset',
                    'users_trained': 0,
                    'images_trained': 0
                }
            
            for user_dir in user_dirs:
                # Extract user_id from directory name (User.{id})
                try:
                    user_id = int(user_dir.name.split('.')[1])
                except (IndexError, ValueError):
                    logger.warning(f"Invalid user directory name: {user_dir.name}")
                    continue
                
                # Load all images for this user
                image_count = 0
                for img_path in sorted(user_dir.glob("*.jpg")):
                    img_gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                    if img_gray is None:
                        logger.warning(f"Could not read {img_path}")
                        continue
                    faces.append(img_gray)
                    labels.append(user_id)
                    image_count += 1
                
                if image_count > 0:
                    # Query database to get actual employee name
                    try:
                        from models import Employee, db
                        from flask import has_app_context, current_app
                        
                        # Try to get employee name from database if in Flask app context
                        if has_app_context():
                            employee = Employee.query.filter_by(id=user_id).first()
                            if employee:
                                id_to_name[user_id] = employee.name
                            else:
                                # Fallback to directory name if employee not found
                                logger.warning(f"Employee with id {user_id} not found in database, using directory name")
                                id_to_name[user_id] = user_dir.name
                        else:
                            # Not in Flask context (e.g., called from command line), use directory name
                            logger.warning(f"Not in Flask app context, using directory name for user_id {user_id}")
                            id_to_name[user_id] = user_dir.name
                    except Exception as e:
                        # Fallback to directory name if database query fails
                        logger.warning(f"Could not query employee name for id {user_id}: {e}. Using directory name.")
                        id_to_name[user_id] = user_dir.name
            
            if not faces:
                return {
                    'success': False,
                    'message': 'No face images found in dataset',
                    'users_trained': 0,
                    'images_trained': 0
                }
            
            logger.info(f"Training on {len(faces)} images from {len(id_to_name)} users")
            
            # Train recognizer
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(faces, np.array(labels))
            
            # Save model
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            recognizer.write(str(self.model_path))
            
            # Save labels (will be updated with actual names from database)
            with self.labels_path.open("w", encoding="utf-8") as f:
                json.dump(id_to_name, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': f'Model trained successfully on {len(faces)} images',
                'users_trained': len(id_to_name),
                'images_trained': len(faces),
                'model_path': str(self.model_path)
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return {
                'success': False,
                'message': f'Training error: {str(e)}',
                'users_trained': 0,
                'images_trained': 0
            }
    
    def model_exists(self) -> bool:
        """Check if trained model file exists."""
        return self.model_path.exists() and self.model_path.stat().st_size > 0


class AccessControlService:
    """Service for verifying access based on time and day rules."""
    
    def __init__(self):
        pass
    
    def verify_access(self, face_id: int) -> Dict[str, any]:
        """
        Verify if an employee with given face_id has access at current time.
        
        Args:
            face_id: The face_id from recognition system (maps to employee.id)
        
        Returns:
            Dict with 'granted', 'employee_name', 'reason'
        """
        from models import Employee, AccessRule
        
        try:
            # Find employee by face_id (assuming face_id maps to employee.id)
            # Note: In your system, face_id might be different from employee.id
            # Adjust this mapping based on your actual implementation
            employee = Employee.query.filter_by(id=face_id).first()
            
            if not employee:
                return {
                    'granted': False,
                    'employee_name': None,
                    'reason': 'Employee not found'
                }
            
            # Get current time and day
            now = datetime.now()
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            current_time = now.time()
            
            # Find active access rules for this employee and day
            rules = AccessRule.query.filter_by(
                employee_id=employee.id,
                day_of_week=current_day
            ).all()
            
            if not rules:
                return {
                    'granted': False,
                    'employee_name': employee.name,
                    'reason': 'No access rule defined for this day'
                }
            
            # Check if current time is within any rule's time window
            for rule in rules:
                if rule.start_time <= current_time <= rule.end_time:
                    return {
                        'granted': True,
                        'employee_name': employee.name,
                        'reason': None
                    }
            
            # Time is outside all rules
            return {
                'granted': False,
                'employee_name': employee.name,
                'reason': 'Outside scheduled access hours'
            }
            
        except Exception as e:
            logger.error(f"Error verifying access: {str(e)}")
            return {
                'granted': False,
                'employee_name': None,
                'reason': f'System error: {str(e)}'
            }

