# Person Lock System with Direction Control

A real-time computer vision system that locks onto a person using advanced gesture recognition and provides directional control through pose and gesture analysis. The system features dual gesture combinations with hold timers, persistent ReID tracking, and enhanced security measures.

## ✨ Key Features

### 🔒 Advanced Gesture Control
- **Dual Gesture Locking**: Fist + Palm combination with proximity validation
- **Dual Victory Unlocking**: Both hands showing victory gestures close together
- **2-Second Hold Timer**: Deliberate gesture confirmation with visual countdown
- **Proximity Validation**: Gestures must be within configurable distance thresholds

### 🧠 Intelligent Tracking
- **Persistent ReID Tracking**: Deep learning-based person re-identification
- **Identity Preservation**: Survives occlusions and track ID changes
- **High Security**: Only the locked person can unlock themselves
- **Spatial Consistency**: Prevents false matches through movement validation

### 🎮 Advanced Direction Control
- **Left Hand Movement**: Open Palm = Forward, Closed Fist = Backward
- **Right Elbow Steering**: Angle-based left/right control (90° threshold)
- **Unified Gesture Pipeline**: Conflict-free gesture detection system
- **Real-time Response**: Smooth command execution with hold logic

### 🖥️ Enhanced User Interface
- **Countdown Visualization**: Progress circles with percentage display
- **Dual Mode Support**: Switchable between FIST_PALM and POINTING_UP modes
- **Real-time GUI**: Separate direction control window
- **Rich Visual Feedback**: Color-coded status indicators and connection lines

## System Requirements

- **Python**: 3.11.13 (required for MediaPipe compatibility)
- **Operating System**: Windows, macOS, or Linux
- **Camera**: USB webcam or built-in camera
- **RAM**: Minimum 8GB recommended
- **GPU**: Optional but recommended for better performance

## Installation

### Step 1: Create Conda Environment

**Important**: MediaPipe requires Python 3.11.13 for optimal compatibility. Create a separate conda environment named "gestureModel":

```bash
# Create new conda environment named "gestureModel" with Python 3.11.13
conda create -n gestureModel python=3.11.13

# Activate the environment
conda activate gestureModel
```

### Step 2: Install Dependencies

Once you're in the activated conda environment, install all required packages:

```bash
# Make sure you're in the gestureModel environment (you should see (gestureModel) in your prompt)
# Navigate to your project directory
cd path/to/your/person_tracker

# Install all required packages from requirements.txt
pip install -r requirements.txt
```

### Complete Installation Script

Here's a complete script you can run in your terminal:

```bash
# 1. Create and activate conda environment
conda create -n gestureModel python=3.11.13 -y
conda activate gestureModel

# 2. Navigate to project directory (adjust path as needed)
cd g:\ATR_lab\after_september\GestureResearch\gestureModel\person_tracker

# 3. Install requirements
pip install -r requirements.txt

# 4. Verify installation
python -c "import cv2, mediapipe, torchreid, ultralytics; print('All packages installed successfully!')"
```

### Step 3: Download Models

The system will automatically download required models on first run:
- YOLO weights (`yolov8n.pt`)
- MediaPipe gesture recognition model
- MediaPipe pose landmarker model
- MediaPipe hand landmarker model

## Usage

### Before Running

**Important**: Always activate the conda environment before running the application:

```bash
# Activate the gestureModel environment
conda activate gestureModel

# Verify you're in the correct environment (should show (gestureModel) in prompt)
# Navigate to project directory
cd g:\ATR_lab\after_september\GestureResearch\gestureModel\person_tracker
```

### Basic Usage

```bash
# Run with default camera (camera index 0)
python main.py

# Run with specific camera
python main.py --source 1

# Run with video file
python main.py --source "path/to/video.mp4"
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --source SOURCE         Camera index or video file path (default: "0")
  --conf CONF            YOLO confidence threshold (default: 0.5)
  --sim SIM              ReID similarity threshold (default: 0.30)
  --gesture_conf CONF    Gesture detection confidence (default: 0.50)
  --device DEVICE        Device for ReID model: cpu or cuda (default: cpu)
  --loss_timeout SECONDS Seconds before auto-unlock (default: 15.0)
  --width WIDTH          Display width (default: 1280)
  --height HEIGHT        Display height (default: 720)
  --fullscreen           Start in fullscreen mode
  --debug                Enable debug output
```

### Example Commands

