# 🎮 Person Lock System - Complete Control Manual

A comprehensive guide to operating the Person Lock System with advanced gesture recognition, persistent tracking, and directional control.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Application Launch & Setup](#application-launch--setup)
3. [Keyboard Controls](#keyboard-controls)
4. [Gesture Control System](#gesture-control-system)
5. [Direction Control System](#direction-control-system)
6. [GUI Interface Guide](#gui-interface-guide)
7. [Visual Feedback Reference](#visual-feedback-reference)
8. [Control Modes & Switching](#control-modes--switching)
9. [Troubleshooting Controls](#troubleshooting-controls)
10. [Advanced Control Techniques](#advanced-control-techniques)

---

## 🎯 System Overview

The Person Lock System operates in **two main states**:

### **🔓 UNLOCKED STATE**
- **Mode**: Multi-person detection and tracking
- **Function**: Scan for locking gestures
- **Display**: All detected people with green bounding boxes
- **Controls**: Keyboard shortcuts + gesture locking

### **🔒 LOCKED STATE**
- **Mode**: Single-person focus with direction control
- **Function**: Track locked person + direction commands
- **Display**: Only locked person with red bounding box
- **Controls**: Keyboard shortcuts + gesture unlocking + direction control

---

## 🚀 Application Launch & Setup

### **Command Line Startup**

```bash
# Basic startup (default camera)
python main.py

# Complete startup with options
python main.py --source 0 --conf 0.5 --gesture_conf 0.5 --device cpu --width 1280 --height 720
```

### **Command Line Options Reference**

| Option | Default | Description | Example |
|--------|---------|-------------|---------|
| `--source` | `"0"` | Camera index or video file | `--source 1` or `--source "video.mp4"` |
| `--conf` | `0.5` | YOLO person detection confidence (0.0-1.0) | `--conf 0.7` |
| `--sim` | `0.30` | ReID similarity threshold (0.0-1.0) | `--sim 0.4` |
| `--gesture_conf` | `0.50` | Gesture detection confidence (0.0-1.0) | `--gesture_conf 0.6` |
| `--device` | `"cpu"` | ReID model device (cpu/cuda) | `--device cuda` |
| `--tracker` | `"bytetrack.yaml"` | YOLO tracker configuration | `--tracker "ocsort.yaml"` |
| `--loss_timeout` | `15.0` | Auto-unlock timeout (seconds) | `--loss_timeout 20.0` |
| `--width` | `1280` | Display window width | `--width 640` |
| `--height` | `720` | Display window height | `--height 480` |
| `--fullscreen` | `False` | Start in fullscreen mode | `--fullscreen` |
| `--debug` | `False` | Enable debug console output | `--debug` |

### **Performance Optimization Commands**

```bash
# High performance (GPU + high confidence)
python main.py --device cuda --conf 0.7 --gesture_conf 0.6

# Low resource usage (CPU + lower resolution)
python main.py --device cpu --width 640 --height 480 --conf 0.3

# Maximum accuracy (high thresholds)
python main.py --conf 0.8 --gesture_conf 0.7 --sim 0.4
```

---

## ⌨️ Keyboard Controls

### **Global Keyboard Shortcuts**

| Key | Function | State | Description |
|-----|----------|-------|-------------|
| **`q`** | **Quit** | Any | Immediately exit application |
| **`r`** | **Reset/Unlock** | Any | Force unlock current target and reset system |
| **`f`** | **Toggle Fullscreen** | Any | Switch between windowed and fullscreen mode |

### **Keyboard Control Details**

#### **🛑 'q' - Quit Application**
- **Function**: Immediate application termination
- **Effect**: Closes all windows and releases camera
- **When to use**: Normal shutdown, emergency exit
- **No confirmation**: Application exits immediately

#### **🔄 'r' - Reset/Unlock Target**
- **Function**: Force unlock and reset to scanning mode
- **Effect**: 
  - Removes persistent ReID profile
  - Deactivates direction control
  - Returns to multi-person detection
  - Resets all gesture timers
- **When to use**: Stuck in locked state, want to change target, system errors

#### **🖥️ 'f' - Toggle Fullscreen**
- **Function**: Switch display mode
- **Windowed → Fullscreen**: Expands to full screen, hides window borders
- **Fullscreen → Windowed**: Returns to configured resolution (default 1280x720)
- **When to use**: Better visibility, presentations, smaller screens

---

## 🤲 Gesture Control System

The system supports **two locking modes** configurable in `config.py`:

### **🔒 FIST_PALM Mode (Default)**

#### **Locking Sequence**
1. **Position Hands**: Show both hands to camera clearly
2. **Make Gestures**: 
   - **One hand**: Closed fist ✊
   - **Other hand**: Open palm ✋
3. **Proximity Check**: Bring hands close together
   - **Maximum distance**: 250 pixels or 20% of frame diagonal
   - **Visual indicator**: Yellow connection line appears when close enough
4. **Hold Position**: Maintain gestures for **2.0 seconds**
   - **Progress indicator**: Countdown circle shows completion percentage
   - **Status text**: "Distance: XXpx READY" (green) or "TOO FAR" (red)
5. **Lock Confirmation**: 
   - Person highlighted with **red bounding box**
   - Console message: "PERSISTENT LOCK created"
   - Direction control window activates

#### **Technical Specifications - FIST_PALM**
- **Minimum confidence**: 0.50 for each gesture
- **Required hands**: Exactly 2 hands must be detected
- **Distance threshold**: 250px OR 20% of frame diagonal (whichever is smaller)
- **Hold duration**: 2.0 seconds with 0.1s update intervals
- **Hand detection**: Uses MediaPipe gesture recognition
- **Person association**: 3-tier fallback system (expanded bbox → both hands near → nearest person)

### **☝️ POINTING_UP Mode (Fallback)**

#### **Locking Sequence**
1. **Position Hand**: Show one hand to camera
2. **Point Upward**: Extend index finger upward (👆)
3. **Hold Position**: Maintain gesture for **2.0 seconds**
4. **Lock Confirmation**: Immediate lock on gesture detection

#### **Technical Specifications - POINTING_UP**
- **Minimum confidence**: 0.50
- **Required hands**: 1 hand minimum
- **Hold duration**: 2.0 seconds
- **Instant trigger**: No proximity validation required

### **🔓 Unlocking Sequence (Both Modes)**

#### **Dual Victory Unlocking**
1. **Position Hands**: Show both hands to camera
2. **Victory Gestures**: Both hands show peace/victory signs (✌️✌️)
3. **Proximity Check**: Bring victory hands close together
   - **Maximum distance**: 300 pixels or 30% of frame diagonal
   - **Visual indicator**: Connection line between hands
4. **Hold Position**: Maintain for **2.0 seconds**
   - **Progress indicator**: Countdown circle with completion percentage
5. **Identity Verification**: System verifies you are the locked person
   - **ReID check**: Compares facial/body features with locked profile
   - **Security threshold**: 0.75 similarity required
6. **Unlock Confirmation**: 
   - Returns to multi-person mode
   - Console message: "SECURE UNLOCK by original person"
   - Direction control deactivates

#### **Security Features**
- **Only locked person can unlock**: ReID verification prevents unauthorized unlocking
- **Dual gesture requirement**: Single victory gestures are ignored
- **Proximity validation**: Gestures must be intentionally close together
- **Hold timer protection**: 2-second minimum prevents accidental triggers

---

## 🎮 Direction Control System

**Activates automatically when person is locked**

### **Forward/Backward Control (Left Hand)**

| Gesture | Command | Visual Indicator | Technical Details |
|---------|---------|------------------|-------------------|
| **Open Palm** ✋ | **Forward** | Green "Forward" in GUI | Left hand palm facing camera |
| **Closed Fist** ✊ | **Backward** | Red "Backward" in GUI | Left hand clenched fist |
| **No clear gesture** | **None** | Gray "None" in GUI | Neutral position |

#### **Left Hand Control Specifications**
- **Detection method**: MediaPipe gesture recognition on left hand specifically
- **Confidence threshold**: 0.5 minimum
- **Hold behavior**: Commands persist for 0.8 seconds after gesture loss
- **Conflict resolution**: Direction control respects unlocking gestures (priority to unlock)

### **Left/Right Steering (Right Elbow Angle)**

| Elbow Angle | Command | Visual Indicator | Body Position |
|-------------|---------|------------------|---------------|
| **< 90°** | **Left** | Orange/Cyan "Left" in GUI | Elbow bent inward |
| **> 90°** | **Right** | Orange/Cyan "Right" in GUI | Elbow extended outward |
| **~90°** | **None** | Gray "None" in GUI | Neutral arm position |

#### **Right Elbow Control Specifications**
- **Detection method**: MediaPipe pose estimation (shoulder-elbow-wrist angle)
- **Angle calculation**: 3-point angle using landmarks 12, 14, 16
- **Threshold**: 90.0 degrees (configurable)
- **Smoothing**: 5-frame moving average for stability
- **Real-time feedback**: Angle value displayed on screen overlay

### **Direction Control Technical Details**

#### **Processing Pipeline**
1. **Person Crop**: Extract locked person's bounding box region
2. **Parallel Processing**: 
   - **Pose detection**: MediaPipe pose landmarker for elbow angle
   - **Gesture detection**: MediaPipe gesture recognizer for hand gestures
3. **Command Mapping**: 
   - Left hand gestures → Forward/Backward
   - Right elbow angle → Left/Right
4. **GUI Update**: Real-time command display in separate window
5. **Console Output**: Minimal "Forward, Left" style status messages

#### **Performance Characteristics**
- **Processing rate**: 20-25 FPS on person crop region
- **Latency**: <100ms gesture to command mapping
- **Smoothing**: 5-frame buffer for elbow angles
- **Hold logic**: 0.8s command persistence on gesture dropout
- **Print throttling**: 0.25s minimum between identical console outputs

---

## 🖥️ GUI Interface Guide

### **Main Display Window**

#### **Window Properties**
- **Title**: "Person Lock System - PERSISTENT ReID + DIRECTION CONTROL"
- **Default size**: 1280x720 (configurable)
- **Fullscreen mode**: Toggle with 'f' key
- **Always visible**: Main application window

#### **Visual Elements**

| Element | Unlocked State | Locked State | Description |
|---------|----------------|--------------|-------------|
| **Person boxes** | Green rectangles | Red rectangle (locked person only) | Person detection boundaries |
| **Hand landmarks** | White/colored dots | White/colored dots with gesture labels | 21-point hand skeleton |
| **Hand connections** | Thin white lines | Colored lines | Connects hand landmarks |
| **Gesture indicators** | Labels near hands | Labels + direction info | "FIST", "PALM", "VICTORY" |
| **Connection lines** | Yellow between dual gestures | Yellow between dual gestures | Shows proximity validation |
| **Progress circles** | During hold timers | During hold timers | Countdown visualization |
| **HUD information** | Top-left status | Top-left status + direction | System state and instructions |

#### **Status HUD Content**
```
UNLOCKED State:
- [SYSTEM] Person Lock System initialized
- [MODE] FIST_PALM proximity-based locking
- [UNLOCK] Show FIST + PALM close together
- Controls: 'r'=reset, 'q'=quit, 'f'=fullscreen

LOCKED State:
- [LOCKED] Person ID: X (ReID tracking active)
- [DIRECTION] Forward/Back: LEFT HAND | Left/Right: RIGHT ELBOW
- [UNLOCK] Show DUAL VICTORY close together
- Controls: 'r'=reset, 'q'=quit, 'f'=fullscreen
```

### **Direction Control GUI Window**

#### **Window Properties**
- **Title**: "Direction Control"
- **Size**: 400x300 (fixed)
- **Position**: Top-right corner
- **Always on top**: Stays visible above other windows
- **Auto-launch**: Appears when person is locked

#### **Display Elements**

| Section | Content | Color Coding |
|---------|---------|--------------|
| **Lock Status** | "LOCKED" or "UNLOCKED" | Red/Green |
| **Forward/Backward** | "Forward" / "Backward" / "None" | Green / Red / Gray |
| **Left/Right** | "Left" / "Right" / "None" | Orange/Cyan / Gray |
| **Timestamp** | Last update time | White text |

#### **Color Code Reference**
- **🟢 Green**: Forward commands, active lock status
- **🔴 Red**: Backward commands, locked status
- **🟠 Orange**: Left turn commands
- **🟦 Cyan**: Right turn commands  
- **⚫ Gray**: No command detected, unlocked status

---

## 🎨 Visual Feedback Reference

### **Hand Gesture Visualization**

#### **FIST_PALM Mode Visual Indicators**

| Situation | Hand 1 Visual | Hand 2 Visual | Connection | Status Text |
|-----------|---------------|---------------|------------|-------------|
| **Hands detected, too far** | Normal landmarks | Normal landmarks | None | No status |
| **Hands close, wrong gestures** | Normal landmarks | Normal landmarks | None | "Wrong gestures" |
| **Fist + Palm detected, close** | Red landmarks + "FIST" | Green landmarks + "PALM" | Yellow line | "Distance: XXpx READY" (green) |
| **Fist + Palm detected, far** | Red landmarks + "FIST" | Green landmarks + "PALM" | None | "Distance: XXpx TOO FAR" (red) |
| **Hold timer active** | Gesture visuals + progress circle | Gesture visuals + progress circle | Yellow line | Countdown percentage |
| **Lock successful** | Green circle at midpoint + "LOCKED!" | Green circle at midpoint + "LOCKED!" | Yellow line | "PERSISTENT LOCK created" |

#### **Dual Victory Unlock Visual Indicators**

| Situation | Hand 1 Visual | Hand 2 Visual | Connection | Status Text |
|-----------|---------------|---------------|------------|-------------|
| **Victory gestures detected** | Blue landmarks + "VICTORY" | Blue landmarks + "VICTORY" | Cyan line | "Dual victory detected" |
| **Hold timer active** | Victory visuals + progress circle | Victory visuals + progress circle | Cyan line | Countdown percentage |
| **Unlock successful** | Green circle + "UNLOCKED!" | Green circle + "UNLOCKED!" | Green line | "SECURE UNLOCK by original person" |
| **Security failed** | Red X marker | Red X marker | Red line | "SECURITY: Wrong person attempting unlock" |

### **Direction Control Visualization**

#### **Pose Overlay Elements**
- **Right arm skeleton**: Shoulder → Elbow → Wrist connection
- **Elbow angle arc**: Visual angle measurement
- **Angle value text**: Real-time degree display
- **Direction arrows**: Left/Right indicators

#### **Hand Gesture Overlays**
- **Left hand focus**: Highlighted for direction control
- **Gesture labels**: "Open_Palm" / "Closed_Fist"
- **Command arrows**: Forward/Backward direction indicators

---

## 🔄 Control Modes & Switching

### **Locking Mode Configuration**

#### **Switching Between FIST_PALM and POINTING_UP**

**File**: `config.py` (Line 21)

```python
# Change this line to switch modes:
LOCKING_MODE = "FIST_PALM"    # Dual gesture mode (default)
# OR
LOCKING_MODE = "POINTING_UP"  # Single gesture mode (fallback)
```

**After changing**: Restart the application

#### **Mode Comparison**

| Feature | FIST_PALM Mode | POINTING_UP Mode |
|---------|----------------|------------------|
| **Locking gesture** | Fist + Palm (dual hand) | Pointing up (single hand) |
| **Proximity requirement** | Yes (250px max) | No |
| **Hold timer** | 2.0 seconds | 2.0 seconds |
| **Security level** | High (dual gesture) | Medium (single gesture) |
| **Ease of use** | Moderate (coordination) | Easy (one hand) |
| **Unlocking** | Dual victory (same for both) | Dual victory (same for both) |

### **Configuration Parameters**

#### **FIST_PALM Configuration**
```python
FIST_PALM_MIN_CONFIDENCE = 0.50        # Gesture confidence threshold
FIST_PALM_MAX_DISTANCE_PIXELS = 250     # Max pixel distance between hands
FIST_PALM_MAX_DISTANCE_RATIO = 0.20     # Max distance as frame ratio
FIST_PALM_REQUIRED_HANDS = 2            # Must detect exactly 2 hands
```

#### **Dual Victory Configuration**
```python
DUAL_VICTORY_MIN_CONFIDENCE = 0.50      # Victory gesture confidence
DUAL_VICTORY_MAX_DISTANCE_PIXELS = 300  # Max pixel distance
DUAL_VICTORY_MAX_DISTANCE_RATIO = 0.30  # Max distance ratio
DUAL_VICTORY_REQUIRED_HANDS = 2         # Must detect exactly 2 hands
```

#### **Direction Control Configuration**
```python
FB_HOLD_SECONDS = 0.8           # Hold forward/backward commands
LR_THRESHOLD = 90.0             # Elbow angle threshold (degrees)
ANGLE_SMOOTH_N = 5              # Smoothing buffer size
PRINT_COOLDOWN = 0.25           # Console output throttling
```

---

## 🔧 Troubleshooting Controls

### **Common Control Issues**

#### **Gesture Recognition Problems**

| Problem | Possible Causes | Solutions |
|---------|----------------|-----------|
| **Gestures not detected** | Poor lighting, low confidence | • Improve lighting<br>• Lower `--gesture_conf`<br>• Clean hand visibility |
| **False gesture triggers** | High sensitivity | • Increase `--gesture_conf`<br>• Increase confidence thresholds |
| **Dual gestures don't work** | Hands too far apart | • Check distance thresholds<br>• Move hands closer<br>• Verify proximity limits |
| **Hold timer keeps resetting** | Inconsistent gestures | • Hold steadier position<br>• Improve lighting<br>• Check confidence levels |

#### **🔒 Locking/Unlocking Issues**

| Problem | Possible Causes | Solutions |
|---------|----------------|-----------|
| **Can't lock on person** | Person association failure | • Move closer to camera<br>• Ensure clear person visibility<br>• Check detection confidence |
| **Wrong person gets locked** | Multiple people overlap | • Isolate target person<br>• Use higher confidence<br>• Improve camera angle |
| **Can't unlock** | ReID mismatch, wrong person | • Press 'r' to force reset<br>• Verify you are locked person<br>• Check security thresholds |
| **Auto-unlock occurs** | Loss timeout reached | • Stay visible to camera<br>• Increase `--loss_timeout`<br>• Check ReID similarity |

#### **🎮 Direction Control Problems**

| Problem | Possible Causes | Solutions |
|---------|----------------|-----------|
| **No direction commands** | Not locked, poor pose detection | • Ensure person is locked<br>• Check pose visibility<br>• Verify crop region |
| **Inconsistent commands** | Poor gesture/pose detection | • Improve lighting<br>• Clear arm visibility<br>• Check confidence levels |
| **Direction GUI not appearing** | GUI initialization failure | • Check tkinter installation<br>• Restart application<br>• Run with `--debug` |
| **Wrong direction mapping** | Incorrect pose estimation | • Check elbow angle display<br>• Verify arm positions<br>• Adjust angle threshold |

#### **📹 Camera and Display Issues**

| Problem | Possible Causes | Solutions |
|---------|----------------|-----------|
| **Camera not found** | Wrong index, permissions | • Try different `--source` values<br>• Check camera permissions<br>• Test with system camera app |
| **Poor performance** | High resolution, CPU overload | • Lower resolution: `--width 640 --height 480`<br>• Use GPU: `--device cuda`<br>• Increase confidence thresholds |
| **Display issues** | Window problems, fullscreen | • Toggle fullscreen with 'f'<br>• Restart application<br>• Check display drivers |

### **Debug Commands**

#### **Diagnosis Commands**
```bash
# Debug mode with full logging
python main.py --debug

# Test with lower confidence
python main.py --conf 0.3 --gesture_conf 0.3

# CPU-only mode for compatibility
python main.py --device cpu

# High confidence for accuracy testing
python main.py --conf 0.8 --gesture_conf 0.8
```

#### **System Validation**
```bash
# Test camera access
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera FAIL')"

# Test MediaPipe installation
python -c "import mediapipe as mp; print(f'MediaPipe {mp.__version__} OK')"

# Test ReID system
python -c "import torchreid; print(f'TorchReID {torchreid.__version__} OK')"
```

---

## 🏆 Advanced Control Techniques

### **Optimal Control Practices**

#### **🎯 Best Locking Practices**
1. **Positioning**: Stand 3-6 feet from camera for optimal detection
2. **Lighting**: Ensure even lighting on hands and body
3. **Background**: Avoid cluttered backgrounds that confuse detection
4. **Gesture clarity**: Make distinct, clear gestures with good hand separation
5. **Timing**: Wait for visual confirmation before releasing gestures

#### **🎮 Efficient Direction Control**
1. **Left hand positioning**: Keep left hand in camera view for forward/backward
2. **Right arm visibility**: Ensure shoulder-elbow-wrist landmarks are visible
3. **Smooth movements**: Make gradual pose changes for stable angle detection
4. **Command persistence**: Brief gesture holds are sufficient due to 0.8s hold logic
5. **GUI monitoring**: Watch direction GUI for real-time command feedback

#### **🔐 Security Best Practices**
1. **Clear unlocking**: Use distinct victory gestures with proper proximity
2. **Identity consistency**: Maintain consistent appearance during session
3. **Timeout awareness**: Stay visible to avoid 15-second auto-unlock
4. **Manual reset**: Use 'r' key if system gets confused
5. **Mode switching**: Choose appropriate mode for your use case

### **Power User Shortcuts**

#### **Rapid Mode Switching**
```bash
# Quick FIST_PALM mode setup
sed -i 's/LOCKING_MODE = .*/LOCKING_MODE = "FIST_PALM"/' config.py

# Quick POINTING_UP mode setup  
sed -i 's/LOCKING_MODE = .*/LOCKING_MODE = "POINTING_UP"/' config.py
```

#### **Performance Profiles**

**High Performance Profile**:
```bash
python main.py --device cuda --conf 0.7 --gesture_conf 0.6 --width 1920 --height 1080
```

**Low Latency Profile**:
```bash
python main.py --device cpu --conf 0.4 --gesture_conf 0.4 --width 640 --height 480
```

**Maximum Accuracy Profile**:
```bash
python main.py --conf 0.8 --gesture_conf 0.8 --sim 0.4 --loss_timeout 30.0
```

#### **Custom Configuration Templates**

**Security-Focused**:
```python
FIST_PALM_MIN_CONFIDENCE = 0.70
DUAL_VICTORY_MIN_CONFIDENCE = 0.70
PERSISTENT_REID_LOCK_THRESH = 0.85
GESTURE_HOLD_DURATION = 3.0
```

**Performance-Focused**:
```python
FIST_PALM_MIN_CONFIDENCE = 0.40
DUAL_VICTORY_MIN_CONFIDENCE = 0.40
GESTURE_HOLD_DURATION = 1.5
FB_HOLD_SECONDS = 0.5
```

---

## 📞 Support and Resources

### **Documentation References**
- **README.md**: Installation and basic usage
- **IMPLEMENTATION_SUMMARY.md**: Technical implementation details
- **UBUNTU_INSTALLATION_GUIDE.md**: Linux-specific setup
- **system_flow_diagram.md**: System architecture diagrams

### **Configuration Files**
- **config.py**: All system parameters and thresholds
- **requirements.txt**: Python dependencies
- **main.py**: Command-line argument reference

### **Getting Help**
1. **Enable debug mode**: `python main.py --debug`
2. **Check console output**: Look for `[SYSTEM]`, `[GESTURE]`, `[DIRECTION]` messages
3. **Test basic functionality**: Camera access, gesture detection, person detection
4. **Review configuration**: Verify `config.py` settings match your needs
5. **Performance tuning**: Adjust confidence thresholds and resolution

---

**🎉 You now have complete control over the Person Lock System!**

This manual covers all aspects of operating the system from basic startup to advanced configuration. Refer to specific sections as needed and experiment with different settings to find your optimal configuration.
