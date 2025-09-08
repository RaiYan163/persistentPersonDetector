# Person Tracker System - Ubuntu Installation Guide

Complete installation guide for setting up the Person Tracker with Fist+Palm gesture locking on Ubuntu Linux.

## **System Requirements**

### **Supported Ubuntu Versions:**
- Ubuntu 20.04 LTS (Focal Fossa) ✅
- Ubuntu 22.04 LTS (Jammy Jellyfish) ✅ **Recommended**
- Ubuntu 23.04+ (Latest) ✅

### **Hardware Requirements:**
- **RAM:** Minimum 8GB (16GB recommended)
- **CPU:** Modern multi-core processor (Intel/AMD)
- **GPU:** Optional but recommended (NVIDIA with CUDA support)
- **Camera:** USB webcam or built-in camera
- **Storage:** At least 5GB free space

---

## **Step 1: System Preparation**

### **1.1 Update System Packages**
```bash
# Update package lists and upgrade system
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential software-properties-common
```

### **1.2 Install Python 3.11**
```bash
# Add deadsnakes PPA for Python 3.11 (if not available)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and development tools
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Verify installation
python3.11 --version  # Should show: Python 3.11.x
```

### **1.3 Install System Dependencies**

#### **OpenCV and Computer Vision Libraries:**
```bash
# Core OpenCV dependencies
sudo apt install -y libopencv-dev python3-opencv

# Additional image processing libraries
sudo apt install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx

# Video and multimedia support
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev libgtk-3-dev

# Math and scientific computing
sudo apt install -y libatlas-base-dev gfortran
```

#### **Camera and Video Support:**
```bash
# Video4Linux utilities for camera management
sudo apt install -y v4l-utils

# Additional camera drivers
sudo apt install -y libv4l-0 libv4l2rds0

# Check available cameras
v4l2-ctl --list-devices
```

#### **GUI and Display Support:**
```bash
# Tkinter for GUI components
sudo apt install -y python3-tk python3-tkinter

# X11 development libraries (for display)
sudo apt install -y libx11-dev libxext-dev libxfixes-dev libxi-dev libxrandr-dev

# Font support
sudo apt install -y fonts-dejavu-core fontconfig
```

### **1.4 GPU Support (Optional but Recommended)**

#### **For NVIDIA GPUs:**
```bash
# Check if NVIDIA GPU is available
lspci | grep -i nvidia

# Install NVIDIA drivers (if not already installed)
sudo apt install -y nvidia-driver-535  # Use latest stable version

# Install CUDA toolkit (for GPU acceleration)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-2

# Add CUDA to PATH (add to ~/.bashrc)
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify CUDA installation
nvcc --version
nvidia-smi
```

---

## **Step 2: Project Setup**

### **2.1 Create Project Directory**
```bash
# Create project directory
mkdir -p ~/Projects/person_tracker
cd ~/Projects/person_tracker

# Copy your project files here
# (Download or transfer all .py files, requirements.txt, etc.)
```

### **2.2 Create Virtual Environment**
```bash
# Create Python 3.11 virtual environment
python3.11 -m venv gestureModel

# Activate the environment
source gestureModel/bin/activate

# Verify you're in the correct environment
which python  # Should point to gestureModel/bin/python
python --version  # Should show Python 3.11.x
```

### **2.3 Upgrade pip and Install Wheel**
```bash
# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Verify pip version
pip --version
```

---

## **Step 3: Install Python Dependencies**

### **3.1 Install PyTorch (GPU Support)**
```bash
# For NVIDIA GPU support (recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CPU-only (if no NVIDIA GPU)
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Verify PyTorch installation
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### **3.2 Install Core Dependencies**
```bash
# Install main requirements
pip install opencv-python>=4.8.0
pip install numpy>=1.21.0
pip install Pillow>=8.3.0
pip install mediapipe>=0.10.0
pip install ultralytics>=8.0.0
pip install urllib3>=1.26.0

# Install person re-identification
pip install torchreid>=1.4.0
```

### **3.3 Alternative: Install from requirements.txt**
```bash
# If you have the requirements.txt file
pip install -r requirements.txt
```

### **3.4 Verify Installation**
```bash
# Test all major components
python -c "
import cv2
import numpy as np
import mediapipe as mp
import torch
import ultralytics
import torchreid
print('✅ All packages imported successfully!')
print(f'OpenCV: {cv2.__version__}')
print(f'MediaPipe: {mp.__version__}')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
```

---

## **Step 4: Camera Setup and Permissions**

### **4.1 Check Camera Access**
```bash
# List available cameras
ls /dev/video*

# Check camera details
v4l2-ctl --list-devices

# Test camera access
v4l2-ctl --device=/dev/video0 --all
```

### **4.2 Fix Camera Permissions (if needed)**
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Apply group membership (logout/login or reboot)
newgrp video

# Verify group membership
groups | grep video
```

### **4.3 Test Camera with OpenCV**
```bash
# Quick camera test
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print('✅ Camera working! Frame shape:', frame.shape)
else:
    print('❌ Camera not accessible')
cap.release()
"
```

---

## **Step 5: Project Configuration**

### **5.1 Copy Project Files**
Make sure you have all these files in your project directory:
```bash
# Required files:
ls -la
# Should show:
# main.py
# config.py
# person_detector.py
# gesture_detector.py
# person_reid.py
# target_tracker.py
# direction_controller.py
# direction_gui.py
# utils.py
# requirements.txt
```

### **5.2 Download Model Files**
```bash
# The application will auto-download these on first run:
# - gesture_recognizer.task
# - hand_landmarker.task  
# - pose_landmarker_lite.task
# - yolov8n.pt

# Ensure internet connection for auto-download
curl -I https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task
```

