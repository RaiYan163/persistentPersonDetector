# utils.py - Helper functions and utilities with exclusive mode support

import os
import math
import urllib.request
import numpy as np
import cv2
from typing import Tuple, List, Optional
import config

def download_if_missing(url: str, path: str):
    """Download a file if it doesn't exist locally."""
    if os.path.isfile(path):
        return
    print(f"[DL] Downloading {os.path.basename(path)}...")
    urllib.request.urlretrieve(url, path)
    print(f"[DL] Saved to {path}")

def to_np_xyxy(box) -> np.ndarray:
    """
    Ensure a 1D np.ndarray [x1,y1,x2,y2] regardless of input type.
    Handles torch.Tensor, list, or numpy array inputs.
    """
    # Handle torch.Tensor without importing torch explicitly
    if hasattr(box, "detach") and hasattr(box, "cpu") and hasattr(box, "numpy"):
        try:
            box = box.detach().cpu().numpy()
        except Exception:
            pass
    
    arr = np.asarray(box).reshape(-1)
    return arr.astype(np.float32)

def expand_box(box, expansion_factor: float = config.BOX_EXPANSION_FACTOR) -> np.ndarray:
    """Expand bounding box by factor to catch gestures near person"""
    box = to_np_xyxy(box)
    x1, y1, x2, y2 = box[:4]
    
    w, h = x2 - x1, y2 - y1
    expansion_w = w * expansion_factor
    expansion_h = h * expansion_factor
    
    return np.array([x1 - expansion_w, y1 - expansion_h, 
                    x2 + expansion_w, y2 + expansion_h])

def point_in_box(px: int, py: int, box) -> bool:
    """Check if point is inside bounding box"""
    box = to_np_xyxy(box)
    x1, y1, x2, y2 = box[:4]
    return (px >= x1) and (px <= x2) and (py >= y1) and (py <= y2)

def box_center(box) -> Tuple[int, int]:
    """Get center point of bounding box"""
    box = to_np_xyxy(box)
    x1, y1, x2, y2 = box[:4]
    return int((x1 + x2) / 2), int((y1 + y2) / 2)

def associate_gesture_to_person(gesture_x: int, gesture_y: int, 
                               boxes_xyxy: np.ndarray, 
                               frame_shape: Tuple[int, int]) -> Optional[int]:
    """
    Associate a gesture to the nearest person.
    Returns index of the person or None if no association found.
    
    IMPORTANT: This function now works with ALL detections (before filtering)
    to ensure proper gesture-to-person association in exclusive mode.
    """
    if boxes_xyxy is None or len(boxes_xyxy) == 0:
        return None
    
    H, W = frame_shape
    
    # Method 1: Try expanded bounding boxes first (most reliable)
    for i, box in enumerate(boxes_xyxy):
        expanded_box = expand_box(box)
        if point_in_box(gesture_x, gesture_y, expanded_box):
            print(f"[ASSOC] Gesture at ({gesture_x},{gesture_y}) -> Person {i} (expanded box)")
            return i
    
    # Method 2: Find nearest person within reasonable distance
    max_distance = math.sqrt(W*W + H*H) * config.MAX_GESTURE_DISTANCE
    best_distance = float('inf')
    best_idx = None
    
    for i, box in enumerate(boxes_xyxy):
        cx, cy = box_center(box)
        distance = math.hypot(gesture_x - cx, gesture_y - cy)
        if distance < max_distance and distance < best_distance:
            best_distance = distance
            best_idx = i
    
    if best_idx is not None:
        print(f"[ASSOC] Gesture at ({gesture_x},{gesture_y}) -> Person {best_idx} (nearest, dist={best_distance:.1f})")
        return best_idx
    
    print(f"[ASSOC] Gesture at ({gesture_x},{gesture_y}) -> No person associated")
    return None

