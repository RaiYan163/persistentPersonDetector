# gesture_detector.py - MediaPipe gesture recognition

import cv2
import math
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

# Helper functions for fist+palm detection
def calculate_hand_centers_distance(hand1_landmarks, hand2_landmarks, frame_shape):
    """
    Calculate distance between two hand centers (wrist positions).
    Returns both pixel distance and normalized distance ratio.
    """
    if not hand1_landmarks or not hand2_landmarks or len(hand1_landmarks) < 1 or len(hand2_landmarks) < 1:
        return float('inf'), float('inf')
    
    # Get wrist positions (landmark 0 is always the wrist)
    wrist1_x = hand1_landmarks[0][0]  # hand1 wrist X
    wrist1_y = hand1_landmarks[0][1]  # hand1 wrist Y
    wrist2_x = hand2_landmarks[0][0]  # hand2 wrist X
    wrist2_y = hand2_landmarks[0][1]  # hand2 wrist Y
    
    # Calculate pixel distance
    pixel_distance = math.sqrt((wrist1_x - wrist2_x)**2 + (wrist1_y - wrist2_y)**2)
    
    # Calculate frame diagonal for normalization
    H, W = frame_shape[:2]
    frame_diagonal = math.sqrt(W*W + H*H)
    
    # Calculate normalized distance ratio
    distance_ratio = pixel_distance / frame_diagonal
    
    return pixel_distance, distance_ratio

def calculate_hand_midpoint(hand1_landmarks, hand2_landmarks):
    """Calculate midpoint between two hand centers."""
    if not hand1_landmarks or not hand2_landmarks or len(hand1_landmarks) < 1 or len(hand2_landmarks) < 1:
        return None, None
    
    wrist1_x, wrist1_y = hand1_landmarks[0][0], hand1_landmarks[0][1]
    wrist2_x, wrist2_y = hand2_landmarks[0][0], hand2_landmarks[0][1]
    
    midpoint_x = int((wrist1_x + wrist2_x) / 2)
    midpoint_y = int((wrist1_y + wrist2_y) / 2)
    
    return midpoint_x, midpoint_y

def is_closed_fist(gesture_categories):
    """Check if gesture is closed fist."""
    if not gesture_categories:
        return False, 0.0
    
    for cat in gesture_categories:
        name = (cat.category_name or "").lower().replace("-", "_").replace(" ", "_")
        if name in ["closed_fist", "fist"]:
            return True, float(cat.score)
    
    return False, 0.0

def is_open_palm(gesture_categories):
    """Check if gesture is open palm."""
    if not gesture_categories:
        return False, 0.0
    
    for cat in gesture_categories:
        name = (cat.category_name or "").lower().replace("-", "_").replace(" ", "_")
        if name in ["open_palm", "palm"]:
            return True, float(cat.score)
    
    return False, 0.0

