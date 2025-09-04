# person_detector.py - YOLO person detection

import numpy as np
from ultralytics import YOLO
from typing import Tuple, Optional
import config

class PersonDetector:
    """
    Handles person detection using YOLO model.
    Provides a clean interface for detecting people in frames.
    """
    
    def __init__(self, model_path: str = config.YOLO_WEIGHTS, 
                 conf_threshold: float = config.DEFAULT_CONF,
                 iou_threshold: float = config.DEFAULT_IOU,
                 tracker_config: str = config.DEFAULT_TRACKER):
        """
        Initialize the person detector.
        
        Args:
            model_path: Path to YOLO weights file
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            tracker_config: Tracker configuration file
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.tracker_config = tracker_config
        print(f"[DETECTOR] Loaded YOLO model: {model_path}")
    
    def track_people(self, source, stream: bool = True) -> object:
        """
        Start tracking people in video stream.
        
        Args:
            source: Video source (camera index or file path)
            stream: Whether to return streaming results
            
        Returns:
            Generator of tracking results
        """
        return self.model.track(
            source=source,
            stream=stream,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            classes=[config.PERSON_CLASS_ID],  # Only detect persons
            tracker=self.tracker_config,
            persist=True,  # Keep track IDs across frames
            verbose=False
        )
    
    def extract_detections(self, result) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Extract bounding boxes and track IDs from YOLO result.
        
        Args:
            result: YOLO tracking result
            
        Returns:
            Tuple of (boxes_xyxy, track_ids) or (None, None) if no detections
        """
        if result.boxes is None or len(result.boxes) == 0:
            return None, None
        
        try:
            # Extract bounding boxes
            boxes_xyxy = result.boxes.xyxy.cpu().numpy()
            
            # Extract track IDs if available
            track_ids = None
            if result.boxes.id is not None:
                # Convert track IDs safely without astype
                raw_ids = result.boxes.id.cpu().numpy()
                track_ids = np.array([int(tid) for tid in raw_ids])
                
        except AttributeError:
            # Fallback for different YOLO versions
            boxes_xyxy = np.asarray(result.boxes.xyxy)
            if result.boxes.id is not None:
                raw_ids = np.asarray(result.boxes.id)
                track_ids = np.array([int(tid) for tid in raw_ids])
            else:
                track_ids = None
        
        return boxes_xyxy, track_ids
    
    def get_frame(self, result) -> np.ndarray:
        """
        Extract the original frame from YOLO result.
        
        Args:
            result: YOLO tracking result
            
        Returns:
            Original frame as numpy array
        """
        return result.orig_img.copy()
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold"""
        self.conf_threshold = threshold
        print(f"[DETECTOR] Updated confidence threshold to {threshold}")
    
    def get_detection_count(self, result) -> int:
        """Get number of people detected in current frame"""
        if result.boxes is None:
            return 0
        return len(result.boxes)