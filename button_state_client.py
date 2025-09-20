# button_state_client.py - TCP client for monitoring button state updates

import socket
import json
import time
import argparse

class ButtonStateClient:
    """TCP client that connects to button state server and displays updates"""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.latest_state = None

    def connect(self):
        """Connect to the button state server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"[CLIENT] Connected to server at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            print(f"[CLIENT] Error: Could not connect to server at {self.host}:{self.port}")
            print("[CLIENT] Make sure the main gesture system is running with button state server")
            return False
        except Exception as e:
            print(f"[CLIENT] An unexpected error occurred during connection: {e}")
            return False

    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("[CLIENT] Disconnected from server")
        
    def listen(self):
        """Listen for button state updates from server"""
        if not self.connected:
            print("[CLIENT] Not connected to server")
            return
            
        print("[CLIENT] Listening for button state updates...")
        print("=" * 60)
        print("Format: [timestamp] button_state | parsed_buttons")
        print("-" * 60)
        
        try:
            while self.connected:
                # Receive data from server
                data = self.socket.recv(1024).decode()
                if not data:
                    print("[CLIENT] Server disconnected.")
                    break
                    
                # Process each line (in case multiple messages received)
                for line in data.strip().split('\n'):
                    if line:
                        try:
                            message = json.loads(line)
                            self._display_message(message)
                            self.latest_state = message  # Store latest state
                        except json.JSONDecodeError:
                            print(f"[CLIENT] Invalid JSON received: {line}")
                            
        except KeyboardInterrupt:
            print("\n[CLIENT] Stopped by user")
        except Exception as e:
            print(f"[CLIENT] Error: {e}")
        finally:
            self.disconnect()
            
    def _display_message(self, message):
        """Display the received message"""
        timestamp = message.get('timestamp', 0)
        button_state = message.get('button_state', '')
        parsed = message.get('parsed', {})
        
        # Get the original string with \n for display
        original_state = button_state + '\n'
        
        # Show which buttons are active
        active_buttons = []
        if parsed.get('forward'): active_buttons.append('FORWARD')
        if parsed.get('right'): active_buttons.append('RIGHT')
        if parsed.get('backward'): active_buttons.append('BACKWARD')
        if parsed.get('left'): active_buttons.append('LEFT')
        if parsed.get('button_a'): active_buttons.append('BUTTON_A')
        if parsed.get('button_b'): active_buttons.append('BUTTON_B')
        if parsed.get('button_c'): active_buttons.append('BUTTON_C')
        
        active_str = ', '.join(active_buttons) if active_buttons else 'NONE'
        print(f"[{timestamp:.3f}] {original_state!r} | {active_str}")
            
    def get_latest_state(self):
        """Get the latest button state (non-blocking)"""
        return self.latest_state

def main():
    """Main function for command line usage"""
    print("Button State Client")
    print("=" * 50)
    print("Connecting to: localhost:8888")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    client = ButtonStateClient()
    
    if client.connect():
        client.listen()
    else:
        print("\nTroubleshooting:")
        print("1. Make sure main.py is running with button state server")
        print("2. Check if the server is listening on the correct port")
        print("3. Try running: python button_state_server.py (standalone test)")

if __name__ == "__main__":
    main()
