# direction_controller.py - Pose and gesture-based directional control for locked person

import os
import time
import math
import urllib.request
from collections import deque
from typing import Optional, Tuple, Dict

import cv2
import numpy as np
import mediapipe as mp
from mediapipe import Image, ImageFormat
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import config

# Model URLs and paths
POSE_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
POSE_PATH = "pose_landmarker_lite.task"

HAND_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
HAND_PATH = "hand_landmarker.task"

GESTURE_URL = "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task"
GESTURE_PATH = "gesture_recognizer.task"

# Direction control configuration
GESTURE_TO_FB = {
    "Thumb_Up": "Forward",
    "Thumb_Down": "Backward", 
    "Open_Palm": "Pause",
}

# Control parameters
FB_HOLD_SECONDS = 0.8  # Hold last command briefly on dropouts
LR_THRESHOLD = 90.0    # Right elbow angle threshold for left/right
ANGLE_SMOOTH_N = 5     # Smoothing frames for elbow angle
PRINT_COOLDOWN = 0.25  # Minimum seconds between identical prints

def ensure_model(path: str, url: str):
    """Download model if it doesn't exist locally"""
    if os.path.exists(path):
        return
    print(f"[DIRECTION] Downloading {os.path.basename(path)}...")
    urllib.request.urlretrieve(url, path)
    print(f"[DIRECTION] Saved to {path}")

def to_px(xy, w, h):
    """Convert normalized coordinates to pixel coordinates"""
    return int(xy.x * w), int(xy.y * h)

def angle_3pts(a, b, c):
    """Calculate angle ABC in degrees"""
    ab = (a[0]-b[0], a[1]-b[1])
    cb = (c[0]-b[0], c[1]-b[1])
    dot = ab[0]*cb[0] + ab[1]*cb[1]
    nab = math.hypot(*ab)
    ncb = math.hypot(*cb)
    if nab == 0 or ncb == 0:
        return None
    cosang = max(-1.0, min(1.0, dot/(nab*ncb)))
    return math.degrees(math.acos(cosang))

