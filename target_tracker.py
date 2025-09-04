# target_tracker.py - Persistent ReID-based person tracking

import time
import numpy as np
from typing import Optional, Tuple, List, Dict
import config
from person_reid import PersonReID

class PersistentPersonProfile:
    """
    Represents a persistent person identity based on ReID features.
    This maintains the person's visual signature across time and occlusions.
    """
    
    def __init__(self, initial_features: np.ndarray, person_id: str):
        self.person_id = person_id
        self.features = initial_features.copy()  # Primary ReID signature
        self.feature_history = [initial_features.copy()]  # History for updates
        self.created_time = time.time()
        self.last_seen_time = time.time()
        self.last_update_time = time.time()
        self.confidence_scores = []  # Track matching confidence over time
        self.total_matches = 0
        
        print(f"[PROFILE] Created persistent person profile: {person_id}")
    
    def update_features(self, new_features: np.ndarray, confidence: float):
        """
        Update the person's feature profile with new high-confidence match.
        Uses exponential moving average to adapt to appearance changes.
        """
        if confidence > 0.80:  # Only update with high-confidence matches
            # Exponential moving average: 70% old features + 30% new features
            self.features = 0.7 * self.features + 0.3 * new_features
            self.feature_history.append(new_features.copy())
            
            # Keep only recent history (last 10 updates)
            if len(self.feature_history) > 10:
                self.feature_history = self.feature_history[-10:]
            
            self.last_update_time = time.time()
            print(f"[PROFILE] Updated {self.person_id} features (confidence: {confidence:.3f})")
    
    def update_seen_time(self):
        """Update the last seen timestamp"""
        self.last_seen_time = time.time()
        self.total_matches += 1
    
    def get_age_seconds(self) -> float:
        """Get how long this profile has existed"""
        return time.time() - self.created_time
    
    def get_time_since_last_seen(self) -> float:
        """Get time since this person was last matched"""
        return time.time() - self.last_seen_time
    
    def get_stability_score(self) -> float:
        """
        Calculate how stable/reliable this person profile is.
        Higher score = more reliable identification.
        """
        age_factor = min(self.get_age_seconds() / 10.0, 1.0)  # Cap at 10 seconds
        match_factor = min(self.total_matches / 20.0, 1.0)    # Cap at 20 matches
        recency_factor = max(0, 1.0 - self.get_time_since_last_seen() / 5.0)  # Decay over 5s
        
        return (age_factor + match_factor + recency_factor) / 3.0

