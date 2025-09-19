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

# Serial communication
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[SERIAL] Warning: pyserial not installed. Install with: pip install pyserial")

# Model URLs and paths
POSE_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
POSE_PATH = "pose_landmarker_lite.task"

HAND_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
HAND_PATH = "hand_landmarker.task"

GESTURE_URL = "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task"
GESTURE_PATH = "gesture_recognizer.task"

# Serial communication configuration
SERIAL_BAUD_RATE = 115200  # Change to your desired baud rate
SERIAL_PORT = "COM10"  # Default COM port (change to your Arduino port)
SERIAL_TIMEOUT = 0.1  # 100ms timeout
SERIAL_COMMAND_MAP = {
    None: 0,           # Default/no command
    "FORWARD": 1,      # Forward movement  
    "RIGHT": 2,        # Right movement
    "BACKWARD": 3,     # Backward movement
    "LEFT": 4,         # Left movement
    "BUTTON_A": 5,     # Button A
    "BUTTON_B": 6,     # Button B  
    "BUTTON_C": 7,     # Button C
    "PAUSE": 0         # Pause maps to default
}

# Direction control configuration - Dynamic gesture mapping
def load_gesture_mappings():
    """Load gesture mappings from configuration file"""
    import json
    import os
    
    # Default mappings (all gestures can map to any command)
    default_mappings = {
        "Open_Palm": "FORWARD",
        "Closed_Fist": "BACKWARD",
        "Thumb_Up": "BUTTON_A", 
        "Thumb_Down": "BUTTON_B",
        "Pointing_Up": "BUTTON_C",
        "Right_Elbow_Extended": "RIGHT",
        "Right_Elbow_Bent": "LEFT"
    }
    
    # Try to load from runtime config file
    config_file = "runtime_gesture_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                user_mappings = config_data.get("gesture_mappings", {})
                
                # Validate that user mappings has the essential gestures
                if user_mappings and len(user_mappings) > 0:
                    print(f"[DIRECTION] Loaded custom gesture mappings from {config_file}")
                    return user_mappings
                else:
                    print(f"[DIRECTION] Custom mappings file empty, using defaults")
        except Exception as e:
            print(f"[DIRECTION] Error loading custom mappings: {e}, using defaults")
    
    print("[DIRECTION] Using default gesture mappings")
    return default_mappings

# Load gesture mappings (will be reloaded when controller is initialized)
GESTURE_MAPPINGS = load_gesture_mappings()