def is_victory_gesture(gesture_categories):
    """Check if gesture is victory/peace sign."""
    if not gesture_categories:
        return False, 0.0
    
    for cat in gesture_categories:
        name = (cat.category_name or "").lower().replace("-", "_").replace(" ", "_")
        if name in ["victory", "peace"]:
            return True, float(cat.score)
    
    return False, 0.0

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
        
        # Add fist+palm detection
        fist_palm_result = self.detect_fist_palm_combination(all_hands_data, (H, W))
        
        # Add dual victory detection
        dual_victory_result = self.detect_dual_victory_combination(all_hands_data, (H, W))

        return {
            'pointing_up_list': pointing_up_list,
            'victory_list': victory_list,
            'fist_palm_combination': fist_palm_result,
            'dual_victory_combination': dual_victory_result,  # NEW
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
    
    def detect_fist_palm_combination(self, all_hands_data, frame_shape):
        """
        Detect fist + palm combination with proximity validation.
        Returns detection result with midpoint for person association.
        """
        # Initialize result structure
        result = {
            'detected': False,
            'fist_hand_idx': None,
            'palm_hand_idx': None,
            'midpoint': (None, None),
            'distance_pixels': float('inf'),
            'distance_ratio': float('inf'),
            'fist_confidence': 0.0,
            'palm_confidence': 0.0,
            'close_enough': False
        }
        
        # Must have exactly 2 hands
        if len(all_hands_data) != config.FIST_PALM_REQUIRED_HANDS:
            return result
        
        hand1 = all_hands_data[0]
        hand2 = all_hands_data[1]
        
        # Check if we have the fist + palm combination
        hand1_is_fist, hand1_fist_score = is_closed_fist([type('obj', (object,), {'category_name': hand1['gesture'], 'score': hand1['score']})()])
        hand1_is_palm, hand1_palm_score = is_open_palm([type('obj', (object,), {'category_name': hand1['gesture'], 'score': hand1['score']})()])
        
        hand2_is_fist, hand2_fist_score = is_closed_fist([type('obj', (object,), {'category_name': hand2['gesture'], 'score': hand2['score']})()])
        hand2_is_palm, hand2_palm_score = is_open_palm([type('obj', (object,), {'category_name': hand2['gesture'], 'score': hand2['score']})()])
        
        # Check for valid combinations (order independent)
        fist_hand_idx = None
        palm_hand_idx = None
        fist_confidence = 0.0
        palm_confidence = 0.0
        
        if hand1_is_fist and hand2_is_palm:
            # Hand 1 is fist, Hand 2 is palm
            fist_hand_idx = 0
            palm_hand_idx = 1
            fist_confidence = hand1_fist_score
            palm_confidence = hand2_palm_score
        elif hand1_is_palm and hand2_is_fist:
            # Hand 1 is palm, Hand 2 is fist
            fist_hand_idx = 1
            palm_hand_idx = 0
            fist_confidence = hand2_fist_score
            palm_confidence = hand1_palm_score
        else:
            # No valid combination found
            return result
        
        # Check confidence thresholds
        if (fist_confidence < config.FIST_PALM_MIN_CONFIDENCE or 
            palm_confidence < config.FIST_PALM_MIN_CONFIDENCE):
            return result
        
        # Calculate distance between hands
        hand1_landmarks = hand1['landmarks']
        hand2_landmarks = hand2['landmarks']
        
        pixel_distance, distance_ratio = calculate_hand_centers_distance(
            hand1_landmarks, hand2_landmarks, frame_shape
        )
        
        # Check if hands are close enough
        close_enough = (pixel_distance <= config.FIST_PALM_MAX_DISTANCE_PIXELS or 
                       distance_ratio <= config.FIST_PALM_MAX_DISTANCE_RATIO)
        
        # Calculate midpoint for person association
        midpoint_x, midpoint_y = calculate_hand_midpoint(hand1_landmarks, hand2_landmarks)
        
        # Update result
        result.update({
            'detected': close_enough,  # Only true if close enough
            'fist_hand_idx': fist_hand_idx,
            'palm_hand_idx': palm_hand_idx,
            'midpoint': (midpoint_x, midpoint_y),
            'distance_pixels': pixel_distance,
            'distance_ratio': distance_ratio,
            'fist_confidence': fist_confidence,
            'palm_confidence': palm_confidence,
            'close_enough': close_enough
        })
        
        # Debug information
        if result['detected']:
            print(f"[FIST+PALM] DETECTED: Fist confidence={fist_confidence:.2f}, "
                  f"Palm confidence={palm_confidence:.2f}, Distance={pixel_distance:.0f}px")
        elif fist_hand_idx is not None and palm_hand_idx is not None:
            print(f"[FIST+PALM] Gestures OK but TOO FAR: Distance={pixel_distance:.0f}px "
                  f"(max={config.FIST_PALM_MAX_DISTANCE_PIXELS}px)")
        
        return result
    
    def detect_dual_victory_combination(self, all_hands_data, frame_shape):
        """
        Detect dual victory gesture combination with proximity validation.
        Both hands must show victory gestures and be close together.
        Returns detection result with midpoint for person association.
        """
        # Initialize result structure
        result = {
            'detected': False,
            'victory1_hand_idx': None,
            'victory2_hand_idx': None,
            'midpoint': (None, None),
            'distance_pixels': float('inf'),
            'distance_ratio': float('inf'),
            'victory1_confidence': 0.0,
            'victory2_confidence': 0.0,
            'close_enough': False
        }
        
        # Must have exactly 2 hands
        if len(all_hands_data) != config.DUAL_VICTORY_REQUIRED_HANDS:
            return result
        
        hand1 = all_hands_data[0]
        hand2 = all_hands_data[1]
        
        # Check if both hands show victory gestures using the proper method
        hand1_is_victory = hand1.get('is_victory', False)
        hand2_is_victory = hand2.get('is_victory', False)
        hand1_victory_score = hand1.get('score', 0.0) if hand1_is_victory else 0.0
        hand2_victory_score = hand2.get('score', 0.0) if hand2_is_victory else 0.0
        
        # Both hands must be victory gestures
        if not (hand1_is_victory and hand2_is_victory):
            # Debug output to understand what gestures are detected
            print(f"[DUAL_VICTORY] Hand1: {hand1.get('gesture', 'Unknown')} (is_victory: {hand1_is_victory})")
            print(f"[DUAL_VICTORY] Hand2: {hand2.get('gesture', 'Unknown')} (is_victory: {hand2_is_victory})")
            return result
        
        # Check confidence thresholds
        if (hand1_victory_score < config.DUAL_VICTORY_MIN_CONFIDENCE or 
            hand2_victory_score < config.DUAL_VICTORY_MIN_CONFIDENCE):
            return result
        
        # Calculate distance between hands
        hand1_landmarks = hand1['landmarks']
        hand2_landmarks = hand2['landmarks']
        
        pixel_distance, distance_ratio = calculate_hand_centers_distance(
            hand1_landmarks, hand2_landmarks, frame_shape
        )
        
        # Check if hands are close enough
        close_enough = (pixel_distance <= config.DUAL_VICTORY_MAX_DISTANCE_PIXELS or 
                       distance_ratio <= config.DUAL_VICTORY_MAX_DISTANCE_RATIO)
        
        # Calculate midpoint for person association
        midpoint_x, midpoint_y = calculate_hand_midpoint(hand1_landmarks, hand2_landmarks)
        
        # Update result
        result.update({
            'detected': close_enough,  # Only true if close enough
            'victory1_hand_idx': 0,
            'victory2_hand_idx': 1,
            'midpoint': (midpoint_x, midpoint_y),
            'distance_pixels': pixel_distance,
            'distance_ratio': distance_ratio,
            'victory1_confidence': hand1_victory_score,
            'victory2_confidence': hand2_victory_score,
            'close_enough': close_enough
        })
        
        # Debug information
        if result['detected']:
            print(f"[DUAL_VICTORY] DETECTED: Victory1 confidence={hand1_victory_score:.2f}, "
                  f"Victory2 confidence={hand2_victory_score:.2f}, Distance={pixel_distance:.0f}px")
        elif hand1_is_victory and hand2_is_victory:
            print(f"[DUAL_VICTORY] Both victory gestures OK but TOO FAR: Distance={pixel_distance:.0f}px "
                  f"(max={config.DUAL_VICTORY_MAX_DISTANCE_PIXELS}px)")
        
        return result
    
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