```bash
# High confidence detection
python main.py --conf 0.7 --gesture_conf 0.6

# Use GPU for ReID (if available)
python main.py --device cuda

# Custom timeout
python main.py --loss_timeout 20.0

# Fullscreen mode
python main.py --fullscreen
```

## How It Works

### 1. Person Detection
- Uses YOLO v8 for real-time person detection
- Tracks multiple people with unique IDs
- Filters detections to only show persons

### 2. Advanced Gesture Recognition System
- **Locking Mechanism**: Dual Fist + Palm combination
  - Both hands must show specific gestures (Closed_Fist + Open_Palm)
  - Hands must be within proximity threshold (configurable distance)
  - 2-second hold requirement with real-time countdown
  - Visual progress circle showing completion percentage

- **Unlocking Mechanism**: Dual Victory gestures
  - Both hands must show victory/peace signs simultaneously
  - Proximity validation ensures intentional gesture
  - 2-second hold timer prevents accidental unlocking
  - Color-coded countdown with completion feedback

### 3. Enhanced Person Identification
- **Persistent ReID Profiles**: Deep learning-based person signatures
- **Identity Continuity**: Survives occlusions, lighting changes, track ID resets
- **High-Security Matching**: Multiple confidence thresholds and spatial validation
- **Profile Evolution**: Adaptive features that improve over time
- **Multi-Frame Validation**: Temporal consistency checks prevent false matches

### 4. Sophisticated Direction Control
- **Left Hand Navigation**:
  - Open Palm = Forward movement
  - Closed Fist = Backward movement
  - Natural and intuitive hand-based control

- **Right Elbow Steering**:
  - Elbow angle < 90° = Left turn
  - Elbow angle > 90° = Right turn
  - Real-time angle calculation with smoothing
  - Visual overlay showing current angle

- **Unified Gesture Pipeline**:
  - Single gesture detection system prevents conflicts
  - Direction control respects unlocking gestures
  - Seamless coordination between all gesture types

### 5. Multi-Layer Security System
- **Identity Verification**: Only the locked person can unlock
- **Gesture Source Validation**: Victory gestures verified against person profile
- **Proximity Requirements**: All dual gestures require hand proximity
- **Hold Timer Protection**: 2-second minimum prevents accidental triggers
- **Spatial Consistency**: Movement validation prevents impossible matches

## Controls

### Keyboard Controls
- **'q'**: Quit application
- **'r'**: Reset/unlock current target
- **'f'**: Toggle fullscreen mode

### Advanced Gesture Controls

#### 🔒 Locking Sequence
1. **Show Dual Gestures**: One hand in fist, other hand open palm
2. **Proximity Check**: Hands must be close together (within configured distance)
3. **Hold Position**: Maintain gestures for 2 seconds
4. **Visual Countdown**: Watch progress circle fill up
5. **Lock Confirmation**: System locks onto the person

#### 🔓 Unlocking Sequence  
1. **Show Victory Signs**: Both hands showing peace/victory gestures
2. **Proximity Check**: Victory hands must be close together
3. **Hold Position**: Maintain for 2 seconds while countdown displays
4. **Identity Verification**: System confirms you are the locked person
5. **Unlock Confirmation**: System unlocks and returns to normal mode

#### 🎮 Direction Control (When Locked)
- **Left Hand Forward/Backward**:
  - Open Palm = Move Forward
  - Closed Fist = Move Backward
  
- **Right Elbow Left/Right**:
  - Bend elbow < 90° = Turn Left
  - Extend elbow > 90° = Turn Right

## GUI Components

### Main Display Window
- **Live Camera Feed**: Real-time video with person detection overlays
- **Gesture Visualization**: Hand landmarks with skeleton connections
- **Dual Gesture Indicators**: Special highlighting for fist+palm and dual victory
- **Countdown Timers**: Visual progress circles during 2-second hold periods
- **Person Tracking**: Color-coded bounding boxes (green=normal, red=locked)
- **Status Information**: Current mode, instructions, and system state
- **Connection Lines**: Visual links between hands during dual gestures

### Direction Control GUI
- **Separate Control Window**: Dedicated direction command display
- **Real-time Command Updates**: 
  - Forward/Backward status (LEFT HAND: Palm=Forward, Fist=Backward)
  - Left/Right status (RIGHT ELBOW: <90°=Left, >90°=Right)
- **Color-Coded Indicators**:
  - Green = Forward/Active commands
  - Red = Backward commands  
  - Orange/Cyan = Left/Right commands
  - Gray = No command detected
