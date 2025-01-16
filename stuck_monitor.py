import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
from action_controller import controller
import sys

def wait_for_position():
    """Wait for user to position cursor and press Enter"""
    input("Press Enter when ready...")
    return pyautogui.position()

def select_region():
    """Let user select region with cursor positions"""
    print("\n=== Region Selection ===")
    print("1. Move cursor to TOP-LEFT corner of the area to monitor")
    x1, y1 = wait_for_position()
    print(f"Top-left: ({x1}, {y1})")
    
    print("\n2. Move cursor to BOTTOM-RIGHT corner of the area to monitor")
    x2, y2 = wait_for_position()
    print(f"Bottom-right: ({x2}, {y2})")
    
    print("\n3. Move cursor to where you want to click when inactivity is detected")
    action_x, action_y = wait_for_position()
    print(f"Action click position: ({action_x}, {action_y})")
    
    # Ensure coordinates are in correct order
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    region = {
        'left': left,
        'top': top,
        'width': width,
        'height': height,
        'action_x': action_x,
        'action_y': action_y
    }
    
    print(f"\nMonitoring region: {width}x{height} at ({left}, {top})")
    print(f"Will click at ({action_x}, {action_y}) after 70 seconds of inactivity")
    return region

def capture_region(sct, region):
    """Capture the specified region"""
    return np.array(sct.grab(region))

def check_for_changes(current, previous, threshold=2.0):
    """Check if two captures are different"""
    if current is None or previous is None:
        return True
    
    diff = np.abs(current.astype(float) - previous.astype(float))
    mean_diff = np.mean(diff)
    return mean_diff > threshold

def queue_stuck_action(x, y):
    """Queue the stuck action to the controller"""
    message = "please continue with the todo list, and be sure to test as you go, follow the process. solve one problem at a time, and add everything else to the todo list"
    controller.queue_action(
        'click_and_type',
        x=x,
        y=y,
        message=message
    )
    print("Queued stuck action")

def load_region():
    """Load the saved region data"""
    try:
        with open('stuck_region.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("No calibration found. Please run setup_monitors.py first.")
        sys.exit(1)

def monitor_region():
    """Main monitoring loop"""
    # Load calibrated region
    region = load_region()
    
    print(f"\nMonitoring region: {region['width']}x{region['height']} at ({region['left']}, {region['top']})")
    print(f"Will click at ({region['action_x']}, {region['action_y']}) after 70 seconds of inactivity")
    print("Press Ctrl+C to stop")
    
    with mss.mss() as sct:
        previous_capture = None
        last_change_time = time.time()
        inactivity_threshold = 70  # seconds
        
        while True:
            try:
                current_time = time.time()
                
                # Capture current state
                current_capture = capture_region(sct, region)
                
                # Check for changes
                if check_for_changes(current_capture, previous_capture):
                    last_change_time = current_time
                    print(".", end="", flush=True)
                elif current_time - last_change_time >= inactivity_threshold:
                    queue_stuck_action(region['action_x'], region['action_y'])
                    last_change_time = current_time  # Reset inactivity timer
                
                # Update previous capture
                previous_capture = current_capture
                
                # Small delay between checks
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break

if __name__ == "__main__":
    monitor_region() 