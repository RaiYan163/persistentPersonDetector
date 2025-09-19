#!/usr/bin/env python3
"""
Serial Communication Test Script

This script tests the serial communication functionality independently
to verify that your Arduino/microcontroller is receiving the correct data.
"""

import time
import sys
import os

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from direction_controller import SerialController, SERIAL_COMMAND_MAP
    print("✅ Successfully imported SerialController")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project directory")
    sys.exit(1)

def test_serial_communication(port=None):
    """Test serial communication with different commands"""
    
    print("🔌 Serial Communication Test")
    print("=" * 40)
    
    # Use direct serial connection like send.py
    if port is None:
        port = "COM3"  # Default port
    
    print(f"Connecting to {port} at 115200 baud...")
    
    try:
        import serial
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # give time for Arduino to reset
        print(f"✅ Connected to {port} at 115200 baud")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test sequence - send as strings like send.py
    test_commands = [
        ("Default/None", "0"),
        ("Forward", "1"),
        ("Right", "2"),
        ("Backward", "3"),
        ("Left", "4"),
        ("Button A", "5"),
        ("Button B", "6"),
        ("Button C", "7"),
        ("Default/None", "0"),
    ]
    
    print("📡 Sending test sequence...")
    print("Watch your Arduino Serial Monitor for received values!")
    print()
    
    for i, (name, code) in enumerate(test_commands):
        print(f"Step {i+1}: Sending {name} (code: {code})")
        ser.write(code.encode())  # Send as encoded string like send.py
        ser.flush()
        print(f"Sent: {code}")
        time.sleep(1)  # Wait 1 second between commands
    
    print()
    print("🔄 Testing continuous default (0) transmission...")
    print("This should send '0' every 500ms for 5 seconds")
    print("Watch your Arduino - you should see repeated '0' values")
    
    start_time = time.time()
    while time.time() - start_time < 5:
        ser.write("0".encode())  # Send as encoded string
        ser.flush()
        print(".", end="", flush=True)
        time.sleep(0.5)
    
    print()
    print("✅ Test completed!")
    print("Check your Arduino Serial Monitor to verify all commands were received")
    
    # Cleanup
    ser.close()
    return True

def main():
    """Main test function"""
    print("🎯 Serial Communication Test Tool")
    print("=" * 50)
    
    # Check if port specified
    port = None
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"Using specified port: {port}")
    else:
        print("Auto-detecting serial port...")
    
    print()
    
    try:
        success = test_serial_communication(port)
        if success:
            print("\n🎉 Test completed successfully!")
            print("\nNext steps:")
            print("1. Verify all commands (0-7) were received on Arduino")
            print("2. Run the main gesture system: python start_person_tracker.py --direct")
            print("3. Lock onto a person and test gestures")
        else:
            print("\n❌ Test failed!")
            print("\nTroubleshooting:")
            print("1. Check Arduino is connected via USB")
            print("2. Verify correct port (use Device Manager on Windows)")
            print("3. Make sure Arduino Serial Monitor is closed")
            print("4. Try specifying port manually: python test_serial.py COM3")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