- **Lock Status Display**: Shows when direction control is active
- **Always-on-Top**: Stays visible during operation

## Troubleshooting

### Common Issues

1. **MediaPipe Installation Issues**
   ```bash
   # Make sure you're in the gestureModel environment
   conda activate gestureModel
   
   # Ensure you're using Python 3.11.13
   python --version
   
   # Reinstall MediaPipe
   pip uninstall mediapipe
   pip install mediapipe>=0.10.0
   ```

2. **Camera Not Found**
   ```bash
   # List available cameras
   python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
   
   # Try different camera index
   python main.py --source 1
   ```

3. **Poor Gesture Recognition**
   ```bash
   # Lower confidence threshold
   python main.py --gesture_conf 0.3
   
   # Ensure good lighting and clear hand visibility
   ```

4. **ReID Model Issues**
   ```bash
   # Use CPU if CUDA issues
   python main.py --device cpu
   
   # Check torchreid installation
   python -c "import torchreid; print(torchreid.__version__)"
   ```

### Performance Optimization

1. **For Better Performance**
   - Use GPU: `--device cuda`
   - Lower resolution: `--width 640 --height 480`
   - Higher confidence: `--conf 0.7`

2. **For Better Accuracy**
   - Higher confidence: `--conf 0.6 --gesture_conf 0.6`
   - Good lighting conditions
   - Clear hand visibility

## File Structure

```
person_tracker/
├── main.py                 # Main application entry point
├── config.py              # Configuration constants
├── person_detector.py     # YOLO person detection
├── gesture_detector.py    # MediaPipe gesture recognition
├── person_reid.py         # Person re-identification
├── target_tracker.py      # Persistent tracking logic
├── direction_controller.py # Direction control system
├── direction_gui.py       # Direction control GUI
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── yolov8n.pt            # YOLO model weights
├── gesture_recognizer.task # MediaPipe gesture model
├── hand_landmarker.task   # MediaPipe hand model
└── pose_landmarker_lite.task # MediaPipe pose model
```

## Technical Details

### Core Models & Technologies
- **YOLO v8n**: Ultra-fast person detection and tracking
- **OSNet x0.25**: Lightweight person re-identification features  
- **MediaPipe Tasks**: Hand gesture recognition and pose estimation
- **OpenCV**: Computer vision processing and display
- **Torchreid**: Person re-identification framework

### Advanced Algorithms

#### 🎯 Dual Gesture Detection
- **Proximity Validation**: Mathematical distance calculation between hand centers
- **Confidence Thresholding**: Multi-level confidence checks for gesture reliability
- **Temporal Consistency**: 2-second hold validation with frame-by-frame verification
- **Gesture Association**: Spatial mapping between gestures and person bounding boxes

#### 🧠 Persistent Person Profiling  
- **Feature Extraction**: 512-dimensional ReID feature vectors
- **Profile Evolution**: Exponential moving average for adaptive person signatures
- **Multi-Frame Security**: Consecutive match requirements and spatial consistency
- **Identity Persistence**: Survives track ID changes and temporary occlusions

#### 📐 Pose Analysis Engine
- **3-Point Angle Calculation**: Precise elbow angle computation using shoulder-elbow-wrist landmarks
- **Temporal Smoothing**: Moving average filter for stable angle readings
- **Threshold-Based Classification**: 90° cutoff for left/right determination
- **Coordinate Transformation**: Normalized to pixel coordinate mapping

### Performance Characteristics
- **Overall System**: 20-30 FPS on modern hardware
- **Person Detection**: ~30 FPS (YOLO inference)
- **ReID Processing**: 10-15 FPS (CPU) / 20-25 FPS (GPU)
- **Gesture Recognition**: 25-30 FPS (MediaPipe)
- **Memory Footprint**: 2-4 GB RAM (varies with model size)
- **Latency**: <100ms end-to-end gesture response

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) for person detection
- [MediaPipe](https://mediapipe.dev/) for gesture and pose recognition
- [Torchreid](https://github.com/KaiyangZhou/deep-person-reid) for person re-identification
- [OpenCV](https://opencv.org/) for computer vision utilities

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the command line options
3. Ensure proper conda environment setup
4. Check system requirements

---

**Note**: This system requires Python 3.11.13 for optimal MediaPipe compatibility. Always use the conda environment setup as described in the installation section.
