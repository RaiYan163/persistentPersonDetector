# main.py - Main application entry point with persistent ReID and direction control

import argparse
import time
import cv2
import config
from person_detector import PersonDetector
from gesture_detector import GestureDetector
from person_reid import PersonReID
from target_tracker import TargetTracker
from direction_controller import DirectionController
from direction_gui import direction_gui
from utils import (
    associate_gesture_to_person, 
    draw_hand_landmarks, 
    draw_person_boxes,
    draw_locked_target, 
    draw_hud
)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Person Lock System - Lock onto a person with pointing up gesture (PERSISTENT ReID TRACKING + DIRECTION CONTROL)"
    )
    
    # Video source
    parser.add_argument("--source", type=str, default="0", 
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
        
        # Initialize direction controller
        self.direction_controller = DirectionController()
        
        # Start the direction GUI
        direction_gui.start_gui()
        
        print("[SYSTEM] Person Lock System initialized with PERSISTENT ReID tracking")
        print("[SYSTEM] Security: High-confidence persistent person identification")
        print("[SYSTEM] Features: Survives occlusions, prevents false positives, 15s timeout")
        print("[SYSTEM] Lock Gesture: POINTING UP (index finger pointing upward)")
        print("[SYSTEM] Unlock Gesture: VICTORY (peace sign)")
        print("[SYSTEM] DIRECTION CONTROL: Active when person is locked")
        print("[SYSTEM] Direction Commands: Fist=Forward, Thumb=Backward, Palm=Pause, Elbow angle=Left/Right")
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
            direction_result = self.direction_controller.analyze_locked_person(frame, locked_person_bbox)
        
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
        """Try to lock onto a person showing pointing up gesture"""
        pointing_up_list = gesture_results['pointing_up_list']
        
        if not pointing_up_list or all_boxes_xyxy is None or len(all_boxes_xyxy) == 0:
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
            
            # Visual feedback
            cv2.circle(frame, (gesture_x, gesture_y), 25, config.GREEN, 4)
            cv2.putText(frame, "LOCKED!", (gesture_x + 30, gesture_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, config.GREEN, 3)
    
    def try_unlock_target_secure(self, frame, all_boxes_xyxy, all_track_ids, gesture_results):
        """
        SECURE VERSION: Try to unlock with victory gesture.
        Only unlocks if victory gesture comes from the locked person.
        This is the critical security fix.
        """
        victory_list = gesture_results['victory_list']
        
        if not victory_list:
            return
        
        best_victory = self.gesture_detector.get_best_victory(victory_list)
        if not best_victory:
            return
        
        gesture_x, gesture_y = best_victory['x'], best_victory['y']
        
        # SECURITY CHECK: Verify victory gesture comes from locked target person
        is_from_target = self.tracker.is_target_person_at_location(
            frame, gesture_x, gesture_y, all_boxes_xyxy, all_track_ids
        )
        
        if is_from_target:
            state_info = self.tracker.get_state()
            person_id = state_info.get('person_id', 'Unknown')
            print(f"[SYSTEM] Victory gesture from {person_id}")
            print(f"[SYSTEM] UNLOCKING persistent ReID profile")
            print(f"[SYSTEM] DIRECTION CONTROL deactivated")
            
            # Reset direction controller state
            self.direction_controller.reset_state()
            
            self.tracker.unlock_target()
            
            # Visual feedback
            cv2.circle(frame, (gesture_x, gesture_y), 25, config.BLUE, 4)
            cv2.putText(frame, "UNLOCKED!", (gesture_x + 30, gesture_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, config.BLUE, 3)
        else:
            print(f"[SECURITY] Victory gesture NOT from target person - IGNORING")
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
    
    def draw_persistent_hud(self, frame):
        """Draw HUD with persistent ReID tracking and direction control information"""
        H = frame.shape[0]
        
        if self.tracker.is_locked:
            # Locked mode - minimal info
            cv2.putText(frame, "LOCKED", (20, H - 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.RED, 3)
            cv2.putText(frame, "VICTORY to unlock", (20, H - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
        else:
            # Unlocked mode - minimal info
            cv2.putText(frame, "READY FOR LOCK", (20, H - 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.GREEN, 3)
            cv2.putText(frame, "POINTING UP to lock", (20, H - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.YELLOW, 2)
        
        cv2.putText(frame, "r: reset | q: quit | f: fullscreen", (20, H - 20),
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