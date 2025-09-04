# gesture_detector.py - MediaPipe gesture recognition

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Tuple, Dict
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
import config
from utils import download_if_missing

# Compatibility for different MediaPipe versions
try:
    from mediapipe.tasks.python.vision import RunningMode
except Exception:
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode as RunningMode

class GestureDetector:
    """
    Handles hand gesture recognition using MediaPipe.
    Detects pointing_up (for locking) and victory (for unlocking) gestures.
    """
    
    def __init__(self, model_path: str = config.GESTURE_PATH, 
                 min_score: float = config.DEFAULT_GESTURE_CONF):
        """
        Initialize the gesture detector.
        
        Args:
            model_path: Path to MediaPipe gesture model
            min_score: Minimum confidence score for gesture detection
        """
        # Download model if missing
        download_if_missing(config.GESTURE_URL, model_path)
        
        # Setup MediaPipe
        base_options = BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=RunningMode.VIDEO,
            num_hands=config.MAX_HANDS
        )
        
        self.recognizer = vision.GestureRecognizer.create_from_options(options)
        self.min_score = min_score
        print(f"[GESTURE] Loaded MediaPipe gesture recognizer")
        print(f"[GESTURE] Lock gesture: POINTING UP (replaces thumbs up)")
        print(f"[GESTURE] Unlock gesture: VICTORY")
    
    def detect_gestures(self, frame_bgr: np.ndarray, timestamp_ms: int) -> Dict:
        """
        Detect all gestures in the frame.
        
        Args:
            frame_bgr: Input frame in BGR format
            timestamp_ms: Timestamp in milliseconds
            
        Returns:
            Dictionary containing:
            - pointing_up_list: List of pointing up detections
            - victory_list: List of victory gesture detections  
            - all_hands_data: List of all hand data for visualization
        """
        H, W = frame_bgr.shape[:2]
        
        # Convert to RGB for MediaPipe
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        # Recognize gestures
        result = self.recognizer.recognize_for_video(mp_image, timestamp_ms)
        
        pointing_up_list = []
        victory_list = []
        all_hands_data = []
        
        if not result or not result.hand_landmarks:
            return {
                'pointing_up_list': pointing_up_list,
                'victory_list': victory_list,
                'all_hands_data': all_hands_data
            }
        
        # Process each detected hand
        for i, landmarks_list in enumerate(result.hand_landmarks):
            if not landmarks_list:
                continue
                
            # Convert landmarks to pixel coordinates
            landmarks = []
            for lm in landmarks_list:
                x = int(lm.x * W)
                y = int(lm.y * H)
                landmarks.append((x, y))
            
            # Analyze gesture
            hand_data = self._analyze_hand_gesture(landmarks, result.gestures, i)
            all_hands_data.append(hand_data)
            
            # Check for specific gestures
            wrist_x, wrist_y = landmarks[0]  # Wrist is landmark 0
            
            if hand_data['is_pointing_up'] and hand_data['score'] >= self.min_score:
                pointing_up_list.append({
                    'x': wrist_x,
                    'y': wrist_y,
                    'score': hand_data['score'],
                    'label': hand_data['gesture']
                })
            
            if hand_data['is_victory'] and hand_data['score'] >= self.min_score:
                victory_list.append({
                    'x': wrist_x,
                    'y': wrist_y,
                    'score': hand_data['score'],
                    'label': hand_data['gesture']
                })
        
        return {
            'pointing_up_list': pointing_up_list,
            'victory_list': victory_list,
            'all_hands_data': all_hands_data
        }
    
    def _analyze_hand_gesture(self, landmarks: List[Tuple[int, int]], 
                            all_gestures, hand_index: int) -> Dict:
        """
        Analyze gesture for a single hand.
        
        Returns:
            Dictionary with gesture information
        """
        gesture_data = {
            'landmarks': landmarks,
            'gesture': 'None',
            'score': 0.0,
            'is_pointing_up': False,
            'is_victory': False
        }
        
        if not all_gestures or hand_index >= len(all_gestures):
            return gesture_data
        
        gesture_categories = all_gestures[hand_index]
        if not gesture_categories:
            return gesture_data
        
        # Check for pointing up
        is_pointing_up, pu_score, pu_label = self._is_pointing_up(gesture_categories)
        
        # Check for victory gesture
        is_victory, vic_score, vic_label = self._is_victory(gesture_categories)
        
        # Prioritize between gestures if both detected
        if is_pointing_up and is_victory:
            if pu_score >= vic_score:
                gesture_data.update({
                    'gesture': pu_label,
                    'score': pu_score,
                    'is_pointing_up': True,
                    'is_victory': False
                })
            else:
                gesture_data.update({
                    'gesture': vic_label,
                    'score': vic_score,
                    'is_pointing_up': False,
                    'is_victory': True
                })
        elif is_pointing_up:
            gesture_data.update({
                'gesture': pu_label,
                'score': pu_score,
                'is_pointing_up': True
            })
        elif is_victory:
            gesture_data.update({
                'gesture': vic_label,
                'score': vic_score,
                'is_victory': True
            })
        else:
            # Get best gesture for display
            best = max(gesture_categories, key=lambda c: c.score)
            gesture_data.update({
                'gesture': best.category_name or "Unknown",
                'score': float(best.score)
            })
        
        return gesture_data
    
    @staticmethod
    def _is_pointing_up(gesture_categories) -> Tuple[bool, float, str]:
        """Check if gesture is pointing up"""
        if not gesture_categories:
            return False, 0.0, ""
        
        for cat in gesture_categories:
            name = (cat.category_name or "").lower().replace("-", "_").replace(" ", "_")
            if "pointing_up" in name or name in ["point_up", "pointing"]:
                return True, float(cat.score), cat.category_name or "Pointing_Up"
        
        # Return best gesture for debugging
        best = max(gesture_categories, key=lambda c: c.score)
        return False, float(best.score), best.category_name or "Unknown"
    
    @staticmethod
    def _is_victory(gesture_categories) -> Tuple[bool, float, str]:
        """Check if gesture is victory/peace sign"""
        if not gesture_categories:
            return False, 0.0, ""
        
        for cat in gesture_categories:
            name = (cat.category_name or "").lower().replace("-", "_").replace(" ", "_")
            if name in ["victory", "peace"]:
                return True, float(cat.score), cat.category_name or "Victory"
        
        best = max(gesture_categories, key=lambda c: c.score)
        return False, float(best.score), best.category_name or "Unknown"
    
    def set_min_score(self, score: float):
        """Update minimum confidence score"""
        self.min_score = score
        print(f"[GESTURE] Updated min score to {score}")
    
    def get_best_pointing_up(self, pointing_up_list: List[Dict]) -> Dict:
        """Get the pointing up gesture with highest confidence"""
        if not pointing_up_list:
            return None
        return max(pointing_up_list, key=lambda d: d['score'])
    
    def get_best_victory(self, victory_list: List[Dict]) -> Dict:
        """Get the victory gesture with highest confidence"""
        if not victory_list:
            return None
        return max(victory_list, key=lambda d: d['score'])