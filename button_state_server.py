# button_state_server.py - TCP server for broadcasting button state updates

import socket
import threading
import time
import json
from button_state_shared import get_button_state, BUTTON_POSITIONS

class ButtonStateServer:
    """TCP server that broadcasts button state updates to connected clients"""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.clients = []
        self.running = False
        self.server_socket = None
        
    def start_server(self):
        """Start the button state server"""
        if self.running:
            return
            
        self.running = True
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        print(f"[BUTTON_SERVER] Server starting on {self.host}:{self.port}")
        
    def stop_server(self):
        """Stop the button state server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[BUTTON_SERVER] Server stopped")
        
    def _run_server(self):
        """Main server loop - accepts client connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            # Start broadcasting thread
            broadcast_thread = threading.Thread(target=self._broadcast_states, daemon=True)
            broadcast_thread.start()
            
            print(f"[BUTTON_SERVER] Waiting for clients on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"[BUTTON_SERVER] Client connected: {addr}")
                    self.clients.append(client_socket)
                except OSError:
                    # Server socket closed
                    break
                    
        except Exception as e:
            print(f"[BUTTON_SERVER] Error: {e}")
        finally:
            self._cleanup_clients()
            
    def _broadcast_states(self):
        """Continuously broadcast button states to all connected clients"""
        while self.running:
            try:
                current_state = get_button_state()
                timestamp = time.time()
                
                # Create message with timestamp and button state
                message = {
                    "timestamp": timestamp,
                    "button_state": current_state.strip(),
                    "parsed": self._parse_button_state(current_state)
                }
                
                message_str = json.dumps(message) + "\n"
                
                # Send to all connected clients
                disconnected_clients = []
                for client in self.clients:
                    try:
                        client.sendall(message_str.encode())
                    except (socket.error, BrokenPipeError):
                        disconnected_clients.append(client)
                
                # Remove disconnected clients
                for client in disconnected_clients:
                    if client in self.clients:
                        self.clients.remove(client)
                        try:
                            client.close()
                        except socket.error:
                            pass
                        print(f"[BUTTON_SERVER] Client disconnected.")
                
                time.sleep(0.05)  # 20Hz update rate
                
            except Exception as e:
                print(f"[BUTTON_SERVER] Broadcast error: {e}")
                time.sleep(0.1)
    
    def _parse_button_state(self, state_string):
        """Parse the button state string into a dictionary"""
        parsed = {}
        for button_name, pos_index in BUTTON_POSITIONS.items():
            # Adjust for 0-indexed string vs 1-indexed BUTTON_POSITIONS
            if 0 <= pos_index - 1 < len(state_string):
                parsed[button_name.lower()] = (state_string[pos_index - 1] == '1')
            else:
                parsed[button_name.lower()] = False
        
        # Add reserved positions
        for i in range(7, 10):  # Positions 7, 8, 9 (0-indexed)
            if 0 <= i < len(state_string):
                parsed[f"reserved_{i}"] = (state_string[i] == '1')
            else:
                parsed[f"reserved_{i}"] = False
                
        return parsed
    
    def _cleanup_clients(self):
        """Clean up all client connections"""
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
    def get_client_count(self):
        """Get number of connected clients"""
        return len(self.clients)

# Global server instance
button_server = ButtonStateServer()

def start_button_state_server():
    """Start the button state server"""
    button_server.start_server()
    
def stop_button_state_server():
    """Stop the button state server"""
    button_server.stop_server()
    
def get_server_status():
    """Get server status information"""
    return {
        "running": button_server.running,
        "clients": button_server.get_client_count(),
        "host": button_server.host,
        "port": button_server.port,
        "socket_bound": button_server.server_socket is not None
    }

if __name__ == "__main__":
    # Test the server standalone
    print("Starting Button State Server (Standalone Test)")
    print("=" * 50)
    
    start_button_state_server()
    
    try:
        while True:
            status = get_server_status()
            print(f"Server Status: Running={status['running']}, Clients={status['clients']}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        stop_button_state_server()
