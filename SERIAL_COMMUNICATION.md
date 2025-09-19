# Serial Communication Guide

This guide explains how to use the serial communication feature for streaming gesture commands to external devices (Arduino, microcontrollers, etc.).

## 🔌 Hardware Setup

1. **Connect your device** (Arduino/microcontroller) to computer via USB
2. **Note the serial port**:
   - **Windows**: Usually `COM3`, `COM4`, etc.
   - **Linux/Mac**: Usually `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.

## 📡 Command Protocol

The system streams **single byte commands** at **115200 baud rate**:

| Command | Code | Description |
|---------|------|-------------|
| Default/None | `0` | No gesture detected or paused |
| Forward | `1` | Forward movement gesture |
| Right | `2` | Right turn gesture |
| Backward | `3` | Backward movement gesture |
| Left | `4` | Left turn gesture |
| Button A | `5` | Button A gesture (e.g., Thumb Up) |
| Button B | `6` | Button B gesture (e.g., Thumb Down) |
| Button C | `7` | Button C gesture (e.g., Pointing Up) |

## 🚀 Usage Examples

### Auto-Detection (Recommended)
```bash
# Let the system auto-detect available serial ports
python start_person_tracker.py --direct
```

### Specify Serial Port
```bash
# Windows
python start_person_tracker.py --direct --serial_port COM3

# Linux/Mac  
python start_person_tracker.py --direct --serial_port /dev/ttyUSB0
```

### Run main.py directly
```bash
python main.py --serial_port COM3
```

## 🔧 Arduino Example Code

Here's a simple Arduino sketch to receive and process the commands:

```cpp
void setup() {
  Serial.begin(115200);  // Match baud rate
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    int command = Serial.read();
    
    switch(command) {
      case 0:
        // Default/No command
        digitalWrite(LED_BUILTIN, LOW);
        break;
        
      case 1:
        // Forward
        Serial.println("Moving Forward");
        digitalWrite(LED_BUILTIN, HIGH);
        break;
        
      case 2:
        // Right
        Serial.println("Turning Right");
        break;
        
      case 3:
        // Backward
        Serial.println("Moving Backward");
        break;
        
      case 4:
        // Left
        Serial.println("Turning Left");
        break;
        
      case 5:
        // Button A
        Serial.println("Button A Pressed");
        break;
        
      case 6:
        // Button B
        Serial.println("Button B Pressed");
        break;
        
      case 7:
        // Button C
        Serial.println("Button C Pressed");
        break;
    }
  }
}
```

## 🎛️ Command Priority

When multiple gestures are detected simultaneously, the system uses this priority order:

1. **Button Commands** (highest priority): A, B, C
2. **Forward/Backward Commands**: FORWARD, BACKWARD
3. **Left/Right Commands**: LEFT, RIGHT  
4. **Default**: `0` when no commands active

## 🧪 Testing Serial Communication

### Quick Test Script
Run the included test script to verify your setup:

```bash
# Auto-detect port
python test_serial.py

# Specify port manually
python test_serial.py COM3          # Windows
python test_serial.py /dev/ttyUSB0  # Linux/Mac
```

This will send a sequence of all commands (0-7) and verify reception.

### Manual Testing in Main Application
1. **Start the system**: `python start_person_tracker.py --direct`
2. **Press 'h' key** while running to send a test heartbeat (command: 0)
3. **Lock onto a person** and perform gestures to see real-time commands

### Expected Behavior
- **When idle**: Should receive `0` every 500ms
- **When gestures detected**: Should receive corresponding command codes (1-7)
- **When no gestures**: Should return to sending `0` periodically

## 🔍 Troubleshooting

### No Serial Connection
- **Check port name**: Use Device Manager (Windows) or `ls /dev/tty*` (Linux)
- **Install pyserial**: `pip install pyserial`
- **Check permissions**: On Linux, add user to `dialout` group
- **Run test script**: `python test_serial.py` to diagnose issues

### Commands Not Received
- **Verify baud rate**: Both ends must use 115200
- **Check wiring**: Ensure USB connection is stable
- **Monitor serial**: Use Arduino Serial Monitor to verify data
- **Test with script**: Run `python test_serial.py` first

### Auto-Detection Issues
- **Manually specify port**: Use `--serial_port` argument
- **Check available ports**: The system will list detected ports at startup
- **Use test script**: `python test_serial.py COM3` to test specific port

## 📊 Console Output

When serial communication is active, you'll see:

```
[SERIAL] Auto-detected port: COM3 (Arduino Uno)
[SERIAL] Connected to COM3 at 115200 baud
[DIRECTION] Hand Open_Palm -> FORWARD
[DIRECTION] Button A: Thumb_Up -> BUTTON_A
```

## 🛑 Disabling Serial Communication

Serial communication is automatically disabled if:
- No `--serial_port` specified and auto-detection finds no ports
- `pyserial` package not installed
- Connection fails

## 🔄 Integration with Existing Projects

The serial communication runs parallel to the existing console output and GUI. Your existing gesture detection workflow remains unchanged - serial streaming is an additional output channel.

## 📋 Requirements

- **Python package**: `pyserial>=3.5` (automatically installed with requirements.txt)
- **Hardware**: Any device supporting 115200 baud serial communication
- **OS**: Windows, Linux, macOS supported
