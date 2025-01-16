import json
import time
import pyautogui
from mss import mss
import numpy as np

def get_click_position():
    """Get a click position from user"""
    print("\nMove your cursor to the target position and press Enter...")
    input()
    x, y = pyautogui.position()
    return {'x': x, 'y': y}

def calibrate_click_targets():
    """Calibrate multiple click targets"""
    targets = []
    while True:
        print(f"\nCurrently calibrated {len(targets)} targets.")
        if len(targets) > 0 and input("Done adding targets? (y/n): ").lower() == 'y':
            break
            
        print("\nCalibrating new click target...")
        target = get_click_position()
        targets.append(target)
        print(f"Saved target at position ({target['x']}, {target['y']})")
    
    # Save targets
    with open('click_targets.json', 'w') as f:
        json.dump(targets, f)
    return targets

def add_click_targets():
    """Add new click targets to existing ones"""
    # Load existing targets
    try:
        with open('click_targets.json', 'r') as f:
            targets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        targets = []
    
    print(f"\nCurrently have {len(targets)} targets.")
    while True:
        print("\nCalibrating new click target...")
        target = get_click_position()
        targets.append(target)
        print(f"Saved target at position ({target['x']}, {target['y']})")
        
        if input("Done adding targets? (y/n): ").lower() == 'y':
            break
    
    # Save updated targets
    with open('click_targets.json', 'w') as f:
        json.dump(targets, f)
    return targets

def calibrate_stuck_monitor():
    """Calibrate the stuck monitor region and action position"""
    print("\nCalibrating stuck monitor...")
    print("Move your cursor to the top-left corner of the region to monitor and press Enter...")
    input()
    x1, y1 = pyautogui.position()
    
    print("Move your cursor to the bottom-right corner of the region and press Enter...")
    input()
    x2, y2 = pyautogui.position()
    
    print("Move your cursor to where you want to click when stuck and press Enter...")
    input()
    action_x, action_y = pyautogui.position()
    
    region = {
        'top': min(y1, y2),
        'left': min(x1, x2),
        'width': abs(x2 - x1),
        'height': abs(y2 - y1),
        'action_x': action_x,
        'action_y': action_y
    }
    
    # Save region
    with open('stuck_region.json', 'w') as f:
        json.dump(region, f)
    return region

def setup_monitors():
    """Run the complete setup process"""
    print("\nHustleBot Setup")
    print("==============")
    
    # Calibrate click targets
    print("\nLet's set up click targets first...")
    targets = calibrate_click_targets()
    print(f"\nSuccessfully calibrated {len(targets)} click targets!")
    
    # Calibrate stuck monitor
    print("\nNow let's set up the stuck monitor...")
    region = calibrate_stuck_monitor()
    print(f"\nSuccessfully calibrated stuck monitor!")
    print(f"Monitoring region: {region['width']}x{region['height']} at ({region['left']}, {region['top']})")
    print(f"Action position: ({region['action_x']}, {region['action_y']})")
    
    print("\nSetup complete! You can now run the monitors.")

if __name__ == "__main__":
    setup_monitors() 