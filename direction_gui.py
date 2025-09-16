# direction_gui.py - Simple GUI window to display direction commands

import tkinter as tk
from tkinter import font
import threading
import time
from typing import Optional, Dict

class DirectionGUI:
    """
    Simple GUI window that displays current direction commands in large text.
    Shows only Forward/Backward/Pause and Left/Right commands.
    """
    
    def __init__(self):
        """Initialize the direction display GUI"""
        self.window = None
        self.fb_label = None
        self.lr_label = None
        self.status_label = None
        self.is_running = False
        self.current_fb = "None"
        self.current_lr = "None"
        self.is_locked = False
        
        # Button states
        self.button_states = {
            'button_a': "None",
            'button_b': "None", 
            'button_c': "None"
        }
        
        # Thread for GUI
        self.gui_thread = None
        
    def start_gui(self):
        """Start the GUI in a separate thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.gui_thread = threading.Thread(target=self._run_gui, daemon=True)
        self.gui_thread.start()
        
        # Wait a moment for GUI to initialize
        time.sleep(0.5)
        print("[GUI] Direction display window started")
    
    def stop_gui(self):
        """Stop the GUI"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.window:
            self.window.quit()
        print("[GUI] Direction display window stopped")
    
    def _run_gui(self):
        """Run the GUI main loop"""
        # Create main window
        self.window = tk.Tk()
        self.window.title("Direction Control")
        self.window.geometry("500x400")  # Increased size for button controls
        self.window.configure(bg='black')
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Configure fonts
        big_font = font.Font(family="Arial", size=24, weight="bold")
        medium_font = font.Font(family="Arial", size=16, weight="bold")
        small_font = font.Font(family="Arial", size=12)
        
        # Status label
        self.status_label = tk.Label(
            self.window, 
            text="WAITING FOR LOCK", 
            font=medium_font,
            fg='yellow',
            bg='black'
        )
        self.status_label.pack(pady=10)
        
        # Forward/Backward label
        tk.Label(
            self.window, 
            text="FORWARD/BACKWARD:", 
            font=small_font,
            fg='white',
            bg='black'
        ).pack(pady=(20, 5))
        
        self.fb_label = tk.Label(
            self.window, 
            text="NONE", 
            font=big_font,
            fg='cyan',
            bg='black'
        )
        self.fb_label.pack(pady=5)
        
        # Left/Right label
        tk.Label(
            self.window, 
            text="LEFT/RIGHT:", 
            font=small_font,
            fg='white',
            bg='black'
        ).pack(pady=(20, 5))
        
        self.lr_label = tk.Label(
            self.window, 
            text="NONE", 
            font=big_font,
            fg='lime',
            bg='black'
        )
        self.lr_label.pack(pady=5)
        
        # Button Controls Section
        tk.Label(
            self.window, 
            text="BUTTON CONTROLS:", 
            font=small_font,
            fg='white',
            bg='black'
        ).pack(pady=(20, 5))
        
        # Button controls frame
        button_frame = tk.Frame(self.window, bg='black')
        button_frame.pack(pady=5)
        
        # Button A
        self.button_a_label = tk.Label(button_frame, text="A", 
                                     font=font.Font(family="Arial", size=18),
                                     fg='gray', bg='black')
        self.button_a_label.pack(side='left', padx=20)
        
        # Button B  
        self.button_b_label = tk.Label(button_frame, text="B",
                                     font=font.Font(family="Arial", size=18),
                                     fg='gray', bg='black')
        self.button_b_label.pack(side='left', padx=20)
        
        # Button C
        self.button_c_label = tk.Label(button_frame, text="C",
                                     font=font.Font(family="Arial", size=18),
                                     fg='gray', bg='black')
        self.button_c_label.pack(side='left', padx=20)
        
        # Instructions removed as requested by user
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Start the update loop
        self._update_display()
        
        # Run GUI
        try:
            self.window.mainloop()
        except Exception as e:
            print(f"[GUI] Error: {e}")
        finally:
            self.is_running = False
    
    def _update_display(self):
        """Update the display with current commands"""
        if not self.is_running or not self.window:
            return
        
        try:
            # Update status
            if self.is_locked:
                self.status_label.config(text="DIRECTION CONTROL ACTIVE", fg='lime')
            else:
                self.status_label.config(text="WAITING FOR LOCK", fg='yellow')
            
            # Update forward/backward
            fb_text = self.current_fb.upper() if self.current_fb != "None" else "NONE"
            self.fb_label.config(text=fb_text)
            
            # Color coding for forward/backward (fixed to match uppercase commands)
            if self.current_fb == "FORWARD":
                self.fb_label.config(fg='lime')
            elif self.current_fb == "BACKWARD":
                self.fb_label.config(fg='red')
            elif self.current_fb == "PAUSE":
                self.fb_label.config(fg='yellow')
            else:
                self.fb_label.config(fg='gray')
            
            # Update left/right
            lr_text = self.current_lr.upper() if self.current_lr != "None" else "NONE"
            self.lr_label.config(text=lr_text)
            
            # Color coding for left/right (fixed to match uppercase commands)
            if self.current_lr == "LEFT":
                self.lr_label.config(fg='orange')
            elif self.current_lr == "RIGHT":
                self.lr_label.config(fg='cyan')
            else:
                self.lr_label.config(fg='gray')
            
            # Update button controls
            self._update_button_displays()
            
            # Schedule next update
            self.window.after(100, self._update_display)  # Update every 100ms
            
        except Exception as e:
            print(f"[GUI] Update error: {e}")
    
    def _update_button_displays(self):
        """Update button control displays"""
        try:
            # Import font locally
            from tkinter import font
            
            # Button A
            if self.button_states['button_a'] == 'BUTTON_A':
                self.button_a_label.config(text="A", fg='lime', 
                                         font=font.Font(family="Arial", size=18, weight="bold"))
            else:
                self.button_a_label.config(text="A", fg='gray',
                                         font=font.Font(family="Arial", size=18))
            
            # Button B  
            if self.button_states['button_b'] == 'BUTTON_B':
                self.button_b_label.config(text="B", fg='lime',
                                         font=font.Font(family="Arial", size=18, weight="bold"))
            else:
                self.button_b_label.config(text="B", fg='gray',
                                         font=font.Font(family="Arial", size=18))
            
            # Button C
            if self.button_states['button_c'] == 'BUTTON_C':
                self.button_c_label.config(text="C", fg='lime',
                                         font=font.Font(family="Arial", size=18, weight="bold"))
            else:
                self.button_c_label.config(text="C", fg='gray',
                                         font=font.Font(family="Arial", size=18))
                
        except Exception as e:
            print(f"[GUI] Button update error: {e}")
    
    def _on_close(self):
        """Handle window close event"""
        self.stop_gui()
    
    def update_commands(self, fb_command: Optional[str], lr_command: Optional[str], button_states: Optional[Dict] = None):
        """
        Update the displayed commands.
        
        Args:
            fb_command: Forward/Backward/Pause command or None
            lr_command: Left/Right command or None
            button_states: Dictionary with button states {'button_a': cmd, 'button_b': cmd, 'button_c': cmd}
        """
        self.current_fb = fb_command if fb_command else "None"
        self.current_lr = lr_command if lr_command else "None"
        
        # Update button states if provided
        if button_states:
            self.button_states = {
                'button_a': button_states.get('button_a', 'None'),
                'button_b': button_states.get('button_b', 'None'),
                'button_c': button_states.get('button_c', 'None')
            }
            # Force immediate GUI update for button states
            if hasattr(self, 'window') and self.window:
                self._update_button_displays()
    
    def set_lock_status(self, is_locked: bool):
        """
        Update the lock status.
        
        Args:
            is_locked: Whether person tracking is currently locked
        """
        self.is_locked = is_locked
        
        if not is_locked:
            # Reset commands when unlocked
            self.current_fb = "None"
            self.current_lr = "None"
    
    def is_gui_running(self) -> bool:
        """Check if GUI is currently running"""
        return self.is_running

# Global instance for easy access
direction_gui = DirectionGUI()