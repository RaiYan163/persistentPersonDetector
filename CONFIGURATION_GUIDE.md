# 🎮 Gesture Configuration Guide

## Overview

The Person Tracker now includes a **Configuration GUI** that allows you to customize gesture mappings before starting the tracking application. This makes the system highly flexible and personalized to your preferences.

## 🚀 Quick Start

### Method 1: Configuration GUI First (Recommended)
```bash
python start_person_tracker.py
```
This will:
1. Open the Configuration GUI
2. Allow you to customize gesture mappings
3. Start the Person Tracker with your settings

### Method 2: Direct Start (Use Existing Config)
```bash
python start_person_tracker.py --direct
```
This will start the tracker directly with existing or default settings.

### Method 3: Configuration Only
```bash
python start_person_tracker.py --config
```
This opens only the configuration GUI without starting the tracker.

## 📋 Configuration GUI Features

### **Tab 1: Lock/Unlock Configuration**
- **Lock Gesture 1 & 2**: Choose which two gestures lock onto a person
- **Unlock Gesture 1 & 2**: Choose which two gestures unlock the person
- **Proximity Requirements**: Whether gestures must be close together

### **Tab 2: Direction Control Configuration**
Configure which gestures control movement:

**Available Hand Gestures:**
- `Open_Palm` ✋ - Open hand, palm facing camera
- `Closed_Fist` ✊ - Closed fist
- `Thumb_Up` 👍 - Thumbs up gesture  
- `Thumb_Down` 👎 - Thumbs down gesture
- `Victory` ✌️ - Peace/Victory sign
- `Pointing_Up` ☝️ - Index finger pointing up
- `ILoveYou` 🤟 - I Love You sign

**Available Pose Gestures:**
- `Right_Elbow_Extended` - Right arm extended (angle > 90°)
- `Right_Elbow_Bent` - Right arm bent inward (angle < 90°)
- `Left_Elbow_Extended` - Left arm extended (angle > 90°)
- `Left_Elbow_Bent` - Left arm bent inward (angle < 90°)

**Available Commands:**
- `FORWARD` - Move forward
- `BACKWARD` - Move backward
- `LEFT` - Turn left
- `RIGHT` - Turn right
- `PAUSE` - Pause/stop
- `NONE` - No action

### **Tab 3: Preview**
Shows your complete configuration before starting the application.

## 🔧 Configuration Examples

### Example 1: Default Configuration
```
Lock: Closed_Fist + Open_Palm
Unlock: Victory + Victory
Direction Control:
- Open_Palm → FORWARD
- Closed_Fist → BACKWARD
- Right_Elbow_Extended → RIGHT
- Right_Elbow_Bent → LEFT
```

### Example 2: Custom Thumbs Configuration
```
Lock: Thumb_Up + Thumb_Down
Unlock: Victory + Victory
Direction Control:
- Thumb_Up → FORWARD
- Thumb_Down → BACKWARD
- Left_Elbow_Extended → RIGHT
- Left_Elbow_Bent → LEFT
```

### Example 3: Mixed Gesture Configuration
```
Lock: Pointing_Up + Open_Palm
Unlock: ILoveYou + ILoveYou
Direction Control:
- Victory → FORWARD
- Closed_Fist → BACKWARD
- Right_Elbow_Extended → RIGHT
- Left_Elbow_Extended → LEFT
```

## 💾 Configuration Storage

- **User Config**: `gesture_config.json` - Your saved settings
- **Runtime Config**: `runtime_gesture_config.json` - Active settings during tracking
- **Auto-save**: Configuration is automatically saved when you start tracking

## 🎯 Usage Workflow

1. **Run Configuration GUI**:
   ```bash
   python start_person_tracker.py
   ```

2. **Configure Lock/Unlock Gestures**:
   - Choose your preferred locking gesture combination
   - Set proximity requirements
   - Choose unlock gesture combination

3. **Configure Direction Control**:
   - Map hand gestures to FORWARD/BACKWARD commands
   - Map pose gestures to LEFT/RIGHT commands
   - Set unused gestures to NONE

4. **Preview & Save**:
   - Review your configuration in the Preview tab
   - Click "Save Config" to store settings
   - Click "Start Person Tracker" to begin

5. **Use Your Custom Gestures**:
   - The tracking system now uses your custom mappings
   - Direction GUI shows your gesture names
   - Console output reflects your chosen gestures

## 🔄 Modifying Configuration

### During Runtime
The system loads configuration at startup. To change mappings:
1. Stop the current session
2. Run the configuration GUI again
3. Modify your settings
4. Restart the tracker

### File-Based Editing (Advanced)
You can directly edit `gesture_config.json`:
```json
{
  "Lock_Gesture_1": "Thumb_Up",
  "Lock_Gesture_2": "Open_Palm",
  "Open_Palm": "FORWARD",
  "Closed_Fist": "BACKWARD",
  "Right_Elbow_Extended": "RIGHT",
  "Right_Elbow_Bent": "LEFT"
}
```

## 🛠️ Advanced Features

### Configuration Loading
- **Auto-load**: Previous settings are automatically loaded
- **Default fallback**: System uses sensible defaults if no config exists
- **Error handling**: Invalid configurations fall back to defaults

### Dynamic Updates
- **Runtime adaptation**: Direction controller adapts to new mappings
- **GUI updates**: Direction display shows your custom gesture names
- **Console feedback**: Debug output uses your gesture names

### Multiple Configurations
- **Save/Load**: Save different configurations for different users
- **Quick switch**: Easy switching between configuration profiles
- **Backup**: Keep multiple configuration versions

## 🎮 Tips for Effective Configuration

### Choosing Lock Gestures
- **Distinct**: Choose gestures that are clearly different
- **Comfortable**: Pick gestures easy to hold for 2 seconds
- **Reliable**: Use gestures MediaPipe detects consistently

### Choosing Direction Gestures
- **Intuitive**: Map gestures to commands that feel natural
- **Conflict-free**: Avoid using unlock gestures for direction control
- **Accessible**: Choose gestures you can perform reliably

### Testing Your Configuration
1. Start with simple mappings
2. Test each gesture individually
3. Verify proximity requirements work
4. Adjust confidence thresholds if needed

## 📞 Troubleshooting

### Configuration GUI Not Opening
```bash
# Check if file exists
ls gesture_config_gui.py

# Run directly
python gesture_config_gui.py
```

### Gestures Not Working
1. Check confidence thresholds in main application
2. Verify good lighting conditions
3. Ensure clear hand visibility
4. Test individual gestures first

### Configuration Not Loading
1. Check for `runtime_gesture_config.json`
2. Verify JSON syntax if editing manually
3. Check file permissions
4. Use "Reset to Default" in GUI

## 🎯 Next Steps

After configuring your gestures:
1. Practice your custom gesture combinations
2. Adjust timing and confidence settings if needed
3. Create backup configurations for different scenarios
4. Share effective configurations with other users

---

**🎉 Enjoy your personalized gesture control experience!**

The configuration system makes the Person Tracker truly yours - set it up exactly how you want it to work.
