import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
from action_controller import controller
import sys

def capture_state(sct, x, y):
    """Capture a small region around the given coordinates"""
    region = {
        'left': x - 5,     # 5 pixels left of cursor
        'top': y - 5,      # 5 pixels above cursor
        'width': 10,       # 10 pixels wide
        'height': 10       # 10 pixels tall
    }
    return np.array(sct.grab(region)), region

def calibrate():
    """Capture both present and absent states of the target"""
    with mss.mss() as sct:
        print("\n=== Button Present Calibration ===")
        print("1. Hover over the target button when it IS present (DO NOT CLICK)...")
        print("Make sure the button is fully visible!")
        input("Press Enter when ready...")
        
        # Get cursor position for present state
        x, y = pyautogui.position()
        print(f"Target position: ({x}, {y})")
        
        # Capture button present state
        present_img, region = capture_state(sct, x, y)
        
        print("\n=== Button Absent Calibration ===")
        print("2. Wait for the button to completely disappear at the SAME location...")
        print("Make sure there are no other UI elements in this area!")
        input("Press Enter when the button is completely gone...")
        
        # Capture button absent state at the same position
        absent_img, _ = capture_state(sct, x, y)
        
        # Save calibration data
        data = {
            'x': x,
            'y': y,
            'region': region,
            'present_pixels': present_img.tolist(),
            'absent_pixels': absent_img.tolist()
        }
        
        with open('basic_target.json', 'w') as f:
            json.dump(data, f)
        
        print("\nCalibration complete!")
        print(f"Position: ({x}, {y})")
        return data

def load_calibration():
    """Load the saved calibration data"""
    try:
        with open('basic_targets.json', 'r') as f:
            targets = json.load(f)
            # Convert pixel arrays back to numpy arrays
            for target in targets:
                target['present_pixels'] = np.array(target['present_pixels'])
                target['absent_pixels'] = np.array(target['absent_pixels'])
            return targets
    except FileNotFoundError:
        print("No calibration found. Please run setup_monitors.py first.")
        sys.exit(1)

def check_state(current, target_data):
    """Check if current state matches either present or absent state"""
    present_ref = target_data['present_pixels']
    absent_ref = target_data['absent_pixels']
    
    # Calculate differences
    diff_present = np.mean(np.abs(current - present_ref))
    diff_absent = np.mean(np.abs(current - absent_ref))
    
    # Consider it a match if it's closer to present than absent
    return diff_present < diff_absent

def queue_click_action(x, y):
    """Queue a click action to the controller"""
    controller.queue_action(
        'click',
        x=x,
        y=y
    )
    print("Queued click action")

def run_clicker():
    """Main loop to check target areas and click when matched"""
    # Load calibration
    targets = load_calibration()
    
    print("\nMonitoring targets:")
    for i, target in enumerate(targets, 1):
        print(f"Target {i} at ({target['x']}, {target['y']})")
    print("Press Ctrl+C to stop")
    
    with mss.mss() as sct:
        while True:
            try:
                # Check each target
                for target in targets:
                    # Capture current state
                    current, _ = capture_state(sct, target['x'], target['y'])
                    
                    # Check if button is present
                    if check_state(current, target):
                        print(f"\nTarget detected! Queueing click at ({target['x']}, {target['y']})")
                        queue_click_action(target['x'], target['y'])
                
                # Small delay between checks
                time.sleep(0.02)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break

if __name__ == "__main__":
    run_clicker() 