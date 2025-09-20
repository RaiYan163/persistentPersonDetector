# main.py - Main application entry point with persistent ReID and direction control

import argparse
import time
import cv2
import config
class GestureHoldTimer:
    """
    Manages gesture hold timing with countdown display for locking/unlocking.
    Requires gestures to be held for a specified duration before triggering.
    """
    
    def __init__(self, hold_duration: float = config.GESTURE_HOLD_DURATION):
        self.hold_duration = hold_duration
        self.reset()
    
    def reset(self):
        """Reset the timer state"""
        self.start_time = None
        self.is_active = False
        self.gesture_type = None
        self.last_update_time = 0
    
    def start_timing(self, gesture_type: str):
        """Start timing a gesture"""
        current_time = time.time()
        
        if not self.is_active:
            # Start new timing
            self.start_time = current_time
            self.is_active = True
            self.gesture_type = gesture_type
            self.last_update_time = current_time
            print(f"[TIMER] Started {gesture_type} hold timer - hold for {self.hold_duration:.1f}s")
        
        return False  # Not completed yet
    
    def update(self, gesture_detected: bool) -> tuple[bool, float]:
        """
        Update timer state.
        
        Returns:
            (completed, remaining_time)
        """
        if not self.is_active:
            return False, self.hold_duration
        
        if not gesture_detected:
            # Gesture lost, reset timer
            print(f"[TIMER] {self.gesture_type} gesture lost - resetting timer")
            self.reset()
            return False, self.hold_duration
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        remaining = max(0, self.hold_duration - elapsed)
        
        # Update countdown display every 100ms
        if (current_time - self.last_update_time) >= config.COUNTDOWN_UPDATE_INTERVAL:
            if remaining > 0:
                print(f"[TIMER] {self.gesture_type} hold: {remaining:.1f}s remaining")
            self.last_update_time = current_time
        
        if elapsed >= self.hold_duration:
            # Timer completed
            print(f"[TIMER] {self.gesture_type} hold completed!")
            self.reset()
            return True, 0.0
        
        return False, remaining
    
    def get_progress(self) -> float:
        """Get progress as ratio 0.0-1.0"""
        if not self.is_active or not self.start_time:
            return 0.0
        
        elapsed = time.time() - self.start_time
        return min(1.0, elapsed / self.hold_duration)

# Serial monitor thread removed - focusing only on button state changes

from person_detector import PersonDetector
from gesture_detector import GestureDetector
from person_reid import PersonReID
from target_tracker import TargetTracker
from direction_controller import DirectionController
from direction_gui import direction_gui
from utils import (
    associate_gesture_to_person,
    associate_fist_palm_to_person,
    associate_dual_victory_to_person,
    draw_hand_landmarks, 
    draw_person_boxes,
    draw_locked_target, 
    draw_hud
)
from button_state_shared import (
    get_button_state,
    set_button_state,
    set_button_pressed,
    reset_button_state,
    get_button_state_info,
    set_button_position,
    set_multiple_buttons,
    get_button_position,
    BUTTON_POSITIONS
)
from button_state_server import start_button_state_server, stop_button_state_server, get_server_status

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Person Lock System - Lock onto a person with pointing up gesture (PERSISTENT ReID TRACKING + DIRECTION CONTROL)"
    )
    
    # Video source
    parser.add_argument("--source", type=str, default=str(config.DEFAULT_CAMERA), 
                       help="Camera index or path to video file")
    
    # Detection parameters
    parser.add_argument("--conf", type=float, default=config.DEFAULT_CONF,
                       help="YOLO confidence threshold")
    parser.add_argument("--sim", type=float, default=config.DEFAULT_SIM_THRESH,
                       help="ReID similarity threshold (0-1)")
    parser.add_argument("--gesture_conf", type=float, default=config.DEFAULT_GESTURE_CONF,
                       help="Minimum confidence for gesture detection")
    
    # System parameters
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device for ReID model (cpu/cuda)")
    parser.add_argument("--tracker", type=str, default=config.DEFAULT_TRACKER,
                       help="YOLO tracker configuration")
    parser.add_argument("--loss_timeout", type=float, default=config.DEFAULT_LOSS_TIMEOUT,
                       help="Seconds before auto-unlock (now 15s)")
    
    # Display parameters
    parser.add_argument("--width", type=int, default=config.DEFAULT_WIDTH,
                       help="Display width")
    parser.add_argument("--height", type=int, default=config.DEFAULT_HEIGHT,
                       help="Display height")
    parser.add_argument("--fullscreen", action="store_true",
                       help="Start in fullscreen mode")
    
    # Serial communication removed - will be implemented from scratch
    
    # Debug options
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug output")
    
    return parser.parse_args()

