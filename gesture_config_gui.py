# gesture_config_gui.py - Configuration GUI for gesture mappings

import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from typing import Dict, Optional
import config

class GestureConfigGUI:
    """
    Configuration GUI for customizing gesture-to-command mappings before starting the main application.
    Allows users to configure locking/unlocking gestures and direction control mappings.
    """
    
    def __init__(self):
        """Initialize the configuration GUI"""
        self.window = None
        self.gesture_mappings = {}
        self.config_file = "gesture_config.json"
        
        # Available gestures (only implemented ones from the original code)
        # Victory is omitted as it's reserved for unlock
        self.available_gestures = {
            "Hand Gestures": [
                "Open_Palm",      # ✋ - Actually implemented
                "Closed_Fist",   # ✊ - Actually implemented
                "Thumb_Up",      # 👍 - Actually implemented
                "Thumb_Down",    # 👎 - Actually implemented
                "Pointing_Up"    # ☝️ - Actually implemented
            ],
            "Pose Gestures": [
                "Right_Elbow_Extended",  # > 90° - Actually implemented
                "Right_Elbow_Bent"       # < 90° - Actually implemented
            ]
        }
        
        # Available commands (directional + button commands)
        self.available_commands = ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "PAUSE", "BUTTON_A", "BUTTON_B", "BUTTON_C", "NONE"]
        
        # Default mappings (all gestures can map to any command)
        self.default_mappings = {
            "Open_Palm": "FORWARD",
            "Closed_Fist": "BACKWARD", 
            "Thumb_Up": "BUTTON_A",
            "Thumb_Down": "BUTTON_B",
            "Pointing_Up": "BUTTON_C",
            "Right_Elbow_Extended": "RIGHT",
            "Right_Elbow_Bent": "LEFT"
        }
        
        # GUI components
        self.gesture_vars = {}
        self.command_vars = {}
        
    def load_config(self):
        """Load configuration from file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.gesture_mappings = {**self.default_mappings, **saved_config}
                    print(f"[CONFIG] Loaded saved configuration from {self.config_file}")
            except Exception as e:
                print(f"[CONFIG] Error loading config: {e}, using defaults")
                self.gesture_mappings = self.default_mappings.copy()
        else:
            self.gesture_mappings = self.default_mappings.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.gesture_mappings, f, indent=2)
            print(f"[CONFIG] Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"[CONFIG] Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            return False
    
    def create_gui(self):
        """Create the main configuration GUI"""
        self.window = tk.Tk()
        self.window.title("Person Tracker - Gesture Configuration")
        self.window.geometry("900x750")  # Slightly larger to ensure button visibility
        self.window.configure(bg='#f0f0f0')
        
        # Make window non-resizable for consistent layout
        self.window.resizable(False, False)
        
        # Configure fonts
        title_font = font.Font(family="Arial", size=16, weight="bold")
        section_font = font.Font(family="Arial", size=12, weight="bold")
        normal_font = font.Font(family="Arial", size=10)
        
        # Main container
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🎮 Gesture Configuration", 
                              font=title_font, bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # Tab 1: Lock/Unlock Information (Read-only)
        lock_frame = tk.Frame(notebook, bg='white', padx=20, pady=20)
        notebook.add(lock_frame, text="ℹ️ Lock/Unlock Info")
        self.create_lock_unlock_tab(lock_frame, section_font, normal_font)
        
        # Tab 2: Direction Control Configuration
        direction_frame = tk.Frame(notebook, bg='white', padx=20, pady=20)
        notebook.add(direction_frame, text="🎮 Direction Control")
        self.create_direction_control_tab(direction_frame, section_font, normal_font)
        
        # Tab 3: Preview Current Mappings
        preview_frame = tk.Frame(notebook, bg='white', padx=20, pady=20)
        notebook.add(preview_frame, text="👁️ Preview")
        self.create_preview_tab(preview_frame, section_font, normal_font)
        
        # Separator before buttons
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=(10, 0))
        
        # Bottom buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(20, 10), side='bottom')  # Ensure it's always at bottom
        
        # Load, Save, Reset buttons
        tk.Button(button_frame, text="📁 Load Config", command=self.load_and_refresh,
                 bg='#3498db', fg='white', font=normal_font, padx=20).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="💾 Save Config", command=self.save_config,
                 bg='#2ecc71', fg='white', font=normal_font, padx=20).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="🔄 Reset to Default", command=self.reset_to_default,
                 bg='#e74c3c', fg='white', font=normal_font, padx=20).pack(side='left', padx=(0, 10))
        
        # Start button - Make it more prominent
        start_button = tk.Button(button_frame, text="🚀 START PERSON TRACKER", 
                               command=self.start_application,
                               bg='#27ae60', fg='white', font=section_font, padx=40, pady=15)
        start_button.pack(side='right', padx=(20, 0))
        
    def create_lock_unlock_tab(self, parent, section_font, normal_font):
        """Create the lock/unlock information tab (read-only display)"""
        
        # Information header
        info_header = tk.Label(parent, 
                             text="ℹ️ Lock and Unlock gestures are fixed and cannot be changed.\nThis tab shows the current system configuration.",
                             font=normal_font, bg='white', fg='#e67e22', justify='center')
        info_header.pack(pady=(0, 20))
        
        # Lock Configuration Section (Read-only display)
        lock_section = tk.LabelFrame(parent, text="🔒 Locking Information", 
                                   font=section_font, bg='white', fg='#2c3e50', padx=15, pady=15)
        lock_section.pack(fill='x', pady=(0, 20))
        
        # Current lock mode display
        current_mode = tk.Label(lock_section, 
                              text=f"Current Mode: {config.LOCKING_MODE}", 
                              font=section_font, bg='white', fg='#2c3e50')
        current_mode.pack(anchor='w', pady=(0, 15))
        
        # Lock gesture info (read-only)
        if config.LOCKING_MODE == "FIST_PALM":
            lock_info = tk.Text(lock_section, height=6, bg='#f8f9fa', fg='#2c3e50', 
                              font=normal_font, wrap='word', padx=10, pady=10)
            lock_info.pack(fill='x', pady=5)
            
            lock_text = """🔒 LOCKING SEQUENCE (Fixed):
