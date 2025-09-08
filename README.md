# Person Lock System with Direction Control

A real-time computer vision system that locks onto a person using gesture recognition and provides directional control through pose and gesture analysis. The system uses persistent ReID (Re-identification) tracking to maintain person identity across occlusions and track ID changes.

## Features

- **Persistent Person Tracking**: Uses deep learning ReID features to maintain person identity across occlusions
- **Gesture-Based Locking**: Point up gesture to lock onto a person, victory gesture to unlock
- **Direction Control**: When locked, control movement using hand gestures and pose analysis
- **Security Features**: Only the locked person can unlock themselves using victory gesture
- **Real-time GUI**: Separate window showing current direction commands
- **Robust Tracking**: Survives temporary occlusions and track ID changes

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

### 2. Gesture Recognition
- **Lock Gesture**: Point up (index finger pointing upward)
- **Unlock Gesture**: Victory sign (peace sign)
- Uses MediaPipe for robust hand gesture recognition

### 3. Persistent ReID Tracking
- Creates a persistent person profile using deep learning features
- Maintains identity across occlusions and track ID changes
- High-confidence matching prevents false positive locking

### 4. Direction Control (When Locked)
- **Forward/Backward**: Hand gestures
  - Thumb Up = Forward
  - Thumb Down = Backward
  - Open Palm = Pause
- **Left/Right**: Right elbow angle
  - < 90° = Left turn
  - > 90° = Right turn

### 5. Security Features
- Only the locked person can unlock themselves
- Victory gesture must come from the locked person
- High similarity thresholds prevent false matches

## Controls

### Keyboard Controls
- **'q'**: Quit application
- **'r'**: Reset/unlock current target
- **'f'**: Toggle fullscreen mode

### Gesture Controls
- **Point Up**: Lock onto the person making the gesture
- **Victory Sign**: Unlock (only works for the locked person)

## GUI Components

### Main Window
- Shows camera feed with person detection
- Displays locked person with red bounding box
- Shows gesture recognition results
- Displays system status and instructions

### Direction Control Window
- Separate window showing current direction commands
- Real-time updates of Forward/Backward and Left/Right commands
- Color-coded status indicators
- Stays on top for easy visibility

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

### Models Used
- **YOLO v8**: Person detection and tracking
- **OSNet**: Person re-identification features
- **MediaPipe**: Hand gesture recognition and pose estimation

### Key Algorithms
- **Persistent ReID**: Deep learning-based person re-identification
- **Gesture Association**: Spatial association of gestures to persons
- **Pose Analysis**: Elbow angle calculation for directional control
- **Multi-frame Validation**: Security through temporal consistency

### Performance Metrics
- **Detection**: ~30 FPS on modern hardware
- **ReID**: ~10-15 FPS (CPU), ~20-25 FPS (GPU)
- **Gesture Recognition**: ~25-30 FPS
- **Memory Usage**: ~2-4 GB RAM

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