class DirectionController:
    """
    Provides pose and gesture-based directional control for the locked person.
    Analyzes only the locked person's bounding box region for commands.
    """
    
    def __init__(self):
        """Initialize the direction controller with MediaPipe models"""
        self.initialize_models()
        
        # Direction control state
        self.last_fb = None
        self.last_lr = None
        self.last_print_time = 0.0
        self.last_fb_seen_time = 0.0
        
        # Right elbow angle smoothing
        self.right_angle_buf = deque(maxlen=ANGLE_SMOOTH_N)
        
        # Timestamp for MediaPipe VIDEO mode
        self.start_time = time.perf_counter()
        
        print("[DIRECTION] Direction controller initialized")
        print("[DIRECTION] Forward/Backward: Thumb_Up/Thumb_Down/Open_Palm")
        print("[DIRECTION] Left/Right: Right elbow angle (< 90° = Left, > 90° = Right)")
    
    def initialize_models(self):
        """Initialize MediaPipe models for pose and gesture detection"""
        # Download models if needed
        ensure_model(POSE_PATH, POSE_URL)
        ensure_model(HAND_PATH, HAND_URL)
        ensure_model(GESTURE_PATH, GESTURE_URL)
        
        # Pose landmarker (VIDEO mode)
        pose_base = mp_python.BaseOptions(model_asset_path=POSE_PATH)
        pose_opts = mp_vision.PoseLandmarkerOptions(
            base_options=pose_base,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose_detector = mp_vision.PoseLandmarker.create_from_options(pose_opts)
        
        # Hand landmarker (VIDEO mode)
        hand_base = mp_python.BaseOptions(model_asset_path=HAND_PATH)
        hand_opts = mp_vision.HandLandmarkerOptions(
            base_options=hand_base,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hand_detector = mp_vision.HandLandmarker.create_from_options(hand_opts)
        
        # Gesture recognizer (VIDEO mode) 
        gest_base = mp_python.BaseOptions(model_asset_path=GESTURE_PATH)
        gest_opts = mp_vision.GestureRecognizerOptions(
            base_options=gest_base,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=2
        )
        self.gesture_recognizer = mp_vision.GestureRecognizer.create_from_options(gest_opts)
    
    def analyze_locked_person(self, frame: np.ndarray, person_bbox) -> Optional[Dict]:
        """
        Analyze the locked person's pose and gestures for directional control.
        
        Args:
            frame: Full frame image
            person_bbox: Bounding box of the locked person [x1, y1, x2, y2]
            
        Returns:
            Dictionary with direction commands or None if no analysis possible
        """
        if person_bbox is None:
            return None
        
        # Convert bbox to integers
        x1, y1, x2, y2 = map(int, person_bbox[:4])
        
        # Crop person region with some padding
        h, w = frame.shape[:2]
        pad = 50  # Add padding around person
        crop_x1 = max(0, x1 - pad)
        crop_y1 = max(0, y1 - pad)
        crop_x2 = min(w, x2 + pad)
        crop_y2 = min(h, y2 + pad)
        
        person_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        
        if person_crop.size == 0:
            return None
        
        # Convert to RGB for MediaPipe
        rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
        mp_img = Image(image_format=ImageFormat.SRGB, data=rgb_crop)
        
        # Get timestamp for VIDEO mode
        current_time = time.perf_counter()
        ts_ms = int((current_time - self.start_time) * 1000)
        
        try:
            # Run MediaPipe analysis on cropped region
            pose_result = self.pose_detector.detect_for_video(mp_img, ts_ms)
            gesture_result = self.gesture_recognizer.recognize_for_video(mp_img, ts_ms)
            
            # Analyze pose for left/right control
            lr_command = self._analyze_pose_for_lr(pose_result, person_crop.shape)
            
            # Analyze gestures for forward/backward control  
            fb_command = self._analyze_gestures_for_fb(gesture_result, current_time)
            
            # Check for command changes and print
            self._handle_command_output(fb_command, lr_command, current_time)
            
            return {
                'forward_backward': fb_command,
                'left_right': lr_command,
                'crop_region': (crop_x1, crop_y1, crop_x2, crop_y2),
                'pose_landmarks': pose_result.pose_landmarks[0] if pose_result.pose_landmarks else None
            }
            
        except Exception as e:
            print(f"[DIRECTION] Analysis error: {e}")
            return None
    
    def _analyze_pose_for_lr(self, pose_result, crop_shape) -> Optional[str]:
        """Analyze pose landmarks for left/right control based on right elbow angle"""
        if not pose_result.pose_landmarks:
            return self.last_lr
        
        landmarks = pose_result.pose_landmarks[0]
        h, w = crop_shape[:2]
        
        try:
            # Right arm landmarks: shoulder(12) -> elbow(14) -> wrist(16)
            right_shoulder = to_px(landmarks[12], w, h)
            right_elbow = to_px(landmarks[14], w, h)
            right_wrist = to_px(landmarks[16], w, h)
            
            # Calculate right elbow angle
            elbow_angle = angle_3pts(right_shoulder, right_elbow, right_wrist)
            
            if elbow_angle is not None:
                # Smooth the angle
                self.right_angle_buf.append(elbow_angle)
                smoothed_angle = sum(self.right_angle_buf) / len(self.right_angle_buf)
                
                # Determine left/right based on threshold
                return "Right" if smoothed_angle > LR_THRESHOLD else "Left"
            
        except (IndexError, AttributeError):
            pass
        
        return self.last_lr
    
    def _analyze_gestures_for_fb(self, gesture_result, current_time) -> Optional[str]:
        """Analyze gestures for forward/backward/pause control"""
        if not gesture_result.gestures:
            # Hold last command briefly if no gesture detected
            if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
                return self.last_fb
            return None
        
        # Find best gesture across all hands
        best_gesture = None
        best_score = 0.0
        
        for hand_gestures in gesture_result.gestures:
            if not hand_gestures:
                continue
            
            for gesture in hand_gestures:
                if gesture.score > best_score:
                    best_score = gesture.score
                    best_gesture = gesture
        
        if best_gesture:
            gesture_name = best_gesture.category_name
            mapped_command = GESTURE_TO_FB.get(gesture_name)
            
            if mapped_command:
                self.last_fb_seen_time = current_time
                return mapped_command
        
        # Hold last command briefly
        if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
            return self.last_fb
        
        return None
    
    def _handle_command_output(self, fb_command: Optional[str], lr_command: Optional[str], current_time: float):
        """Handle updating GUI and minimal console output for direction commands"""
        if (fb_command != self.last_fb) or (lr_command != self.last_lr):
            if (current_time - self.last_print_time) >= PRINT_COOLDOWN:
                fb_text = fb_command if fb_command is not None else "None"
                lr_text = lr_command if lr_command is not None else "None"
                
                # Simple console output - just the commands
                print(f"{fb_text}, {lr_text}")
                
                # Update GUI if available
                try:
                    from direction_gui import direction_gui
                    direction_gui.update_commands(fb_command, lr_command)
                except ImportError:
                    pass  # GUI not available
                
                self.last_print_time = current_time
                self.last_fb = fb_command
                self.last_lr = lr_command
    
    def draw_direction_overlay(self, frame: np.ndarray, direction_result: Dict, crop_region: Tuple[int, int, int, int]):
        """
        Draw directional control overlay on the frame.
        
        Args:
            frame: Full frame to draw on
            direction_result: Result from analyze_locked_person()
            crop_region: Crop region (x1, y1, x2, y2)
        """
        if not direction_result:
            return
        
        crop_x1, crop_y1, crop_x2, crop_y2 = crop_region
        
        # Draw crop region boundary
        cv2.rectangle(frame, (crop_x1, crop_y1), (crop_x2, crop_y2), (0, 255, 255), 2)
        
        # Draw pose landmarks if available
        pose_landmarks = direction_result.get('pose_landmarks')
        if pose_landmarks:
            self._draw_pose_overlay(frame, pose_landmarks, crop_region)
        
        # Draw command text
        fb_cmd = direction_result.get('forward_backward', 'None')
        lr_cmd = direction_result.get('left_right', 'None')
        
        cv2.putText(frame, f"FB: {fb_cmd}", (crop_x1, crop_y1 - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"LR: {lr_cmd}", (crop_x1, crop_y1 - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    def _draw_pose_overlay(self, frame: np.ndarray, landmarks, crop_region: Tuple[int, int, int, int]):
        """Draw right arm pose overlay on the full frame"""
        crop_x1, crop_y1, crop_x2, crop_y2 = crop_region
        crop_w = crop_x2 - crop_x1
        crop_h = crop_y2 - crop_y1
        
        try:
            # Convert landmarks to full frame coordinates
            right_shoulder = to_px(landmarks[12], crop_w, crop_h)
            right_elbow = to_px(landmarks[14], crop_w, crop_h)
            right_wrist = to_px(landmarks[16], crop_w, crop_h)
            
            # Offset by crop position
            right_shoulder = (right_shoulder[0] + crop_x1, right_shoulder[1] + crop_y1)
            right_elbow = (right_elbow[0] + crop_x1, right_elbow[1] + crop_y1)
            right_wrist = (right_wrist[0] + crop_x1, right_wrist[1] + crop_y1)
            
            # Draw right arm skeleton
            cv2.line(frame, right_shoulder, right_elbow, (0, 255, 0), 3)
            cv2.line(frame, right_elbow, right_wrist, (0, 255, 0), 3)
            
            # Draw joints
            for point in [right_shoulder, right_elbow, right_wrist]:
                cv2.circle(frame, point, 4, (0, 200, 255), -1)
            
            # Draw elbow angle
            elbow_angle = angle_3pts(right_shoulder, right_elbow, right_wrist)
            if elbow_angle is not None:
                cv2.putText(frame, f"{int(elbow_angle)}", 
                           (right_elbow[0] + 8, right_elbow[1] - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 255, 50), 2)
                           
        except (IndexError, AttributeError):
            pass
    
    def get_current_commands(self) -> Dict[str, Optional[str]]:
        """Get the current direction commands"""
        return {
            'forward_backward': self.last_fb,
            'left_right': self.last_lr
        }
    
    def reset_state(self):
        """Reset the direction control state"""
        self.last_fb = None
        self.last_lr = None
        self.last_print_time = 0.0
        self.last_fb_seen_time = 0.0
        self.right_angle_buf.clear()
        print("[DIRECTION] Direction control state reset")