def associate_fist_palm_to_person(midpoint_x: int, midpoint_y: int, 
                                 hand1_landmarks: List[Tuple[int, int]], 
                                 hand2_landmarks: List[Tuple[int, int]],
                                 boxes_xyxy: np.ndarray, 
                                 frame_shape: Tuple[int, int]) -> Optional[int]:
    """
    Associate fist+palm gesture combination to the nearest person.
    Uses midpoint between hands as primary association point.
    
    Args:
        midpoint_x, midpoint_y: Midpoint between the two hands
        hand1_landmarks, hand2_landmarks: Hand landmark positions
        boxes_xyxy: Person bounding boxes
        frame_shape: Frame dimensions
        
    Returns:
        Index of the person or None if no association found
    """
    if boxes_xyxy is None or len(boxes_xyxy) == 0:
        return None
    
    if midpoint_x is None or midpoint_y is None:
        return None
    
    H, W = frame_shape
    
    # Method 1: Try midpoint inside expanded bounding boxes
    for i, box in enumerate(boxes_xyxy):
        expanded_box = expand_box(box, expansion_factor=0.5)  # Larger expansion for two hands
        if point_in_box(midpoint_x, midpoint_y, expanded_box):
            print(f"[ASSOC] Fist+Palm midpoint ({midpoint_x},{midpoint_y}) -> Person {i} (expanded box)")
            return i
    
    # Method 2: Try if both hands are near the same person
    for i, box in enumerate(boxes_xyxy):
        expanded_box = expand_box(box, expansion_factor=0.6)
        
        # Check if both hand centers are near this person
        hand1_center = hand1_landmarks[0] if hand1_landmarks else (0, 0)
        hand2_center = hand2_landmarks[0] if hand2_landmarks else (0, 0)
        
        hand1_near = point_in_box(hand1_center[0], hand1_center[1], expanded_box)
        hand2_near = point_in_box(hand2_center[0], hand2_center[1], expanded_box)
        
        if hand1_near and hand2_near:
            print(f"[ASSOC] Both hands near Person {i}")
            return i
    
    # Method 3: Find nearest person to midpoint
    max_distance = math.sqrt(W*W + H*H) * 0.3  # 30% of diagonal
    best_distance = float('inf')
    best_idx = None
    
    for i, box in enumerate(boxes_xyxy):
        cx, cy = box_center(box)
        distance = math.hypot(midpoint_x - cx, midpoint_y - cy)
        if distance < max_distance and distance < best_distance:
            best_distance = distance
            best_idx = i
    
    if best_idx is not None:
        print(f"[ASSOC] Fist+Palm midpoint ({midpoint_x},{midpoint_y}) -> Person {best_idx} (nearest, dist={best_distance:.1f})")
        return best_idx
    
    print(f"[ASSOC] Fist+Palm midpoint ({midpoint_x},{midpoint_y}) -> No person associated")
    return None

def draw_hand_landmarks(frame: np.ndarray, landmarks: List[Tuple[int, int]], 
                       color=config.BLUE, thickness: int = 2):
    """Draw hand landmarks and connections on the frame"""
    if not landmarks or len(landmarks) < 21:
        return
    
    # Draw connections
    for a, b in config.HAND_CONNECTIONS:
        if a < len(landmarks) and b < len(landmarks):
            cv2.line(frame, landmarks[a], landmarks[b], color, thickness)
    
    # Draw landmarks
    for (x, y) in landmarks:
        cv2.circle(frame, (x, y), 2, config.YELLOW, -1)