1. Show Closed Fist (✊) with one hand
2. Show Open Palm (✋) with other hand  
3. Bring hands close together (within 250 pixels)
4. Hold position for 2.0 seconds
5. System will lock onto you"""
            
            lock_info.insert(1.0, lock_text)
            lock_info.config(state='disabled')  # Make read-only
            
        else:  # POINTING_UP mode
            lock_info = tk.Text(lock_section, height=4, bg='#f8f9fa', fg='#2c3e50',
                              font=normal_font, wrap='word', padx=10, pady=10)
            lock_info.pack(fill='x', pady=5)
            
            lock_text = """🔒 LOCKING SEQUENCE (Fixed):
1. Point index finger upward (☝️)
2. Hold position for 2.0 seconds
3. System will lock onto you"""
            
            lock_info.insert(1.0, lock_text)
            lock_info.config(state='disabled')  # Make read-only
        
        # Unlock Configuration Section (Read-only display)
        unlock_section = tk.LabelFrame(parent, text="🔓 Unlocking Information", 
                                     font=section_font, bg='white', fg='#2c3e50', padx=15, pady=15)
        unlock_section.pack(fill='x')
        
        # Unlock gesture info (read-only)
        unlock_info = tk.Text(unlock_section, height=6, bg='#f8f9fa', fg='#2c3e50',
                            font=normal_font, wrap='word', padx=10, pady=10)
        unlock_info.pack(fill='x', pady=5)
        
        unlock_text = """🔓 UNLOCKING SEQUENCE (Fixed):
