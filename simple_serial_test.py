#!/usr/bin/env python3
"""
Simple Serial Test - No Dependencies Required
Tests serial communication without needing mediapipe or other heavy dependencies.
"""

import time
import sys

# Configuration - Change these values
DEFAULT_PORT = "COM3"  # Change to your Arduino port
DEFAULT_BAUD = 115200  # Change to your desired baud rate

def test_serial_simple():
    """Simple serial test without external dependencies"""
    try:
        import serial
        print("✅ pyserial is available")
    except ImportError:
        print("❌ pyserial not installed. Install with: pip install pyserial")
        return False
    
    # Test serial ports
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            print("❌ No serial ports detected")
            return False
        
        print(f"📡 Found {len(ports)} serial port(s):")
        for i, port in enumerate(ports):
            print(f"  {i+1}. {port.device} - {port.description}")
        
        # Try to connect to default port first, then first available
        test_port = DEFAULT_PORT
        if not any(p.device == DEFAULT_PORT for p in ports):
            test_port = ports[0].device
            print(f"⚠️ Default port {DEFAULT_PORT} not found, using {test_port}")
        
        print(f"\n🔌 Testing connection to {test_port} at {DEFAULT_BAUD} baud...")
        
        try:
            ser = serial.Serial(
                port=test_port,
                baudrate=DEFAULT_BAUD,
                timeout=1,
                write_timeout=1
            )
            print(f"✅ Connected to {test_port} at {DEFAULT_BAUD} baud")
            
            # Send test sequence
            test_commands = [0, 1, 2, 3, 4, 5, 6, 7, 0]
            print("\n📤 Sending test sequence...")
            print("Watch your Arduino Serial Monitor!")
            print("Expected: 0, 1, 2, 3, 4, 5, 6, 7, 0")
            print()
            
            for i, cmd in enumerate(test_commands):
                print(f"Sending command {i+1}: {cmd}")
                ser.write(bytes([cmd]))
                ser.flush()
                time.sleep(1)
            
            print("\n🔄 Testing continuous '0' transmission...")
            print("Sending '0' every 500ms for 5 seconds...")
            start_time = time.time()
            while time.time() - start_time < 5:
                ser.write(bytes([0]))
                ser.flush()
                print(".", end="", flush=True)
                time.sleep(0.5)
            
            print("\n✅ Test completed!")
            ser.close()
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Port detection error: {e}")
        return False

def main():
    print("🔌 Simple Serial Communication Test")
    print("=" * 40)
    print(f"Default Port: {DEFAULT_PORT}")
    print(f"Default Baud: {DEFAULT_BAUD}")
    print("This test sends commands 0-7 to your Arduino")
    print("Make sure Arduino Serial Monitor is open at the correct baud rate")
    print()
    
    success = test_serial_simple()
    
    if success:
        print("\n🎉 Serial test completed successfully!")
        print("\nNext steps:")
        print("1. Check Arduino Serial Monitor for received values")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run full system: python start_person_tracker.py --direct")
    else:
        print("\n❌ Serial test failed!")
        print("\nTroubleshooting:")
        print("1. Install pyserial: pip install pyserial")
        print("2. Check Arduino is connected via USB")
        print("3. Close Arduino IDE if open")
        print("4. Check Device Manager for COM port")
        print(f"5. Update DEFAULT_PORT in this file (currently: {DEFAULT_PORT})")

if __name__ == "__main__":
    main()