class SerialController:
    """
    Handles serial communication for streaming gesture commands.
    Streams command codes at 115200 baud rate.
    """
    
    def __init__(self, port: str = None, baud_rate: int = SERIAL_BAUD_RATE):
        """
        Initialize serial controller.
        
        Args:
            port: Serial port (default: SERIAL_PORT from config)
            baud_rate: Communication baud rate (default: SERIAL_BAUD_RATE from config)
        """
        self.serial_port = None
        self.port = port
        self.baud_rate = baud_rate
        self.last_command_code = 0  # Track last sent command to avoid spam
        self.last_default_send_time = 0.0  # Track when we last sent default command
        self.default_send_interval = 0.5  # Send default every 500ms when no commands
        
        if not SERIAL_AVAILABLE:
            print("[SERIAL] pyserial not available - serial communication disabled")
            return
        
        # Use default port if not specified
        if port is None:
            port = SERIAL_PORT
            print(f"[SERIAL] Using default port: {port}")
        
        # Try to auto-detect if default port fails
        if not self._test_port(port):
            print(f"[SERIAL] Default port {port} not available, trying auto-detection...")
            detected_port = self._auto_detect_port()
            if detected_port:
                port = detected_port
        
        if port:
            self._connect(port)
        else:
            print("[SERIAL] No serial port specified - serial communication disabled")
            print("[SERIAL] To enable: specify port in config or auto-detection")
    
    def _auto_detect_port(self) -> Optional[str]:
        """Try to auto-detect available serial ports"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            
            if ports:
                # Prefer Arduino/microcontroller ports
                for port in ports:
                    description = port.description.lower()
                    if any(keyword in description for keyword in ['arduino', 'usb', 'serial']):
                        print(f"[SERIAL] Auto-detected port: {port.device} ({port.description})")
                        return port.device
                
                # Fallback to first available port
                first_port = ports[0]
                print(f"[SERIAL] Using first available port: {first_port.device} ({first_port.description})")
                return first_port.device
            else:
                print("[SERIAL] No serial ports detected")
                return None
                
        except Exception as e:
            print(f"[SERIAL] Port detection error: {e}")
            return None
    
    def _test_port(self, port: str) -> bool:
        """Test if a port is available"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            return any(p.device == port for p in ports)
        except:
            return False
    
    def _connect(self, port: str):
        """Connect to serial port"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=SERIAL_TIMEOUT,
                write_timeout=SERIAL_TIMEOUT
            )
            print(f"[SERIAL] Connected to {port} at {self.baud_rate} baud")
            
            # Send initial default command
            self.send_command_code(0)
            
        except Exception as e:
            print(f"[SERIAL] Failed to connect to {port}: {e}")
            print("[SERIAL] Serial communication disabled")
            self.serial_port = None
    
    def send_command_code(self, command_code: int, force: bool = False):
        """
        Send command code to serial port.
        
        Args:
            command_code: Integer command code (0-7)
            force: Force send even if same as last command (for reset scenarios)
        """
        if not self.serial_port or not self.serial_port.is_open:
            return
        
        # Only send if command changed to reduce serial traffic (unless forced)
        if command_code != self.last_command_code or force:
            try:
                # Send as ASCII character (like send.py)
                command_str = str(command_code)
                print(f"[SERIAL] Before Sending command: '{command_str}' (ASCII: {ord(command_str)})")
                self.serial_port.write(command_str.encode())  # Send ASCII character
                print(f"[SERIAL] After Sending command: '{command_str}' (ASCII: {ord(command_str)})")
                self.serial_port.flush()  # Ensure immediate transmission
                
                self.last_command_code = command_code
                
            except Exception as e:
                print(f"[SERIAL] Send error: {e}")
                # Try to reconnect on error
                self._reconnect()
    
    def send_commands(self, fb_command: Optional[str], lr_command: Optional[str], button_states: Dict):
        """
        Send movement and button commands via serial.
        Priority: Button > Forward/Backward > Left/Right > Default
        
        Args:
            fb_command: Forward/backward command
            lr_command: Left/right command  
            button_states: Dictionary of button states
        """
        import time
        current_time = time.time()
        
        # Check for button commands first (highest priority)
        for button_name, button_state in button_states.items():
            if button_state is not None:
                command_code = SERIAL_COMMAND_MAP.get(button_state, 0)
                self.send_command_code(command_code)
                return
        
        # Check for forward/backward commands (medium priority)
        if fb_command and fb_command in SERIAL_COMMAND_MAP:
            command_code = SERIAL_COMMAND_MAP[fb_command]
            self.send_command_code(command_code)
            return
        
        # Check for left/right commands (lower priority)
        if lr_command and lr_command in SERIAL_COMMAND_MAP:
            command_code = SERIAL_COMMAND_MAP[lr_command]
            self.send_command_code(command_code)
            return
        
        # No commands - send default periodically to ensure connection is alive
        if (current_time - self.last_default_send_time) >= self.default_send_interval:
            self.send_command_code(0)
            self.last_default_send_time = current_time
    
    def _reconnect(self):
        """Try to reconnect to serial port"""
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
        
        if self.port:
            print(f"[SERIAL] Attempting to reconnect to {self.port}...")
            self._connect(self.port)
    
    def close(self):
        """Close serial connection"""
        if self.serial_port and self.serial_port.is_open:
            try:
                # Send default command before closing
                self.send_command_code(0)
                self.serial_port.close()
                print("[SERIAL] Serial connection closed")
            except Exception as e:
                print(f"[SERIAL] Error closing connection: {e}")
    
    def is_connected(self) -> bool:
        """Check if serial port is connected"""
        return self.serial_port is not None and self.serial_port.is_open
    
    def send_heartbeat(self):
        """Send a heartbeat/default command to verify connection"""
        self.send_command_code(0)
        print("[SERIAL] Heartbeat sent (command: 0)")
    
    def get_connection_info(self) -> str:
        """Get connection status information"""
        if not self.serial_port:
            return "Not connected"
        elif self.serial_port.is_open:
            return f"Connected to {self.port} at {self.baud_rate} baud"
        else:
            return f"Port {self.port} closed"
    
    def force_reset(self):
        """Force reset the serial controller state and send default command"""
        self.last_command_code = -1  # Force different from 0
        self.send_command_code(0, force=True)
        print("[SERIAL] Force reset - sent default command '0'")

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
    
    def __init__(self, serial_port: str = None):
        """Initialize the direction controller with MediaPipe models and serial communication"""
        self.initialize_models()
        
        # Load current gesture mappings
        self.gesture_mappings = load_gesture_mappings()
        
        # Initialize serial communication
        self.serial_controller = SerialController(port=serial_port)
        
        # Direction control state
        self.last_fb = None
        self.last_lr = None
        self.last_print_time = 0.0
        self.last_fb_seen_time = 0.0
        
        # Button control state
        self.button_states = {
            'button_a': None,
            'button_b': None,
            'button_c': None
        }
        
        # Right elbow angle smoothing
        self.right_angle_buf = deque(maxlen=ANGLE_SMOOTH_N)
        
        # Timestamp for MediaPipe VIDEO mode
        self.start_time = time.perf_counter()
        
        print("[DIRECTION] Direction controller initialized")
        print("[DIRECTION] Using custom gesture mappings:")
        
        # Print current forward/backward mappings
        fb_mappings = []
        for gesture, command in self.gesture_mappings.items():
            if command in ["FORWARD", "BACKWARD"]:
                fb_mappings.append(f"{gesture}={command}")
        if fb_mappings:
            print(f"[DIRECTION] Forward/Backward: {', '.join(fb_mappings)}")
        
        # Print current left/right mappings
        lr_mappings = []
        for gesture, command in self.gesture_mappings.items():
            if command in ["LEFT", "RIGHT"]:
                lr_mappings.append(f"{gesture}={command}")
        if lr_mappings:
            print(f"[DIRECTION] Left/Right: {', '.join(lr_mappings)}")
    
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
    
    def analyze_locked_person(self, frame: np.ndarray, person_bbox, main_gesture_results=None) -> Optional[Dict]:
        """
        Analyze the locked person's pose and gestures for directional control.
        
        Args:
            frame: Full frame image
            person_bbox: Bounding box of the locked person [x1, y1, x2, y2]
            main_gesture_results: Gesture results from main detector to avoid conflicts
            
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
            # Run MediaPipe POSE analysis on cropped region (still needed for elbow angle)
            pose_result = self.pose_detector.detect_for_video(mp_img, ts_ms)
            
            # Analyze pose for left/right control
            lr_command = self._analyze_pose_for_lr(pose_result, person_crop.shape)
            
            # Use main gesture results if provided (to avoid conflicts with unlocking)
            fb_command = None
            if main_gesture_results:
                fb_command = self._analyze_main_gestures_for_fb(main_gesture_results, current_time)
            
            # Analyze button gestures from main gesture results
            self._analyze_button_gestures(main_gesture_results, current_time)
            
            # Check for command changes and print
            self._handle_command_output(fb_command, lr_command, current_time)
            
            return {
                'forward_backward': fb_command,
                'left_right': lr_command,
                'button_states': self.button_states.copy(),
                'crop_region': (crop_x1, crop_y1, crop_x2, crop_y2),
                'pose_landmarks': pose_result.pose_landmarks[0] if pose_result.pose_landmarks else None
            }
            
        except Exception as e:
            print(f"[DIRECTION] Analysis error: {e}")
            return None
    
    def _analyze_pose_for_lr(self, pose_result, crop_shape) -> Optional[str]:
        """Analyze pose landmarks for left/right control based on elbow angles"""
        if not pose_result.pose_landmarks:
            return self.last_lr
        
        landmarks = pose_result.pose_landmarks[0]
        h, w = crop_shape[:2]
        
        try:
            # Check both right and left elbow based on user configuration
            best_command = None
            
            # Right arm landmarks: shoulder(12) -> elbow(14) -> wrist(16)
            right_shoulder = to_px(landmarks[12], w, h)
            right_elbow = to_px(landmarks[14], w, h)
            right_wrist = to_px(landmarks[16], w, h)
            
            # Calculate right elbow angle
            right_angle = angle_3pts(right_shoulder, right_elbow, right_wrist)
            
            if right_angle is not None:
                # Smooth the angle
                self.right_angle_buf.append(right_angle)
                smoothed_angle = sum(self.right_angle_buf) / len(self.right_angle_buf)
                
                # Determine gesture based on angle
                if smoothed_angle > LR_THRESHOLD:
                    right_gesture = "Right_Elbow_Extended"
                else:
                    right_gesture = "Right_Elbow_Bent"
                
                # Check if this gesture maps to a command
                mapped_command = self.gesture_mappings.get(right_gesture)
                if mapped_command in ["LEFT", "RIGHT", "PAUSE"]:
                    best_command = mapped_command
            
            # Left arm landmarks: shoulder(11) -> elbow(13) -> wrist(15)
            try:
                left_shoulder = to_px(landmarks[11], w, h)
                left_elbow = to_px(landmarks[13], w, h)
                left_wrist = to_px(landmarks[15], w, h)
                
                # Calculate left elbow angle
                left_angle = angle_3pts(left_shoulder, left_elbow, left_wrist)
                
                if left_angle is not None:
                    # Determine gesture based on angle
                    if left_angle > LR_THRESHOLD:
                        left_gesture = "Left_Elbow_Extended"
                    else:
                        left_gesture = "Left_Elbow_Bent"
                    
                    # Check if this gesture maps to a command (prioritize if no right command)
                    mapped_command = self.gesture_mappings.get(left_gesture)
                    if mapped_command in ["LEFT", "RIGHT", "PAUSE"] and not best_command:
                        best_command = mapped_command
                        
            except (IndexError, AttributeError):
                pass  # Left arm not visible
                
            return best_command if best_command else self.last_lr
            
        except (IndexError, AttributeError):
            pass
        
        return self.last_lr
    
    def _analyze_gestures_for_fb(self, gesture_result, current_time) -> Optional[str]:
        """Analyze LEFT HAND gestures for forward/backward control"""
        if not gesture_result.gestures or not gesture_result.handedness:
            # Hold last command briefly if no gesture detected
            if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
                return self.last_fb
            return None
        
        # Find left hand gestures specifically
        left_hand_gesture = None
        left_hand_score = 0.0
        
        # Iterate through detected hands to find left hand
        for i, (hand_gestures, handedness_list) in enumerate(zip(gesture_result.gestures, gesture_result.handedness)):
            if not hand_gestures or not handedness_list:
                continue
            
            # Check if this is the left hand
            handedness = handedness_list[0]  # First (and usually only) handedness result
            if handedness.category_name.lower() == "left":
                # Find best gesture for left hand
                for gesture in hand_gestures:
                    if gesture.score > left_hand_score:
                        left_hand_score = gesture.score
                        left_hand_gesture = gesture
                break  # Found left hand, no need to check others
        
        if left_hand_gesture:
            gesture_name = left_hand_gesture.category_name
            # Use dynamic gesture mappings instead of hardcoded LEFT_HAND_GESTURE_TO_FB
            mapped_command = self.gesture_mappings.get(gesture_name)
            
            if mapped_command and mapped_command in ["FORWARD", "BACKWARD", "PAUSE"]:
                self.last_fb_seen_time = current_time
                print(f"[DIRECTION] Left hand {gesture_name} -> {mapped_command}")
                return mapped_command
        
        # Hold last command briefly
        if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
            return self.last_fb
        
        return None
    
    def _analyze_main_gestures_for_fb(self, main_gesture_results, current_time) -> Optional[str]:
        """
        Analyze gestures from main detector for forward/backward control.
        Uses the main gesture detection results to avoid conflicts with unlocking.
        """
        if not main_gesture_results or 'all_hands_data' not in main_gesture_results:
            # Hold last command briefly if no gesture detected
            if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
                return self.last_fb
            return None
        
        all_hands_data = main_gesture_results['all_hands_data']
        
        # Look for any hand gestures that map to forward/backward
        best_gesture = None
        best_score = 0.0
        best_command = None
        
        for hand_data in all_hands_data:
            gesture_name = hand_data.get('gesture', 'None')
            score = hand_data.get('score', 0.0)
            
            # Check if this gesture maps to a forward/backward command
            mapped_command = self.gesture_mappings.get(gesture_name)
            if mapped_command in ["FORWARD", "BACKWARD", "PAUSE"] and score > best_score:
                best_score = score
                best_gesture = gesture_name
                best_command = mapped_command
        
        if best_gesture and best_score > 0.5:  # Minimum confidence
            self.last_fb_seen_time = current_time
            print(f"[DIRECTION] Hand {best_gesture} -> {best_command}")
            return best_command
        
        # Hold last command briefly
        if (current_time - self.last_fb_seen_time) <= FB_HOLD_SECONDS:
            return self.last_fb
        
        return None
    
    def _analyze_button_gestures(self, main_gesture_results, current_time) -> None:
        """Analyze gestures for button commands (BUTTON_A, BUTTON_B, BUTTON_C)"""
        if not main_gesture_results or 'all_hands_data' not in main_gesture_results:
            # No gestures detected, reset button states
            self.button_states = {'button_a': None, 'button_b': None, 'button_c': None}
            return
        
        all_hands_data = main_gesture_results['all_hands_data']
        
        # Reset button states
        new_button_states = {'button_a': None, 'button_b': None, 'button_c': None}
        
        # Check each hand for gestures mapped to button commands
        for hand_data in all_hands_data:
            gesture_name = hand_data.get('gesture', 'None')
            score = hand_data.get('score', 0.0)
            
            if score < 0.5:  # Minimum confidence for button detection
                continue
            
            # Check what command this gesture is mapped to
            mapped_command = self.gesture_mappings.get(gesture_name, 'NONE')
            
            if mapped_command == 'BUTTON_A':
                new_button_states['button_a'] = 'BUTTON_A'
                print(f"[DIRECTION] Button A: {gesture_name} -> BUTTON_A")
            elif mapped_command == 'BUTTON_B':
                new_button_states['button_b'] = 'BUTTON_B'
                print(f"[DIRECTION] Button B: {gesture_name} -> BUTTON_B")
            elif mapped_command == 'BUTTON_C':
                new_button_states['button_c'] = 'BUTTON_C'
                print(f"[DIRECTION] Button C: {gesture_name} -> BUTTON_C")
        
        # Update button states and GUI if states changed
        if self.button_states != new_button_states:
            self.button_states = new_button_states
            print(f"[DIRECTION] Button states updated: {self.button_states}")
            
            # Send button commands immediately via serial
            self.serial_controller.send_commands(self.last_fb, self.last_lr, self.button_states)
            
            self._update_button_gui()
    
    def _update_button_gui(self):
        """Update GUI with current button states"""
        try:
            from direction_gui import direction_gui
            # Update GUI with current movement commands and button states
            direction_gui.update_commands(self.last_fb, self.last_lr, self.button_states)
        except ImportError:
            pass  # GUI not available
    
    def _handle_command_output(self, fb_command: Optional[str], lr_command: Optional[str], current_time: float):
        """Handle updating GUI, serial output, and minimal console output for direction commands"""
        if (fb_command != self.last_fb) or (lr_command != self.last_lr):
            if (current_time - self.last_print_time) >= PRINT_COOLDOWN:
                fb_text = fb_command if fb_command is not None else "None"
                lr_text = lr_command if lr_command is not None else "None"
                
                # Simple console output - just the commands
                print(f"{fb_text}, {lr_text}")
                
                # Send commands via serial
                self.serial_controller.send_commands(fb_command, lr_command, self.button_states)
                
                # Update GUI if available
                try:
                    from direction_gui import direction_gui
                    direction_gui.update_commands(fb_command, lr_command, self.button_states)
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
        self.button_states = {'button_a': None, 'button_b': None, 'button_c': None}
        self.right_angle_buf.clear()
        
        # Force reset serial controller and send default command
        self.serial_controller.force_reset()
        
        print("[DIRECTION] Direction control state reset")
    
    def cleanup(self):
        """Cleanup resources including serial connection"""
        self.reset_state()
        self.serial_controller.close()
        print("[DIRECTION] Direction controller cleanup completed")
    
    def is_serial_connected(self) -> bool:
        """Check if serial communication is active"""
        return self.serial_controller.is_connected()
    
    def send_serial_heartbeat(self):
        """Send a heartbeat to verify serial connection"""
        self.serial_controller.send_heartbeat()
    
    def get_serial_info(self) -> str:
        """Get serial connection information"""
        return self.serial_controller.get_connection_info()