### **5.3 Set Executable Permissions**
```bash
# Make main script executable
chmod +x main.py

# Verify file permissions
ls -la main.py
```

---

## **Step 6: First Run and Testing**

### **6.1 Initial Test Run**
```bash
# Activate environment (if not already active)
source gestureModel/bin/activate

# Run the application
python main.py

# Expected output:
# [SYSTEM] Person Lock System initialized with PERSISTENT ReID tracking
# [SYSTEM] Locking Mode: FIST_PALM (Fist + Palm proximity-based)
# [SYSTEM] Proximity thresholds: 400px OR 30% of frame diagonal
# [SYSTEM] Lock Gesture: FIST + PALM (close together)
```

### **6.2 Test Different Camera Sources**
```bash
# Test camera index 0
python main.py --source 0

# Test camera index 1 (if you have multiple cameras)
python main.py --source 1

# Test with specific device
python main.py --source /dev/video0
```

### **6.3 Test with Different Options**
```bash
# CPU-only mode
python main.py --device cpu

# Debug mode
python main.py --debug

# Lower resolution for better performance
python main.py --width 640 --height 480

# GPU mode (if CUDA available)
python main.py --device cuda
```

---

## **Step 7: Performance Optimization**

### **7.1 GPU Acceleration**
```bash
# Verify GPU usage during runtime
nvidia-smi  # Run in another terminal while app is running

# Check PyTorch GPU usage
python -c "
import torch
print(f'CUDA devices: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'Current device: {torch.cuda.get_device_name(0)}')
"
```

### **7.2 System Resource Optimization**
```bash
# Monitor system resources
htop  # Install with: sudo apt install htop

# Adjust CPU governor for performance
sudo apt install cpufrequtils
sudo cpufreq-set -g performance

# Increase camera buffer size (if needed)
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## **Step 8: Troubleshooting**

### **8.1 Common Issues and Solutions**

#### **Camera Not Detected:**
```bash
# Check camera permissions
ls -la /dev/video*
sudo chmod 666 /dev/video0  # Temporary fix

# Restart video services
sudo systemctl restart systemd-udevd
```

#### **MediaPipe Installation Issues:**
```bash
# Reinstall MediaPipe with specific version
pip uninstall mediapipe
pip install mediapipe==0.10.7
```

#### **GUI Display Issues:**
```bash
# Install additional GUI libraries
sudo apt install python3-pil.imagetk

# For headless systems, install virtual display
sudo apt install xvfb
export DISPLAY=:0
```

#### **CUDA/GPU Issues:**
```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall CUDA-compatible PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### **8.2 Performance Issues:**
```bash
# Lower confidence thresholds for better detection
python main.py --conf 0.3 --gesture_conf 0.4

# Reduce video resolution
python main.py --width 640 --height 480

# CPU-only mode for compatibility
python main.py --device cpu
```

---

## **Step 9: Creating Desktop Launcher (Optional)**

### **9.1 Create Desktop Entry**
```bash
# Create desktop file
cat > ~/.local/share/applications/person-tracker.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Person Tracker
Comment=Gesture-based person tracking system
Exec=/home/$USER/Projects/person_tracker/gestureModel/bin/python /home/$USER/Projects/person_tracker/main.py
Icon=applications-multimedia
Terminal=true
Categories=AudioVideo;Graphics;
EOF

# Make it executable
chmod +x ~/.local/share/applications/person-tracker.desktop
```

### **9.2 Create Startup Script**
```bash
# Create convenient startup script
cat > ~/start-person-tracker.sh << 'EOF'
#!/bin/bash
cd ~/Projects/person_tracker
source gestureModel/bin/activate
python main.py "$@"
EOF

# Make it executable
chmod +x ~/start-person-tracker.sh

# Usage:
# ./start-person-tracker.sh
# ./start-person-tracker.sh --source 1 --debug
```

---

## **Step 10: Usage Examples**

### **10.1 Basic Usage**
```bash
# Standard run
./start-person-tracker.sh

# With specific camera
./start-person-tracker.sh --source 1

# Debug mode
./start-person-tracker.sh --debug
```

### **10.2 Configuration Changes**
```bash
# Edit configuration
nano config.py

# Change locking mode to pointing up
# LOCKING_MODE = "POINTING_UP"

# Adjust sensitivity
# FIST_PALM_MIN_CONFIDENCE = 0.45
```

---

## **Step 11: Uninstallation (Optional)**

### **11.1 Remove Virtual Environment**
```bash
# Remove the virtual environment
rm -rf ~/Projects/person_tracker/gestureModel

# Remove project directory
rm -rf ~/Projects/person_tracker
```

### **11.2 Remove System Dependencies (Optional)**
```bash
# Remove CUDA (if installed)
sudo apt remove --purge cuda* nvidia-cuda-*

# Remove camera utilities
sudo apt remove v4l-utils

# Remove development libraries
sudo apt autoremove
```

---

## **Support and Documentation**

### **📚 Additional Resources:**
- **Project Documentation:** See `IMPLEMENTATION_SUMMARY.md`
- **Testing Guide:** Follow the testing procedures in project docs
- **Configuration:** All settings in `config.py`

### **🐛 Getting Help:**
- Check console output for error messages
- Verify camera access with `v4l2-ctl --list-devices`
- Test with `--debug` flag for detailed logging
- Monitor system resources with `htop`

### **✅ Success Indicators:**
- Application starts without errors
- Camera feed displays in window
- Console shows current locking mode
- Hand gestures are detected and logged
- Direction control window appears

---

**🎉 Installation Complete!**

Your Person Tracker system is now ready to use on Ubuntu Linux. The system supports both fist+palm gesture locking and the original pointing up fallback mode, with full GPU acceleration and camera support.
