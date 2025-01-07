import cv2
import numpy as np
from pathlib import Path
import mss
import pyautogui
import time
import os

def get_monitor():
    """Get monitor 2 (third monitor, index 2)"""
    sct = mss.mss()
    monitors = []
    for i, m in enumerate(sct.monitors[1:], 0):
        monitor = {
            "left": m["left"],
            "top": m["top"],
            "width": m["width"],
            "height": m["height"],
            "name": f"monitor_{i}"
        }
        monitors.append(monitor)
    
    if len(monitors) < 3:
        print("Error: Monitor 2 not found!")
        return None
    
    target_monitor = monitors[2]  # Get monitor 2
    print(f"Using monitor 2: {target_monitor['width']}x{target_monitor['height']} at ({target_monitor['left']}, {target_monitor['top']})")
    return target_monitor

def validate_coordinates(x, y, monitor):
    """Validate that coordinates are within monitor bounds"""
    if x < 0 or x >= monitor["width"]:
        print(f"X coordinate {x} is outside monitor bounds (0-{monitor['width']})")
        return False
    if y < 0 or y >= monitor["height"]:
        print(f"Y coordinate {y} is outside monitor bounds (0-{monitor['height']})")
        return False
    return True

def capture_button(monitor, button_num):
    """Capture pre and post click images and coordinates for a button"""
    print(f"\nCalibrating Button {button_num}:")
    print("Move mouse to button position and press Enter to capture...")
    input()
    
    # Get current mouse position
    mouse_x, mouse_y = pyautogui.position()
    rel_x = mouse_x - monitor["left"]
    rel_y = mouse_y - monitor["top"]
    print(f"Mouse position: ({rel_x}, {rel_y})")
    
    # Validate coordinates
    if not validate_coordinates(rel_x, rel_y, monitor):
        print("Please move mouse within monitor bounds and try again")
        return capture_button(monitor, button_num)
    
    # Create monitor region for screenshot
    monitor_region = {
        "left": monitor["left"],
        "top": monitor["top"],
        "width": monitor["width"],
        "height": monitor["height"],
        "mon": monitor["name"]
    }
    
    # Take pre-click screenshot
    with mss.mss() as sct:
        screen = np.array(sct.grab(monitor_region))
    pre_click = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
    
    # Calculate button region bounds
    button_x = max(0, min(rel_x - 35, monitor["width"] - 70))  # Ensure within bounds
    button_y = max(0, min(rel_y - 10, monitor["height"] - 20))  # Ensure within bounds
    
    # Extract button region (70x20 pixels centered on mouse)
    button_region = pre_click[button_y:button_y+20, button_x:button_x+70]
    
    # Save coordinates
    assets_dir = Path(f'assets/{monitor["name"]}')
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    coords_file = assets_dir / f'click_coords_{button_num}.txt'
    with open(coords_file, 'w') as f:
        f.write(f"{rel_x},{rel_y}")
    
    # Save pre-click image
    cv2.imwrite(str(assets_dir / f'button_{button_num}_pre.png'), button_region)
    print("Pre-click image saved")
    
    print("Press Enter to capture post-click image...")
    input()
    
    # Take post-click screenshot
    with mss.mss() as sct:
        screen = np.array(sct.grab(monitor_region))
    post_click = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
    
    # Extract same button region
    button_region = post_click[button_y:button_y+20, button_x:button_x+70]
    
    # Save post-click image
    cv2.imwrite(str(assets_dir / f'button_{button_num}_post.png'), button_region)
    print("Post-click image saved")
    
    return rel_x, rel_y

def main():
    """Main calibration function"""
    monitor = get_monitor()
    if not monitor:
        return
    
    print("\nStarting calibration process...")
    print("Will capture 3 buttons")
    print("For each button:")
    print("1. Move mouse to button")
    print("2. Press Enter to capture pre-click")
    print("3. Click the button")
    print("4. Press Enter to capture post-click")
    print("\nPress Enter when ready to start...")
    input()
    
    buttons = []
    for i in range(1, 4):
        x, y = capture_button(monitor, i)
        buttons.append((x, y))
    
    print("\nCalibration complete!")
    print("Captured buttons at:")
    for i, (x, y) in enumerate(buttons, 1):
        print(f"Button {i}: ({x}, {y})")

if __name__ == "__main__":
    main() 