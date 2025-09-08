# config.py - All constants and settings

# Model paths and URLs
GESTURE_URL = "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task"
GESTURE_PATH = "gesture_recognizer.task"
YOLO_WEIGHTS = "yolov8n.pt"

# Detection settings
PERSON_CLASS_ID = 0  # COCO 'person' class
DEFAULT_CONF = 0.5   # YOLO confidence threshold
DEFAULT_IOU = 0.5    # YOLO IoU threshold

# Gesture settings
DEFAULT_GESTURE_CONF = 0.50  # Minimum confidence for thumbs-up
MAX_HANDS = 4                # Maximum hands to detect

# ==============================================================================
# LOCKING MODE CONFIGURATION - CHANGE THIS LINE TO SWITCH MODES
# ==============================================================================
# Available modes: "FIST_PALM" or "POINTING_UP"
LOCKING_MODE = "FIST_PALM"  # <-- CODER CHANGES THIS LINE TO SWITCH
# ==============================================================================

# Fist + Palm proximity-based locking settings (only used if LOCKING_MODE = "FIST_PALM")
FIST_PALM_MIN_CONFIDENCE = 0.45        # Minimum confidence for each gesture
FIST_PALM_MAX_DISTANCE_PIXELS = 400      # Max pixels between hand centers
FIST_PALM_MAX_DISTANCE_RATIO = 0.30      # Max distance as ratio of frame diagonal
FIST_PALM_REQUIRED_HANDS = 2             # Must detect exactly 2 hands

# ReID settings for persistent tracking
DEFAULT_SIM_THRESH = 0.30    # Base similarity threshold (not used directly)
DEFAULT_LOSS_TIMEOUT = 15.0  # Seconds before auto-unlock (CHANGED from 5.0 to 15.0)
HIGH_CONFIDENCE_THRESH = 0.75 # High confidence threshold for persistent ReID matching
PERSISTENT_REID_LOCK_THRESH = 0.75   # Threshold for recognizing locked person
PERSISTENT_REID_UPDATE_THRESH = 0.80 # Threshold for updating person profile
MAX_LOW_MATCHES = 5          # Max consecutive low confidence matches
EXCLUSIVE_MODE_SIM_THRESH = 0.65  # Higher threshold for exclusive mode matching

# Drawing colors (BGR format)
GREEN = (0, 200, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLUE = (255, 0, 0)
YELLOW = (0, 255, 255)
CYAN = (255, 255, 0)
GRAY = (100, 100, 100)

# UI settings
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_TRACKER = "bytetrack.yaml"

# Gesture association settings
BOX_EXPANSION_FACTOR = 0.4   # Expand bounding box by 40%
MAX_GESTURE_DISTANCE = 0.15  # Max distance as fraction of diagonal

# Hand landmark connections for drawing
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (0, 9), (9, 10), (10, 11), (11, 12),
    # Ring finger
    (0, 13), (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20)
]