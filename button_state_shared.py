# button_state_shared.py - Shared button state module for two-thread system

import threading

# Global button state variable (11 characters: 0000000000\n)
button_state = "0000000000\n"
button_lock = threading.Lock()

# Button state position mapping
BUTTON_POSITIONS = {
    "FORWARD": 1,      # Position 1 (0-indexed: 0)
    "RIGHT": 2,        # Position 2 (0-indexed: 1)
    "BACKWARD": 3,     # Position 3 (0-indexed: 2)
    "LEFT": 4,         # Position 4 (0-indexed: 3)
    "BUTTON_A": 5,     # Position 5 (0-indexed: 4)
    "BUTTON_B": 6,     # Position 6 (0-indexed: 5)
    "BUTTON_C": 7,     # Position 7 (0-indexed: 6)
    # Positions 8-10 reserved for future use
}

def get_button_state():
    """
    Thread-safe getter for button state.
    
    Returns:
        str: Current button state (11-character string)
    """
    with button_lock:
        return button_state

def set_button_state(new_state):
    """
    Thread-safe setter for button state.
    
    Args:
        new_state (str): New button state to set
    """
    with button_lock:
        global button_state
        button_state = new_state

def update_button_state(new_state):
    """
    Thread-safe update for button state.
    Alias for set_button_state for clarity.
    
    Args:
        new_state (str): New button state to set
    """
    set_button_state(new_state)

def reset_button_state():
    """
    Reset button state to default (all zeros).
    """
    set_button_state("0000000000\n")

def set_button_pressed():
    """
    Set button state to pressed (all ones).
    """
    set_button_state("1111111111\n")

def get_button_state_info():
    """
    Get button state with additional info for debugging.
    
    Returns:
        dict: Button state information
    """
    with button_lock:
        return {
            'state': button_state,
            'state_stripped': button_state.strip(),
            'is_pressed': button_state.strip() == "1111111111",
            'is_released': button_state.strip() == "0000000000"
        }

def set_button_position(button_name, pressed=True):
    """
    Set a specific button position in the state string.
    
    Args:
        button_name (str): Button name (e.g., "FORWARD", "BUTTON_A")
        pressed (bool): True to set to 1, False to set to 0
    """
    if button_name not in BUTTON_POSITIONS:
        print(f"[ERROR] Unknown button: {button_name}")
        return
    
    position = BUTTON_POSITIONS[button_name] - 1  # Convert to 0-indexed
    value = "1" if pressed else "0"
    
    with button_lock:
        global button_state
        # Convert to list, modify, convert back to string
        state_list = list(button_state.strip())
        if 0 <= position < len(state_list):
            state_list[position] = value
            button_state = "".join(state_list) + "\n"

def set_multiple_buttons(button_dict):
    """
    Set multiple buttons at once.
    
    Args:
        button_dict (dict): Dictionary of {button_name: pressed_bool}
    """
    with button_lock:
        global button_state
        state_list = list(button_state.strip())
        
        for button_name, pressed in button_dict.items():
            if button_name in BUTTON_POSITIONS:
                position = BUTTON_POSITIONS[button_name] - 1  # Convert to 0-indexed
                value = "1" if pressed else "0"
                if 0 <= position < len(state_list):
                    state_list[position] = value
        
        button_state = "".join(state_list) + "\n"

def get_button_position(button_name):
    """
    Get the current state of a specific button position.
    
    Args:
        button_name (str): Button name (e.g., "FORWARD", "BUTTON_A")
    
    Returns:
        bool: True if pressed (1), False if released (0)
    """
    if button_name not in BUTTON_POSITIONS:
        return False
    
    position = BUTTON_POSITIONS[button_name] - 1  # Convert to 0-indexed
    
    with button_lock:
        state_list = list(button_state.strip())
        if 0 <= position < len(state_list):
            return state_list[position] == "1"
        return False