class TargetTracker:
    """
    Handles locking onto and tracking a specific person using persistent ReID profiles.
    Creates permanent person identities that survive occlusions and track ID changes.
    """
    
    def __init__(self, reid_system: PersonReID, 
                 similarity_threshold: float = config.DEFAULT_SIM_THRESH,
                 loss_timeout: float = config.DEFAULT_LOSS_TIMEOUT):
        """
        Initialize persistent person tracker.
        
        Args:
            reid_system: Person re-identification system
            similarity_threshold: Base similarity threshold (will use higher for security)
            loss_timeout: Seconds to wait before auto-unlock (15 seconds)
        """
        self.reid_system = reid_system
        self.loss_timeout = loss_timeout
        
        # Persistent tracking state
        self.locked_person_profile = None  # PersistentPersonProfile object
        self.is_locked = False
        
        # Security thresholds for persistent tracking
        self.lock_similarity_threshold = 0.75   # High threshold for matching locked person
        self.update_similarity_threshold = 0.80  # Very high threshold for profile updates
        self.multi_frame_requirement = 2         # Require N consecutive matches
        
        # Tracking state
        self.consecutive_good_matches = 0
        self.consecutive_no_matches = 0
        self.last_match_box = None
        
        print(f"[TRACKER] Initialized PERSISTENT ReID tracking")
        print(f"[TRACKER] Lock similarity threshold: {self.lock_similarity_threshold:.2f}")
        print(f"[TRACKER] Update similarity threshold: {self.update_similarity_threshold:.2f}")
        print(f"[TRACKER] Loss timeout: {loss_timeout:.1f}s")
        print(f"[TRACKER] Security: High-confidence persistent person identification")
    
    def lock_target(self, frame: np.ndarray, bbox, track_id: Optional[int] = None):
        """
        Create a persistent lock onto a specific person using their ReID features.
        
        Args:
            frame: Current frame
            bbox: Bounding box of target person
            track_id: Track ID (used for logging only, not for identification)
        """
        # Extract ReID features for the target person
        features = self.reid_system.extract_features(frame, bbox)
        
        # Create persistent person profile
        person_id = f"LockedPerson_{int(time.time())}"  # Unique persistent ID
        self.locked_person_profile = PersistentPersonProfile(features, person_id)
        
        # Set tracking state
        self.is_locked = True
        self.consecutive_good_matches = 1  # Start with 1 since we just locked
        self.consecutive_no_matches = 0
        self.last_match_box = bbox
        
        print(f"[TRACKER] 🔒 PERSISTENT LOCK created")
        print(f"[TRACKER] Person ID: {person_id}")
        print(f"[TRACKER] YOLO Track ID: {track_id} (reference only)")
        print(f"[TRACKER] Using ReID features for persistent identification")
        print(f"[TRACKER] Only this specific person can unlock themselves")
    
    def unlock_target(self):
        """Unlock the current target and clear persistent profile"""
        if self.locked_person_profile:
            person_id = self.locked_person_profile.person_id
            profile_age = self.locked_person_profile.get_age_seconds()
            total_matches = self.locked_person_profile.total_matches
            
            print(f"[TRACKER] 🔓 PERSISTENT LOCK removed")
            print(f"[TRACKER] Person {person_id} was tracked for {profile_age:.1f}s with {total_matches} matches")
        
        self.locked_person_profile = None
        self.is_locked = False
        self.consecutive_good_matches = 0
        self.consecutive_no_matches = 0
        self.last_match_box = None
        print("[TRACKER] All people are now visible")
    
    def filter_detections_persistent_reid(self, frame: np.ndarray, 
                                        boxes_xyxy: Optional[np.ndarray], 
                                        track_ids: Optional[np.ndarray]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        PERSISTENT ReID FILTERING: Only show the person matching the locked persistent profile.
        This is the core security feature that prevents false positive locking.
        
        Args:
            frame: Current frame
            boxes_xyxy: All detected bounding boxes
            track_ids: Track IDs (used for logging only)
            
        Returns:
            Tuple of (filtered_boxes, filtered_track_ids) - only locked person or None
        """
        if not self.is_locked or not self.locked_person_profile:
            # Not locked - return all detections (normal mode)
            return boxes_xyxy, track_ids
        
        # Check timeout first
        self._check_timeout()
        if not self.is_locked:
            return boxes_xyxy, track_ids
        
        # No detections available
        if boxes_xyxy is None or len(boxes_xyxy) == 0:
            self.consecutive_no_matches += 1
            self.consecutive_good_matches = 0
            print(f"[TRACKER] No detections - consecutive misses: {self.consecutive_no_matches}")
            return None, None
        
        # Find the locked person using persistent ReID matching
        match_result = self._find_locked_person_persistent(frame, boxes_xyxy, track_ids)
        
        if match_result:
            match_idx, match_box, similarity = match_result
            
            # Update persistent profile and tracking state
            new_features = self.reid_system.extract_features(frame, match_box)
            self.locked_person_profile.update_features(new_features, similarity)
            self.locked_person_profile.update_seen_time()
            
            self.consecutive_good_matches += 1
            self.consecutive_no_matches = 0
            self.last_match_box = match_box
            
            # Return only this person
            target_box = boxes_xyxy[match_idx:match_idx+1]
            target_id = track_ids[match_idx:match_idx+1] if track_ids is not None else None
            
            person_id = self.locked_person_profile.person_id
            stability = self.locked_person_profile.get_stability_score()
            
            print(f"[TRACKER] ✓ {person_id} found: similarity={similarity:.3f}, stability={stability:.2f}, consecutive={self.consecutive_good_matches}")
            
            return target_box, target_id
        else:
            # Locked person not found with sufficient confidence
            self.consecutive_no_matches += 1
            self.consecutive_good_matches = 0
            
            person_id = self.locked_person_profile.person_id
            print(f"[TRACKER] ✗ {person_id} not found - consecutive misses: {self.consecutive_no_matches}")
            
            return None, None
    
    def _find_locked_person_persistent(self, frame: np.ndarray, 
                                     boxes_xyxy: np.ndarray, 
                                     track_ids: Optional[np.ndarray]) -> Optional[Tuple[int, np.ndarray, float]]:
        """
        Find the locked person among current detections using persistent ReID matching.
        Uses high confidence thresholds and multi-frame validation for security.
        
        Returns:
            Tuple of (match_index, match_box, similarity) or None if not found
        """
        if not self.locked_person_profile:
            return None
        
        best_similarity = -1.0
        best_index = None
        similarities = []
        
        # Compare each detection against the locked person's persistent profile
        for i, box in enumerate(boxes_xyxy):
            features = self.reid_system.extract_features(frame, box)
            similarity = self.reid_system.compute_similarity(
                self.locked_person_profile.features, features
            )
            similarities.append(similarity)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = i
        
        person_id = self.locked_person_profile.person_id
        available_ids = [int(tid) for tid in track_ids] if track_ids is not None else ["N/A"]
        
        print(f"[TRACKER] {person_id} matching: similarities={[f'{s:.3f}' for s in similarities]}, "
              f"YOLO_IDs={available_ids}, thresh={self.lock_similarity_threshold:.3f}")
        
        # Apply high confidence threshold for security
        if best_index is not None and best_similarity >= self.lock_similarity_threshold:
            
            # Additional security: spatial consistency check
            if self._validate_spatial_consistency(boxes_xyxy[best_index], similarities):
                return best_index, boxes_xyxy[best_index], best_similarity
            else:
                print(f"[TRACKER] {person_id} failed spatial consistency check")
                return None
        
        print(f"[TRACKER] {person_id} similarity too low: {best_similarity:.3f} < {self.lock_similarity_threshold:.3f}")
        return None
    
    def _validate_spatial_consistency(self, current_box, similarities) -> bool:
        """
        Validate that the matched person's location makes spatial sense.
        Prevents teleportation-like false matches.
        """
        if self.last_match_box is None:
            return True  # First match, no previous position to compare
        
        # Calculate movement distance
        from utils import box_center
        last_center = box_center(self.last_match_box)
        current_center = box_center(current_box)
        
        distance = np.sqrt((last_center[0] - current_center[0])**2 + 
                          (last_center[1] - current_center[1])**2)
        
        # Maximum reasonable movement per frame (adjust based on frame rate)
        max_movement = 50  # pixels per frame
        
        if distance > max_movement:
            print(f"[TRACKER] Spatial check: movement too large ({distance:.1f} > {max_movement})")
            return False
        
        return True
    
    def is_target_person_at_location(self, frame: np.ndarray, gesture_x: int, gesture_y: int, 
                                   boxes_xyxy: Optional[np.ndarray], 
                                   track_ids: Optional[np.ndarray]) -> bool:
        """
        Check if victory gesture comes from the locked person using persistent ReID.
        This provides secure victory gesture validation.
        
        Args:
            frame: Current frame
            gesture_x, gesture_y: Gesture location
            boxes_xyxy: All detected boxes (before filtering)
            track_ids: All track IDs (before filtering)
            
        Returns:
            True if gesture comes from the locked person
        """
        if not self.is_locked or not self.locked_person_profile:
            return False
        
        if boxes_xyxy is None or len(boxes_xyxy) == 0:
            return False
        
        # Find which person the gesture is associated with
        from utils import associate_gesture_to_person
        associated_idx = associate_gesture_to_person(gesture_x, gesture_y, boxes_xyxy, frame.shape[:2])
        
        if associated_idx is None:
            print(f"[SECURITY] Victory gesture not associated with any person")
            return False
        
        # Check if the associated person matches our locked person profile
        associated_box = boxes_xyxy[associated_idx]
        features = self.reid_system.extract_features(frame, associated_box)
        similarity = self.reid_system.compute_similarity(
            self.locked_person_profile.features, features
        )
        
        person_id = self.locked_person_profile.person_id
        is_match = similarity >= self.lock_similarity_threshold
        
        if is_match:
            print(f"[SECURITY] ✓ Victory gesture from {person_id} (similarity: {similarity:.3f})")
        else:
            associated_track_id = track_ids[associated_idx] if track_ids is not None else "N/A"
            print(f"[SECURITY] ✗ Victory gesture from different person (YOLO_ID: {associated_track_id}, similarity: {similarity:.3f})")
            print(f"[SECURITY] Required similarity: {self.lock_similarity_threshold:.3f} for {person_id}")
        
        return is_match
    
    def _check_timeout(self):
        """Check if target should be unlocked due to timeout"""
        if not self.is_locked or not self.locked_person_profile:
            return
        
        time_since_last_seen = self.locked_person_profile.get_time_since_last_seen()
        if time_since_last_seen > self.loss_timeout:
            person_id = self.locked_person_profile.person_id
            print(f"[TRACKER] ⏰ TIMEOUT: {person_id} lost for {time_since_last_seen:.1f}s (>{self.loss_timeout}s)")
            self.unlock_target()
    
    def get_state(self) -> dict:
        """Get current persistent tracking state information"""
        if self.locked_person_profile:
            return {
                'is_locked': self.is_locked,
                'person_id': self.locked_person_profile.person_id,
                'profile_age': self.locked_person_profile.get_age_seconds(),
                'time_since_last_seen': self.locked_person_profile.get_time_since_last_seen(),
                'total_matches': self.locked_person_profile.total_matches,
                'stability_score': self.locked_person_profile.get_stability_score(),
                'consecutive_good_matches': self.consecutive_good_matches,
                'consecutive_no_matches': self.consecutive_no_matches,
                'approach': 'PERSISTENT_REID',
                'security_level': 'HIGH'
            }
        else:
            return {
                'is_locked': False,
                'approach': 'PERSISTENT_REID',
                'security_level': 'HIGH'
            }
    
    def set_loss_timeout(self, timeout: float):
        """Update loss timeout"""
        self.loss_timeout = timeout
        print(f"[TRACKER] Updated loss timeout to {timeout:.1f}s")
    
    def set_similarity_threshold(self, threshold: float):
        """Update similarity threshold for locking"""
        self.lock_similarity_threshold = threshold
        print(f"[TRACKER] Updated lock similarity threshold to {threshold:.2f}")
    
    # Legacy method aliases for backward compatibility
    def filter_detections_exclusive(self, frame: np.ndarray, 
                                   boxes_xyxy: Optional[np.ndarray], 
                                   track_ids: Optional[np.ndarray]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Legacy method - redirects to persistent ReID filtering"""
        return self.filter_detections_persistent_reid(frame, boxes_xyxy, track_ids)