class PersonLockSystem:
    """
    Main application class with persistent ReID tracking, pointing up gesture, and direction control.
    When locked, only the target person is visible and direction control is active.
    """
    
    def __init__(self, args):
        """Initialize the person lock system with persistent ReID, pointing up gesture, and direction control"""
        self.args = args
        self.setup_display()
        self.initialize_components()
        self.start_time = time.time()
        
        # Initialize direction controller (serial communication removed)
        self.direction_controller = DirectionController()
        
        # Initialize gesture hold timers
        self.lock_timer = GestureHoldTimer()
        self.unlock_timer = GestureHoldTimer()
        
        # Start the direction GUI
        direction_gui.start_gui()
        
        # Start button state server for external monitoring
        start_button_state_server()
        
        # Give server time to initialize
        time.sleep(0.1)
        
        # Test button state access
        current_button_state = get_button_state()
        print(f"[SYSTEM] Button state access test: {current_button_state.strip()}")
        
        print("[SYSTEM] Person Lock System initialized with PERSISTENT ReID tracking")
        print("[SYSTEM] Security: High-confidence persistent person identification")
        print("[SYSTEM] Features: Survives occlusions, prevents false positives, 15s timeout")
        
        # Display server status
        server_status = get_server_status()
        socket_status = "bound" if server_status['socket_bound'] else "starting"
        print(f"[SYSTEM] Button state server: {server_status['host']}:{server_status['port']} ({socket_status}, clients: {server_status['clients']})")
        print("[SYSTEM] Use 'python button_state_client.py' in another terminal to monitor button states")
        
        # Display current locking mode
        if config.LOCKING_MODE == "FIST_PALM":
            print(f"[SYSTEM] Locking Mode: FIST_PALM (Fist + Palm proximity-based)")
            print(f"[SYSTEM] Proximity thresholds: {config.FIST_PALM_MAX_DISTANCE_PIXELS}px OR {config.FIST_PALM_MAX_DISTANCE_RATIO*100:.0f}% of frame diagonal")
            print("[SYSTEM] Lock Gesture: FIST + PALM (close together)")
        else:
            print(f"[SYSTEM] Locking Mode: POINTING_UP (Original single-gesture)")
            print("[SYSTEM] Lock Gesture: POINTING UP (index finger pointing upward)")
        
        print("[SYSTEM] Unlock Gesture: VICTORY (peace sign)")
        print("[SYSTEM] DIRECTION CONTROL: Active when person is locked")
        print("[SYSTEM] Direction Commands: LEFT HAND (Palm=Forward, Fist=Backward), RIGHT ELBOW (angle=Left/Right)")
        print("[UI] Controls: 'r' = reset/unlock, 'q' = quit, 'f' = toggle fullscreen")
    
    def setup_display(self):
        """Setup OpenCV display window with proper aspect ratio"""
        self.window_name = "Person Lock System - PERSISTENT ReID + DIRECTION CONTROL"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        if self.args.fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, 
                                cv2.WINDOW_FULLSCREEN)
    
    def initialize_components(self):
        """Initialize all system components"""
        # Person detection
        self.detector = PersonDetector(
            model_path=config.YOLO_WEIGHTS,
            conf_threshold=self.args.conf,
            tracker_config=self.args.tracker
        )
        
        # Gesture recognition
        self.gesture_detector = GestureDetector(
            min_score=self.args.gesture_conf
        )
        
        # Person re-identification
        self.reid_system = PersonReID(device=self.args.device)
        
        # Target tracking with persistent ReID
        self.tracker = TargetTracker(
            reid_system=self.reid_system,
            similarity_threshold=self.args.sim,
            loss_timeout=self.args.loss_timeout
        )
    
    def run(self):
        """Main application loop"""
        source = 0 if self.args.source == "0" else self.args.source
        print(f"[SYSTEM] Starting with source: {source}")
        
        # Check camera resolution before starting
        if str(source).isdigit():
            self.check_camera_resolution(int(source))
        
        try:
            # Start tracking stream
            results_stream = self.detector.track_people(source)
            
            for result in results_stream:
                if not self.process_frame(result):
                    break
                    
        except KeyboardInterrupt:
            print("\n[SYSTEM] Interrupted by user")
        except Exception as e:
            print(f"[ERROR] System error: {e}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
        finally:
            direction_gui.stop_gui()  # Stop GUI when application exits
            self.direction_controller.cleanup()  # Cleanup direction controller
            stop_button_state_server()  # Stop button state server
            cv2.destroyAllWindows()
            print("[SYSTEM] Shutdown complete")
    
    def check_camera_resolution(self, camera_index: int):
        """Check and display actual camera resolution"""
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            print(f"[CAMERA] Native resolution: {width}x{height} @ {fps}fps")
            cap.release()
    
    def process_frame(self, detection_result) -> bool:
        """
        Process a single frame with persistent ReID filtering and direction control.
        
        Returns:
            bool: True to continue, False to exit
        """
        # Extract frame and ALL detections (before filtering)
        frame = self.detector.get_frame(detection_result)
        
        # Auto-size window to match frame on first run
        if not hasattr(self, '_window_sized'):
            h, w = frame.shape[:2]
            if not self.args.fullscreen:
                scale_factor = 1.5
                new_width = int(w * scale_factor)
                new_height = int(h * scale_factor)
                cv2.resizeWindow(self.window_name, new_width, new_height)
            self._window_sized = True
        
        # Get ALL detections (unfiltered)
        all_boxes_xyxy, all_track_ids = self.detector.extract_detections(detection_result)
        
        # Process gestures on the full frame (before filtering)
        timestamp_ms = int((time.time() - self.start_time) * 1000.0)
        gesture_results = self.gesture_detector.detect_gestures(frame, timestamp_ms)
        
        # Handle locking/unlocking logic with security checks
        self.handle_gesture_logic(frame, all_boxes_xyxy, all_track_ids, gesture_results)
        
        # CRITICAL: Apply PERSISTENT ReID filtering
        # This creates persistent person identity that survives occlusions and prevents false locking
        filtered_boxes, filtered_ids = self.tracker.filter_detections_persistent_reid(
            frame, all_boxes_xyxy, all_track_ids
        )
        
        # Direction control for locked person
        direction_result = None
        if self.tracker.is_locked and filtered_boxes is not None and len(filtered_boxes) > 0:
            # Analyze the locked person for direction control
            locked_person_bbox = filtered_boxes[0]  # First (and only) person in filtered results
            # Pass gesture results to avoid conflicts with unlocking gestures
            direction_result = self.direction_controller.analyze_locked_person(frame, locked_person_bbox, gesture_results)
        
        # Draw everything using FILTERED detections
        self.draw_frame(frame, filtered_boxes, filtered_ids, gesture_results, direction_result)
        
        # Handle user input
        return self.handle_input()
    
    def handle_gesture_logic(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """
        Handle locking and unlocking based on gestures with security checks.
        Uses ALL detections for gesture association, then applies security.
        """
        if not self.tracker.is_locked:
            # Try to lock with pointing up
            self.try_lock_target(frame, all_boxes_xyxy, all_track_ids, gesture_results)
        else:
            # Try to unlock with victory gesture - SECURE VERSION
            self.try_unlock_target_secure(frame, all_boxes_xyxy, all_track_ids, gesture_results)
    
    def try_lock_target(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """Try to lock onto a person using the configured locking mode"""
        if all_boxes_xyxy is None or len(all_boxes_xyxy) == 0:
            return
        
        # Mode switching: choose between FIST_PALM and POINTING_UP
        if config.LOCKING_MODE == "FIST_PALM":
            self._try_lock_with_fist_palm(frame, all_boxes_xyxy, all_track_ids, gesture_results)
        else:  # POINTING_UP mode (fallback)
            self._try_lock_with_pointing_up(frame, all_boxes_xyxy, all_track_ids, gesture_results)
    
    def _try_lock_with_fist_palm(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """Try to lock using fist+palm combination with hold timer"""
        fist_palm_result = gesture_results.get('fist_palm_combination', {})
        gesture_detected = fist_palm_result.get('detected', False)
        
        if not gesture_detected:
            # Reset timer if gesture not detected
            if self.lock_timer.is_active:
                self.lock_timer.reset()
            return
        
        # Start timer if gesture detected
        if not self.lock_timer.is_active:
            self.lock_timer.start_timing("FIST+PALM LOCK")
        
        # Update timer and check if completed
        timer_completed, remaining_time = self.lock_timer.update(gesture_detected)
        
        if not timer_completed:
            # Show countdown progress
            self._draw_lock_countdown(frame, fist_palm_result, remaining_time)
            return
        
        # Timer completed - proceed with locking
        # Get midpoint for person association
        midpoint_x, midpoint_y = fist_palm_result['midpoint']
        if midpoint_x is None or midpoint_y is None:
            return
        
        # Get hand landmarks for association
        all_hands_data = gesture_results.get('all_hands_data', [])
        if len(all_hands_data) < 2:
            return
        
        hand1_landmarks = all_hands_data[0]['landmarks']
        hand2_landmarks = all_hands_data[1]['landmarks']
        
        # Associate gesture combination to person
        person_idx = associate_fist_palm_to_person(
            midpoint_x, midpoint_y, hand1_landmarks, hand2_landmarks, 
            all_boxes_xyxy, frame.shape[:2]
        )
        
        if person_idx is not None:
            # Lock onto this specific person
            target_box = all_boxes_xyxy[person_idx]
            target_id = int(all_track_ids[person_idx]) if all_track_ids is not None else None
            
            self.tracker.lock_target(frame, target_box, target_id)
            
            print(f"[SYSTEM] PERSISTENT LOCK created for person with Track ID {target_id}")
            print(f"[SYSTEM] ReID-based persistent identity - survives occlusions and ID changes")
            print(f"[SYSTEM] High-confidence matching prevents false positive locking")
            print(f"[SYSTEM] DIRECTION CONTROL now active for locked person")
            print(f"[SYSTEM] Lock Method: FIST + PALM proximity-based (2s hold)")
            
            # Visual feedback for fist+palm lock
            cv2.circle(frame, (midpoint_x, midpoint_y), 25, config.GREEN, 4)
            cv2.putText(frame, "LOCKED!", (midpoint_x + 30, midpoint_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, config.GREEN, 3)
            
            # Draw line between hands to show combination
            if len(all_hands_data) >= 2 and hand1_landmarks and hand2_landmarks:
                hand1_center = hand1_landmarks[0]
                hand2_center = hand2_landmarks[0]
                cv2.line(frame, hand1_center, hand2_center, config.GREEN, 3)
    
    def _try_lock_with_pointing_up(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """Try to lock using pointing up gesture (fallback mode)"""
        pointing_up_list = gesture_results['pointing_up_list']
        
        if not pointing_up_list:
            return
        
        # Get best pointing up gesture
        best_pointing_up = self.gesture_detector.get_best_pointing_up(pointing_up_list)
        if not best_pointing_up:
            return
        
        # Associate gesture to person using ALL detections
        gesture_x, gesture_y = best_pointing_up['x'], best_pointing_up['y']
        person_idx = associate_gesture_to_person(
            gesture_x, gesture_y, all_boxes_xyxy, frame.shape[:2]
        )
        
        if person_idx is not None:
            # Lock onto this specific person
            target_box = all_boxes_xyxy[person_idx]
            target_id = int(all_track_ids[person_idx]) if all_track_ids is not None else None
            
            self.tracker.lock_target(frame, target_box, target_id)
            
            print(f"[SYSTEM] PERSISTENT LOCK created for person with Track ID {target_id}")
            print(f"[SYSTEM] ReID-based persistent identity - survives occlusions and ID changes")
            print(f"[SYSTEM] High-confidence matching prevents false positive locking")
            print(f"[SYSTEM] DIRECTION CONTROL now active for locked person")
            print(f"[SYSTEM] Lock Method: POINTING UP (fallback mode)")
            
            # Visual feedback
            cv2.circle(frame, (gesture_x, gesture_y), 25, config.GREEN, 4)
            cv2.putText(frame, "LOCKED!", (gesture_x + 30, gesture_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, config.GREEN, 3)
    
    def try_unlock_target_secure(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """
        SECURE VERSION: Try to unlock with dual victory gesture combination.
        Only unlocks if both victory gestures come from the locked person and are close together.
        This provides enhanced security through dual gesture requirement.
        """
        # ONLY use dual victory gesture (enhanced security - no fallback)
        dual_victory_result = gesture_results.get('dual_victory_combination', {})
        
        if dual_victory_result.get('detected', False):
            self._try_unlock_with_dual_victory(frame, all_boxes_xyxy, all_track_ids, dual_victory_result, gesture_results)
            return
        
        # No single victory fallback - only dual victory unlocking allowed
        # This ensures users must use both hands with victory gestures close together
        
        # Optional: Show debug message when single victory is detected but ignored
        victory_list = gesture_results['victory_list']
        if victory_list:
            print(f"[SECURITY] Single victory gesture detected but IGNORED - Dual victory required for unlocking")
    
    def _try_unlock_with_dual_victory(self, frame, all_boxes_xyxy, all_track_ids, dual_victory_result, gesture_results):
        """Try to unlock using dual victory gesture combination with hold timer"""
        gesture_detected = dual_victory_result.get('detected', False)
        
        if not gesture_detected:
            # Reset timer if gesture not detected
            if self.unlock_timer.is_active:
                self.unlock_timer.reset()
            return
        
        # Start timer if gesture detected
        if not self.unlock_timer.is_active:
            self.unlock_timer.start_timing("DUAL VICTORY UNLOCK")
        
        # Update timer and check if completed
        timer_completed, remaining_time = self.unlock_timer.update(gesture_detected)
        
        if not timer_completed:
            # Show countdown progress
            self._draw_unlock_countdown(frame, dual_victory_result, remaining_time)
            return
        
        # Timer completed - proceed with unlocking
        # Get midpoint for person association
        midpoint_x, midpoint_y = dual_victory_result['midpoint']
        if midpoint_x is None or midpoint_y is None:
            return
        
        # Get hand landmarks for association
        all_hands_data = gesture_results.get('all_hands_data', [])
        if len(all_hands_data) < 2:
            return
        
        hand1_landmarks = all_hands_data[0]['landmarks']
        hand2_landmarks = all_hands_data[1]['landmarks']
        
        # Associate gesture combination to person
        person_idx = associate_dual_victory_to_person(
            midpoint_x, midpoint_y, hand1_landmarks, hand2_landmarks, 
            all_boxes_xyxy, frame.shape[:2]
        )
        
        if person_idx is None:
            print(f"[SECURITY] Dual victory gesture not associated with any person")
            return
        
        # SECURITY CHECK: Verify dual victory gesture comes from locked target person
        # We use the midpoint location for this check
        is_from_target = self.tracker.is_target_person_at_location(
            frame, midpoint_x, midpoint_y, all_boxes_xyxy, all_track_ids
        )
        
        if is_from_target:
            state_info = self.tracker.get_state()
            person_id = state_info.get('person_id', 'Unknown')
            print(f"[SYSTEM] Dual victory gesture from {person_id}")
            print(f"[SYSTEM] UNLOCKING persistent ReID profile")
            print(f"[SYSTEM] DIRECTION CONTROL deactivated")
            print(f"[SYSTEM] Unlock Method: DUAL VICTORY (enhanced security, 2s hold)")
            
            # Reset direction controller state
            self.direction_controller.reset_state()
            
            self.tracker.unlock_target()
            
            # Visual feedback for dual victory unlock
            cv2.circle(frame, (midpoint_x, midpoint_y), 25, config.BLUE, 4)
            cv2.putText(frame, "UNLOCKED!", (midpoint_x + 30, midpoint_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, config.BLUE, 3)
            
            # Draw line between hands to show combination
            if len(all_hands_data) >= 2 and hand1_landmarks and hand2_landmarks:
                hand1_center = hand1_landmarks[0]
                hand2_center = hand2_landmarks[0]
                cv2.line(frame, hand1_center, hand2_center, config.BLUE, 3)
        else:
            print(f"[SECURITY] Dual victory gesture NOT from target person - IGNORING")
            print(f"[SECURITY] Only the locked person can unlock themselves")
    
    def draw_frame(self, frame, filtered_boxes, filtered_ids, gesture_results, direction_result=None):
        """
        Draw all visual elements on the frame using FILTERED detections.
        In persistent ReID mode, this will only show the target person when locked.
        """
        # Draw detected persons (filtered - only target when locked)
        if filtered_boxes is not None:
            if self.tracker.is_locked:
                # In locked mode, draw target with special styling
                draw_person_boxes(frame, filtered_boxes, filtered_ids, color=config.RED, thickness=4)
                if len(filtered_boxes) > 0:
                    # Draw "LOCKED" label
                    box = filtered_boxes[0]
                    x1, y1 = int(box[0]), int(box[1])
                    cv2.putText(frame, "TARGET (LOCKED) - DIRECTION CONTROL ACTIVE", (x1, max(0, y1 - 10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.RED, 3)
                    
                    # Draw direction control overlay
                    if direction_result:
                        crop_region = direction_result.get('crop_region')
                        if crop_region:
                            self.direction_controller.draw_direction_overlay(frame, direction_result, crop_region)
            else:
                # Normal mode - draw all people
                draw_person_boxes(frame, filtered_boxes, filtered_ids)
        
        # Draw hands and gestures
        self.draw_gestures(frame, gesture_results)
        
        # Draw HUD with persistent ReID and direction info
        self.draw_persistent_hud(frame)
        
        # Show frame
        cv2.imshow(self.window_name, frame)
    
    def draw_gestures(self, frame, gesture_results):
        """Draw hand landmarks and gesture information"""
        all_hands = gesture_results['all_hands_data']
        
        # Handle fist+palm combination display (when in FIST_PALM mode and not locked)
        if (config.LOCKING_MODE == "FIST_PALM" and not self.tracker.is_locked):
            fist_palm_result = gesture_results.get('fist_palm_combination', {})
            if fist_palm_result.get('detected', False):
                self.draw_fist_palm_combination(frame, gesture_results, fist_palm_result)
                return  # Skip individual hand drawing when showing combination
        
        # Handle dual victory combination display (when locked)
        if self.tracker.is_locked:
            dual_victory_result = gesture_results.get('dual_victory_combination', {})
            if dual_victory_result.get('detected', False):
                self.draw_dual_victory_combination(frame, gesture_results, dual_victory_result)
                return  # Skip individual hand drawing when showing combination
        
        for hand_data in all_hands:
            landmarks = hand_data['landmarks']
            if not landmarks:
                continue
            
            # Choose colors based on gesture and lock state
            if self.tracker.is_locked:
                # When locked, highlight victory gestures from target
                if hand_data['is_victory']:
                    color = config.BLUE
                    thickness = 3
                else:
                    color = config.GRAY
                    thickness = 1
            else:
                # When unlocked, highlight pointing up
                if hand_data['is_pointing_up']:
                    color = config.GREEN
                    thickness = 3
                elif hand_data['is_victory']:
                    color = config.BLUE  
                    thickness = 2
                else:
                    color = config.YELLOW
                    thickness = 1
            
            # Draw hand landmarks
            draw_hand_landmarks(frame, landmarks, color, thickness)
            
            # Draw gesture label
            if landmarks and hand_data['gesture'] != 'None':
                wrist_x, wrist_y = landmarks[0]
                gesture_text = f"{hand_data['gesture']}: {hand_data['score']:.2f}"
                cv2.putText(frame, gesture_text, (wrist_x + 10, wrist_y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def draw_fist_palm_combination(self, frame, gesture_results, fist_palm_result):
        """Draw special visualization for fist+palm combination"""
        all_hands_data = gesture_results.get('all_hands_data', [])
        
        if len(all_hands_data) < 2:
            return
        
        fist_hand_idx = fist_palm_result.get('fist_hand_idx')
        palm_hand_idx = fist_palm_result.get('palm_hand_idx')
        
        if fist_hand_idx is None or palm_hand_idx is None:
            return
        
        fist_hand = all_hands_data[fist_hand_idx]
        palm_hand = all_hands_data[palm_hand_idx]
        
        # Draw fist hand in red
        if fist_hand['landmarks']:
            draw_hand_landmarks(frame, fist_hand['landmarks'], config.RED, 3)
            wrist_pos = fist_hand['landmarks'][0]
            cv2.putText(frame, "FIST", (wrist_pos[0] + 15, wrist_pos[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.RED, 2)
        
        # Draw palm hand in green
        if palm_hand['landmarks']:
            draw_hand_landmarks(frame, palm_hand['landmarks'], config.GREEN, 3)
            wrist_pos = palm_hand['landmarks'][0]
            cv2.putText(frame, "PALM", (wrist_pos[0] + 15, wrist_pos[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.GREEN, 2)
        
        # Draw connection line between hands
        if fist_hand['landmarks'] and palm_hand['landmarks']:
            fist_center = fist_hand['landmarks'][0]
            palm_center = palm_hand['landmarks'][0]
            cv2.line(frame, fist_center, palm_center, config.YELLOW, 2)
        
        # Draw midpoint
        midpoint_x, midpoint_y = fist_palm_result['midpoint']
        if midpoint_x is not None and midpoint_y is not None:
            cv2.circle(frame, (midpoint_x, midpoint_y), 8, config.CYAN, -1)
        
        # Draw distance information
        distance_pixels = fist_palm_result.get('distance_pixels', 0)
        close_enough = fist_palm_result.get('close_enough', False)
        
        status_color = config.GREEN if close_enough else config.RED
        status_text = f"Distance: {distance_pixels:.0f}px {'READY' if close_enough else 'TOO FAR'}"
        
        if midpoint_x is not None and midpoint_y is not None:
            cv2.putText(frame, status_text, (midpoint_x - 50, midpoint_y + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
    
    def draw_dual_victory_combination(self, frame, gesture_results, dual_victory_result):
        """Draw special visualization for dual victory gesture combination"""
        all_hands_data = gesture_results.get('all_hands_data', [])
        
        if len(all_hands_data) < 2:
            return
        
        victory1_hand_idx = dual_victory_result.get('victory1_hand_idx')
        victory2_hand_idx = dual_victory_result.get('victory2_hand_idx')
        
        if victory1_hand_idx is None or victory2_hand_idx is None:
            return
        
        victory1_hand = all_hands_data[victory1_hand_idx]
        victory2_hand = all_hands_data[victory2_hand_idx]
        
        # Draw victory hand 1 in blue
        if victory1_hand['landmarks']:
            draw_hand_landmarks(frame, victory1_hand['landmarks'], config.BLUE, 3)
            wrist_pos = victory1_hand['landmarks'][0]
            cv2.putText(frame, "VICTORY", (wrist_pos[0] + 15, wrist_pos[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.BLUE, 2)
        
        # Draw victory hand 2 in cyan
        if victory2_hand['landmarks']:
            draw_hand_landmarks(frame, victory2_hand['landmarks'], config.CYAN, 3)
            wrist_pos = victory2_hand['landmarks'][0]
            cv2.putText(frame, "VICTORY", (wrist_pos[0] + 15, wrist_pos[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.CYAN, 2)
        
        # Draw connection line between hands
        if victory1_hand['landmarks'] and victory2_hand['landmarks']:
            victory1_center = victory1_hand['landmarks'][0]
            victory2_center = victory2_hand['landmarks'][0]
            cv2.line(frame, victory1_center, victory2_center, config.BLUE, 2)
        
        # Draw midpoint
        midpoint_x, midpoint_y = dual_victory_result['midpoint']
        if midpoint_x is not None and midpoint_y is not None:
            cv2.circle(frame, (midpoint_x, midpoint_y), 8, config.BLUE, -1)
        
        # Draw distance information
        distance_pixels = dual_victory_result.get('distance_pixels', 0)
        close_enough = dual_victory_result.get('close_enough', False)
        
        status_color = config.BLUE if close_enough else config.RED
        status_text = f"Dual Victory: {distance_pixels:.0f}px {'READY TO UNLOCK' if close_enough else 'TOO FAR'}"
        
        if midpoint_x is not None and midpoint_y is not None:
            cv2.putText(frame, status_text, (midpoint_x - 80, midpoint_y + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
    
    def _draw_lock_countdown(self, frame, fist_palm_result, remaining_time):
        """Draw countdown timer for fist+palm locking"""
        midpoint_x, midpoint_y = fist_palm_result['midpoint']
        if midpoint_x is None or midpoint_y is None:
            return
        
        # Draw progress circle
        progress = self.lock_timer.get_progress()
        self._draw_countdown_circle(frame, (midpoint_x, midpoint_y), progress, config.GREEN)
        
        # Draw countdown text
        countdown_text = f"LOCKING: {remaining_time:.1f}s"
        cv2.putText(frame, countdown_text, (midpoint_x - 60, midpoint_y - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.GREEN, 2)
    
    def _draw_unlock_countdown(self, frame, dual_victory_result, remaining_time):
        """Draw countdown timer for dual victory unlocking"""
        midpoint_x, midpoint_y = dual_victory_result['midpoint']
        if midpoint_x is None or midpoint_y is None:
            return
        
        # Draw progress circle
        progress = self.unlock_timer.get_progress()
        self._draw_countdown_circle(frame, (midpoint_x, midpoint_y), progress, config.BLUE)
        
        # Draw countdown text
        countdown_text = f"UNLOCKING: {remaining_time:.1f}s"
        cv2.putText(frame, countdown_text, (midpoint_x - 70, midpoint_y - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.BLUE, 2)
    
    def _draw_countdown_circle(self, frame, center, progress, color):
        """Draw a progress circle showing countdown progress"""
        radius = 30
        thickness = 4
        
        # Draw background circle
        cv2.circle(frame, center, radius, config.GRAY, thickness)
        
        # Draw progress arc
        if progress > 0:
            start_angle = -90  # Start from top
            end_angle = start_angle + (360 * progress)
            cv2.ellipse(frame, center, (radius, radius), 0, start_angle, end_angle, color, thickness)
        
        # Draw center dot
        cv2.circle(frame, center, 5, color, -1)
        
        # Draw percentage text
        percentage = int(progress * 100)
        text = f"{percentage}%"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = center[1] + text_size[1] // 2
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def draw_persistent_hud(self, frame):
        """Draw HUD with persistent ReID tracking and direction control information"""
        H = frame.shape[0]
        
        if self.tracker.is_locked:
            # Locked mode - minimal info
            cv2.putText(frame, "LOCKED", (20, H - 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.RED, 3)
            cv2.putText(frame, "DUAL VICTORY (close together) to unlock", (20, H - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
        else:
            # Unlocked mode - show instructions based on mode
            cv2.putText(frame, "READY FOR LOCK", (20, H - 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.GREEN, 3)
            
            # Mode-specific instructions
            if config.LOCKING_MODE == "FIST_PALM":
                cv2.putText(frame, "FIST + PALM (close together) to lock", (20, H - 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
            else:
                cv2.putText(frame, "POINTING UP to lock", (20, H - 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
        
        cv2.putText(frame, "r: reset | q: quit | f: fullscreen | h: help", (20, H - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.WHITE, 2)
    
    def handle_input(self) -> bool:
        """
        Handle keyboard input.
        
        Returns:
            bool: True to continue, False to exit
        """
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return False
        elif key == ord('r'):
            if self.tracker.is_locked:
                print("[UI] Manual unlock - removing persistent ReID profile")
                print("[UI] Direction control deactivated")
                # Reset direction controller and GUI
                self.direction_controller.reset_state()
                direction_gui.set_lock_status(False)
            self.tracker.unlock_target()
        elif key == ord('f'):
            self.toggle_fullscreen()
        elif key == ord('h'):
            # Serial communication removed
            print("[UI] Serial communication removed - will be implemented from scratch")
        
        return True
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_prop = cv2.getWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN)
        
        if current_prop == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, 
                                cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.args.width, self.args.height)
            print("[UI] Switched to windowed mode")
        else:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, 
                                cv2.WINDOW_FULLSCREEN)
            print("[UI] Switched to fullscreen mode")

def main():
    """Main entry point"""
    args = parse_arguments()
    system = PersonLockSystem(args)
    system.run()

if __name__ == "__main__":
    main()