def draw_person_boxes(frame: np.ndarray, boxes_xyxy: np.ndarray, 
                     ids: Optional[np.ndarray] = None, 
                     color=config.GREEN, thickness: int = 2):
    """
    Draw bounding boxes around detected persons.
    In exclusive mode, this will only draw the target person.
    """
    if boxes_xyxy is None or len(boxes_xyxy) == 0:
        return
    
    for i, box in enumerate(boxes_xyxy):
        box = to_np_xyxy(box)
        x1, y1, x2, y2 = box[:4]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        if ids is not None and i < len(ids):
            cv2.putText(frame, f"ID:{ids[i]}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_locked_target(frame: np.ndarray, box, similarity: float):
    """
    Draw the locked target with red box and similarity score.
    NOTE: This function is now less used since exclusive mode handles target drawing.
    """
    box = to_np_xyxy(box)
    x1, y1, x2, y2 = box[:4].astype(int)
    cv2.rectangle(frame, (x1, y1), (x2, y2), config.RED, 4)
    cv2.putText(frame, f"LOCKED ({similarity:.2f})", 
               (x1, max(0, y1 - 10)), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.RED, 3)

def draw_hud(frame: np.ndarray, is_locked: bool):
    """
    Legacy HUD function - replaced by draw_exclusive_hud in main.py
    Kept for backward compatibility.
    """
    H = frame.shape[0]
    
    state_str = "LOCKED" if is_locked else "UNLOCKED"
    if not is_locked:
        instructions = "Show THUMBS UP near your body to lock onto yourself"
    else:
        instructions = "Person locked - Show VICTORY sign to unlock (YOU ONLY)"
    
    cv2.putText(frame, f"STATE: {state_str}", (20, H - 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.WHITE, 3)
    cv2.putText(frame, instructions, (20, H - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
    cv2.putText(frame, "r: reset | q: quit | f: fullscreen", (20, H - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.WHITE, 2)

# New utility functions for exclusive mode

def get_detection_summary(boxes_xyxy: Optional[np.ndarray], 
                         track_ids: Optional[np.ndarray], 
                         is_exclusive_mode: bool = False) -> str:
    """
    Get a summary string of current detections for debugging.
    
    Args:
        boxes_xyxy: Detected bounding boxes
        track_ids: Track IDs
        is_exclusive_mode: Whether system is in exclusive mode
        
    Returns:
        Summary string for logging
    """
    if boxes_xyxy is None or len(boxes_xyxy) == 0:
        return "No detections"
    
    count = len(boxes_xyxy)
    mode = "EXCLUSIVE" if is_exclusive_mode else "NORMAL"
    
    if track_ids is not None:
        ids_str = ",".join([str(int(tid)) for tid in track_ids])
        return f"{mode} mode: {count} person(s) [IDs: {ids_str}]"
    else:
        return f"{mode} mode: {count} person(s) [No IDs]"

def validate_exclusive_mode_state(tracker_locked: bool, 
                                 filtered_count: int, 
                                 original_count: int) -> bool:
    """
    Validate that exclusive mode is working correctly.
    
    Args:
        tracker_locked: Whether tracker is in locked state
        filtered_count: Number of detections after filtering
        original_count: Number of detections before filtering
        
    Returns:
        True if state is valid, False if there's an issue
    """
    if tracker_locked:
        # In exclusive mode, should have 0 or 1 detection
        if filtered_count > 1:
            print(f"[WARNING] Exclusive mode violation: {filtered_count} people visible (should be 0-1)")
            return False
        if filtered_count == 1 and original_count > 1:
            print(f"[EXCLUSIVE] Correctly filtered: {original_count} -> 1 person")
    else:
        # In normal mode, filtered should equal original
        if filtered_count != original_count:
            print(f"[WARNING] Normal mode filtering issue: {original_count} -> {filtered_count}")
            return False
    
    return True

def calculate_gesture_person_distance(gesture_x: int, gesture_y: int, 
                                     bbox, frame_shape: Tuple[int, int]) -> float:
    """
    Calculate normalized distance between gesture and person center.
    
    Args:
        gesture_x, gesture_y: Gesture coordinates
        bbox: Person bounding box
        frame_shape: Frame dimensions (H, W)
        
    Returns:
        Normalized distance (0.0 = same location, 1.0 = opposite corners)
    """
    H, W = frame_shape
    diagonal = math.sqrt(W*W + H*H)
    
    cx, cy = box_center(bbox)
    distance = math.hypot(gesture_x - cx, gesture_y - cy)
    
    return distance / diagonal

def is_gesture_near_person(gesture_x: int, gesture_y: int, 
                          bbox, frame_shape: Tuple[int, int],
                          max_distance_ratio: float = config.MAX_GESTURE_DISTANCE) -> bool:
    """
    Check if gesture is near enough to a person to be associated.
    
    Args:
        gesture_x, gesture_y: Gesture coordinates
        bbox: Person bounding box
        frame_shape: Frame dimensions
        max_distance_ratio: Maximum distance as ratio of diagonal
        
    Returns:
        True if gesture is near enough to person
    """
    distance_ratio = calculate_gesture_person_distance(gesture_x, gesture_y, bbox, frame_shape)
    return distance_ratio <= max_distance_ratio