1. Show Victory gesture (✌️) with both hands
2. Bring victory hands close together (within 300 pixels)
3. Hold position for 2.0 seconds
4. System verifies you are the locked person (ReID security)
5. System will unlock (only you can unlock yourself)"""
        
        unlock_info.insert(1.0, unlock_text)
        unlock_info.config(state='disabled')  # Make read-only
        
        # Security note
        security_note = tk.Label(unlock_section,
                               text="🛡️ Security: Only the originally locked person can unlock the system",
                               font=normal_font, bg='white', fg='#c0392b', justify='center')
        security_note.pack(pady=(10, 0))
    
    def create_direction_control_tab(self, parent, section_font, normal_font):
        """Create the direction control configuration tab"""
        # Instructions
        instruction_text = ("Configure which gestures control movement directions.\n"
                          "Each gesture can be mapped to: FORWARD, BACKWARD, LEFT, RIGHT, PAUSE, or NONE")
        instruction_label = tk.Label(parent, text=instruction_text, font=normal_font, 
                                   bg='white', fg='#7f8c8d', justify='left')
        instruction_label.pack(anchor='w', pady=(0, 20))
        
        # Hand Gestures Section
        hand_section = tk.LabelFrame(parent, text="👋 Hand Gestures", 
                                   font=section_font, bg='white', fg='#2c3e50', padx=15, pady=15)
        hand_section.pack(fill='x', pady=(0, 20))
        
        # Create hand gesture mappings
        for gesture in self.available_gestures["Hand Gestures"]:
            if gesture == "None":
                continue
                
            gesture_frame = tk.Frame(hand_section, bg='white')
            gesture_frame.pack(fill='x', pady=3)
            
            # Gesture name
            gesture_label = tk.Label(gesture_frame, text=f"{gesture}:", 
                                   font=normal_font, bg='white', width=20, anchor='w')
            gesture_label.pack(side='left')
            
            # Command selection
            current_command = self.gesture_mappings.get(gesture, "NONE")
            command_var = tk.StringVar(value=current_command)
            self.command_vars[gesture] = command_var
            
            command_combo = ttk.Combobox(gesture_frame, textvariable=command_var,
                                       values=self.available_commands, state="readonly", width=15)
            command_combo.pack(side='left', padx=(10, 0))
            
            # Description
            desc_text = self.get_gesture_description(gesture)
            desc_label = tk.Label(gesture_frame, text=desc_text, 
                                font=normal_font, bg='white', fg='#95a5a6')
            desc_label.pack(side='left', padx=(20, 0))
        
        # Pose Gestures Section
        pose_section = tk.LabelFrame(parent, text="🤸 Pose Gestures (Elbow Angles)", 
                                   font=section_font, bg='white', fg='#2c3e50', padx=15, pady=15)
        pose_section.pack(fill='x', pady=(0, 20))
        
        # Create pose gesture mappings
        for gesture in self.available_gestures["Pose Gestures"]:
            if gesture == "None":
                continue
                
            gesture_frame = tk.Frame(pose_section, bg='white')
            gesture_frame.pack(fill='x', pady=3)
            
            # Gesture name
            gesture_label = tk.Label(gesture_frame, text=f"{gesture}:", 
                                   font=normal_font, bg='white', width=20, anchor='w')
            gesture_label.pack(side='left')
            
            # Command selection
            current_command = self.gesture_mappings.get(gesture, "NONE")
            command_var = tk.StringVar(value=current_command)
            self.command_vars[gesture] = command_var
            
            command_combo = ttk.Combobox(gesture_frame, textvariable=command_var,
                                       values=self.available_commands, state="readonly", width=15)
            command_combo.pack(side='left', padx=(10, 0))
            
            # Description
            desc_text = self.get_gesture_description(gesture)
            desc_label = tk.Label(gesture_frame, text=desc_text, 
                                font=normal_font, bg='white', fg='#95a5a6')
            desc_label.pack(side='left', padx=(20, 0))
    
    def create_preview_tab(self, parent, section_font, normal_font):
        """Create the preview tab showing current mappings"""
        # Preview text area
        preview_frame = tk.Frame(parent, bg='white')
        preview_frame.pack(fill='both', expand=True)
        
        # Title
        preview_title = tk.Label(preview_frame, text="Current Configuration Preview", 
                               font=section_font, bg='white', fg='#2c3e50')
        preview_title.pack(pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = tk.Frame(preview_frame, bg='white')
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.preview_text = tk.Text(text_frame, yscrollcommand=scrollbar.set, 
                                  font=normal_font, bg='#f8f9fa', fg='#2c3e50',
                                  wrap='word', padx=10, pady=10)
        self.preview_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.preview_text.yview)
        
        # Refresh button
        refresh_button = tk.Button(preview_frame, text="🔄 Refresh Preview", 
                                 command=self.update_preview,
                                 bg='#3498db', fg='white', font=normal_font)
        refresh_button.pack(pady=(10, 0))
        
        # Initial preview
        self.update_preview()
    
    def get_gesture_description(self, gesture):
        """Get description for a gesture"""
        descriptions = {
            "Open_Palm": "✋ Open hand, palm facing camera",
            "Closed_Fist": "✊ Closed hand, fist",
            "Thumb_Up": "👍 Thumbs up gesture",
            "Thumb_Down": "👎 Thumbs down gesture", 
            "Pointing_Up": "☝️ Index finger pointing up",
            "Right_Elbow_Extended": "Right arm extended (angle > 90°)",
            "Right_Elbow_Bent": "Right arm bent inward (angle < 90°)"
        }
        return descriptions.get(gesture, "No description available")
    
    def update_preview(self):
        """Update the preview text with current configuration"""
        # Collect current values
        self.collect_current_values()
        
        preview_text = "🎮 GESTURE CONFIGURATION PREVIEW\n"
        preview_text += "=" * 50 + "\n\n"
        
        # Lock/Unlock section (Fixed - information only)
        preview_text += "🔒 LOCK/UNLOCK (FIXED - CANNOT BE CHANGED):\n"
        if config.LOCKING_MODE == "FIST_PALM":
            preview_text += "  Lock: Closed Fist (✊) + Open Palm (✋) - close together, hold 2s\n"
        else:
            preview_text += "  Lock: Pointing Up (☝️) - hold 2s\n"
        preview_text += "  Unlock: Victory (✌️) + Victory (✌️) - close together, hold 2s\n"
        preview_text += "  Security: Only locked person can unlock (ReID verification)\n\n"
        
        # Direction control section (Configurable)
        preview_text += "🎮 DIRECTION CONTROL MAPPING (CONFIGURABLE):\n"
        
        # Hand gestures
        preview_text += "  Hand Gestures:\n"
        hand_count = 0
        for gesture in self.available_gestures["Hand Gestures"]:
            if gesture == "None":
                continue
            command = self.gesture_mappings.get(gesture, "NONE")
            if command != "NONE":
                preview_text += f"    {gesture} → {command}\n"
                hand_count += 1
        if hand_count == 0:
            preview_text += "    (No hand gestures mapped)\n"
        
        # Pose gestures
        preview_text += "  Pose Gestures:\n"
        pose_count = 0
        for gesture in self.available_gestures["Pose Gestures"]:
            if gesture == "None":
                continue
            command = self.gesture_mappings.get(gesture, "NONE")
            if command != "NONE":
                preview_text += f"    {gesture} → {command}\n"
                pose_count += 1
        if pose_count == 0:
            preview_text += "    (No pose gestures mapped)\n"
        
        
        preview_text += "\n" + "=" * 50 + "\n"
        preview_text += "Ready to start Person Tracker with these settings!"
        
        # Update text widget
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, preview_text)
    
    def collect_current_values(self):
        """Collect current values from GUI components"""
        # Only collect direction control values (lock/unlock are fixed)
        for gesture, var in self.command_vars.items():
            self.gesture_mappings[gesture] = var.get()
    
    def load_and_refresh(self):
        """Load configuration and refresh GUI"""
        self.load_config()
        self.refresh_gui_values()
        self.update_preview()
        messagebox.showinfo("Success", "Configuration loaded successfully!")
    
    def refresh_gui_values(self):
        """Refresh GUI values from loaded configuration"""
        # Only update direction control variables (lock/unlock are fixed)
        for gesture, var in self.command_vars.items():
            var.set(self.gesture_mappings.get(gesture, "NONE"))
    
    def reset_to_default(self):
        """Reset configuration to default values"""
        result = messagebox.askyesno("Confirm Reset", 
                                   "Are you sure you want to reset all settings to default values?")
        if result:
            self.gesture_mappings = self.default_mappings.copy()
            self.refresh_gui_values()
            self.update_preview()
            messagebox.showinfo("Reset Complete", "Configuration reset to default values!")
    
    def start_application(self):
        """Start the main Person Tracker application with current configuration"""
        # Collect current values
        self.collect_current_values()
        
        # Save configuration
        if not self.save_config():
            return
        
        # Show confirmation
        result = messagebox.askyesno("Start Application", 
                                   "Configuration saved! Start Person Tracker with these settings?")
        if result:
            # Close configuration window
            self.window.destroy()
            
            # Import and start main application with custom config
            self.start_main_application()
    
    def start_main_application(self):
        """Start the main application with configured settings"""
        try:
            # Apply configuration to the system
            self.apply_configuration_to_system()
            
            # Import and run main application
            import main
            import sys
            
            # Set up command line arguments (you can modify these as needed)
            sys.argv = ['main.py']  # Reset sys.argv to just the script name
            
            print("[CONFIG] Starting Person Tracker with custom configuration...")
            print("[CONFIG] Lock gestures: Closed_Fist + Open_Palm (fixed)")
            print("[CONFIG] Unlock gestures: Victory + Victory (fixed)")
            
            # Start the main application
            main.main()
            
        except Exception as e:
            print(f"[CONFIG] Error starting main application: {e}")
            messagebox.showerror("Error", f"Failed to start Person Tracker: {e}")
    
    def apply_configuration_to_system(self):
        """Apply the configuration to the actual system files"""
        # This function would modify the actual system configuration
        # For now, we'll create a runtime configuration that can be read by other modules
        
        # Create a runtime config file that other modules can read
        runtime_config = {
            "gesture_mappings": self.gesture_mappings,
            "applied_at": str(__import__('datetime').datetime.now())
        }
        
        with open("runtime_gesture_config.json", 'w') as f:
            json.dump(runtime_config, f, indent=2)
        
        print("[CONFIG] Runtime configuration created successfully")
    
    def run(self):
        """Run the configuration GUI"""
        self.load_config()
        self.create_gui()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        print("[CONFIG] Gesture Configuration GUI started")
        print("[CONFIG] Configure your gesture mappings and click 'Start Person Tracker'")
        
        # Run the GUI
        self.window.mainloop()

def main():
    """Main entry point for the configuration GUI"""
    print("🎮 Person Tracker - Gesture Configuration")
    print("=" * 50)
    print("Configure your gesture mappings before starting the application.")
    print("This GUI allows you to customize:")
    print("- Lock/unlock gesture combinations")
    print("- Direction control mappings")
    print("- Proximity requirements")
    print("=" * 50)
    
    config_gui = GestureConfigGUI()
    config_gui.run()

if __name__ == "__main__":
    main()
