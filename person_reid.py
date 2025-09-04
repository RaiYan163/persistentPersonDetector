# person_reid.py - Person re-identification using OSNet

import cv2
import numpy as np
from typing import Optional
import config
from utils import to_np_xyxy

# Check for torchreid availability
try:
    import torchreid
    HAS_REID = True
    print(f"[REID] torchreid version: {torchreid.__version__}")
except ImportError as e:
    HAS_REID = False
    print(f"[REID] torchreid not available: {e}")

class PersonReID:
    """
    Handles person re-identification using deep learning features.
    Uses OSNet model from torchreid for feature extraction.
    """
    
    def __init__(self, device: str = "cpu", model_name: str = "osnet_x0_25"):
        """
        Initialize person re-identification system.
        
        Args:
            device: Device to run model on ('cpu' or 'cuda')
            model_name: Name of the ReID model to use
        """
        self.device = device
        self.model_name = model_name
        self.use_reid = False
        self.extractor = None
        
        if not HAS_REID:
            raise RuntimeError(
                "torchreid is required for person re-identification!\n"
                "Install with: pip install torchreid"
            )
        
        self._load_model()
    
    def _load_model(self):
        """Load the OSNet model for feature extraction"""
        try:
            print(f"[REID] Loading {self.model_name} on {self.device}...")
            self.extractor = torchreid.utils.FeatureExtractor(
                model_name=self.model_name, 
                device=self.device
            )
            self.use_reid = True
            print(f"[REID] Model loaded successfully")
        except Exception as e:
            print(f"[REID] Failed to load model: {e}")
            raise RuntimeError(f"Failed to load ReID model: {e}")
    
    def extract_features(self, frame: np.ndarray, bbox) -> np.ndarray:
        """
        Extract ReID features from a person bounding box.
        
        Args:
            frame: Input frame
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            
        Returns:
            Feature vector as numpy array
        """
        if not self.use_reid:
            return np.zeros(512, dtype=np.float32)
        
        # Crop person with padding
        crop = self._crop_person(frame, bbox, pad_ratio=0.15)
        if crop is None or crop.size == 0:
            return np.zeros(512, dtype=np.float32)
        
        # Convert to RGB for model
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        
        # Extract features
        features = self.extractor([rgb_crop])  # Returns (1, feature_dim) array
        
        # Normalize features - handle both tensor and numpy
        return self._l2_normalize(features[0])
    
    def _crop_person(self, frame: np.ndarray, bbox, pad_ratio: float = 0.15) -> Optional[np.ndarray]:
        """
        Crop person region from frame with padding.
        
        Args:
            frame: Input frame
            bbox: Bounding box coordinates
            pad_ratio: Padding ratio (0.15 = 15% padding)
            
        Returns:
            Cropped person image or None if invalid
        """
        H, W = frame.shape[:2]
        
        # Convert bbox to numpy array
        bbox = to_np_xyxy(bbox)
        if len(bbox) < 4:
            return None
        
        # Extract coordinates and convert to integers safely
        x1, y1, x2, y2 = bbox[:4]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Add padding
        pad_w = int((x2 - x1) * pad_ratio)
        pad_h = int((y2 - y1) * pad_ratio)
        
        # Ensure coordinates are within frame bounds
        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)  
        x2 = min(W - 1, x2 + pad_w)
        y2 = min(H - 1, y2 + pad_h)
        
        # Check if crop is valid
        if x2 <= x1 or y2 <= y1:
            return None
        
        return frame[y1:y2, x1:x2]
    
    def _l2_normalize(self, features) -> np.ndarray:
        """
        L2 normalize feature vector - handles both tensors and numpy arrays
        """
        # Convert to numpy if it's a tensor
        if hasattr(features, 'detach'):
            features = features.detach().cpu().numpy()
        
        # Ensure it's a numpy array with float32 dtype
        features = np.array(features, dtype=np.float32)
        
        # Compute L2 norm and normalize
        norm = np.linalg.norm(features) + 1e-12
        normalized = features / norm
        
        return normalized
    
    @staticmethod
    def compute_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compute cosine similarity between two feature vectors.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays if needed and ensure float32
        f1 = np.array(features1, dtype=np.float32)
        f2 = np.array(features2, dtype=np.float32)
        
        # Normalize vectors
        f1_norm = np.linalg.norm(f1) + 1e-12
        f2_norm = np.linalg.norm(f2) + 1e-12
        
        f1 = f1 / f1_norm
        f2 = f2 / f2_norm
        
        # Compute dot product (cosine similarity)
        similarity = np.dot(f1, f2)
        
        return float(similarity)
    
    def is_available(self) -> bool:
        """Check if ReID system is available and loaded"""
        return self.use_reid and self.extractor is not None
    
    def get_feature_dim(self) -> int:
        """Get dimension of feature vectors"""
        return 512  # OSNet feature dimension
    
    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'available': self.use_reid,
            'feature_dim': self.get_feature_dim()
        }