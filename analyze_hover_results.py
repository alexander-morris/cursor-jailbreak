import cv2
import numpy as np
from pathlib import Path
import mss
import pyautogui
import time
from PIL import Image
import logging
import tkinter as tk
from tkinter import ttk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_monitor():
    """Get monitor 2 (third monitor, index 2) and validate coordinates"""
    sct = mss.mss()
    monitors = []
    print("\nDetected monitors:")
    for i, m in enumerate(sct.monitors[1:], 0):  # Start from index 0, skip the "all monitors" monitor
        monitor = {
            "left": m["left"],
            "top": m["top"],
            "width": m["width"],
            "height": m["height"],
            "name": f"monitor_{i}"  # Use zero-based index
        }
        monitors.append(monitor)
        print(f"Monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
    
    if len(monitors) < 3:
        print("Error: Monitor 2 (third monitor) not found!")
        return None
    
    target_monitor = monitors[2]  # Get monitor 2 (third monitor)
    print(f"\nSelected monitor 2: {target_monitor['width']}x{target_monitor['height']} at ({target_monitor['left']}, {target_monitor['top']})")
    return target_monitor

def validate_coordinates(x, y, monitor):
    """Validate that coordinates are within monitor bounds"""
    if not monitor:
        return False
    if x < 0 or x >= monitor["width"]:
        print(f"X coordinate {x} is outside monitor bounds (0-{monitor['width']})")
        return False
    if y < 0 or y >= monitor["height"]:
        print(f"Y coordinate {y} is outside monitor bounds (0-{monitor['height']})")
        return False
    return True

def get_screen_coordinates():
    """Get current mouse position in screen coordinates"""
    x, y = pyautogui.position()
    
    # Get all monitors
    sct = mss.mss()
    all_monitors = sct.monitors[1:]  # Skip the "all monitors" monitor
    
    # Find which monitor contains the cursor
    for monitor in all_monitors:
        if (monitor["left"] <= x <= monitor["left"] + monitor["width"] and
            monitor["top"] <= y <= monitor["top"] + monitor["height"]):
            # Convert to monitor-relative coordinates
            rel_x = x - monitor["left"]
            rel_y = y - monitor["top"]
            return rel_x, rel_y, monitor
    
    # If not found in any monitor, use the first one
    monitor = all_monitors[0]
    rel_x = x - monitor["left"]
    rel_y = y - monitor["top"]
    return rel_x, rel_y, monitor

def capture_button_states(index):
    """Capture button before and after click"""
    # Add countdown for pre-click state
    print("\nPreparing to capture pre-click state...")
    for i in range(3, 0, -1):
        print(f"\rHover over button in {i}...", end="", flush=True)
        time.sleep(1)
    print("\rCapturing pre-click state now!", flush=True)
    
    # Get screen coordinates
    x, y = pyautogui.position()
    target_monitor = get_monitor()
    if not target_monitor:
        print("Error: Could not find monitor 2!")
        return None, None, None
    
    print("\nDebug: Screen coordinates before conversion:")
    print(f"Mouse X: {x}, Mouse Y: {y}")
    print(f"Monitor left: {target_monitor['left']}, Monitor top: {target_monitor['top']}")
    
    # Convert screen coordinates to monitor-relative coordinates
    if x < 0:
        # If x is negative, convert to positive monitor-relative
        rel_x = abs(x - target_monitor["left"])
        print(f"Debug: Converting negative X: {x} -> {rel_x}")
    else:
        # If x is positive, calculate relative to monitor left edge
        rel_x = x - target_monitor["left"]
        print(f"Debug: Converting positive X: {x} -> {rel_x}")
        
    if y < 0:
        # If y is negative, it's already relative to monitor 2's top
        rel_y = abs(y)
        print(f"Debug: Converting negative Y: {y} -> {rel_y}")
    else:
        # If y is positive, calculate relative to monitor top
        rel_y = y - target_monitor["top"]
        print(f"Debug: Converting positive Y: {y} -> {rel_y}")
    
    print(f"\nMouse at screen coordinates: ({x}, {y})")
    print(f"Monitor-relative coordinates: ({rel_x}, {rel_y})")
    print(f"Using monitor: {target_monitor['width']}x{target_monitor['height']} at ({target_monitor['left']}, {target_monitor['top']})")
    
    # Calculate region around cursor (100x20 pixels, centered on mouse)
    template_region = {
        "left": x - 50,  # 50px to the left of mouse
        "top": y - 10,   # 10px above mouse
        "width": 100,    # 50px to the right of mouse
        "height": 20,    # 10px below mouse
        "mon": target_monitor["name"]
    }
    
    print(f"\nDebug: Template capture region:")
    print(f"Left edge: {template_region['left']} (mouse X {x} - 50)")
    print(f"Right edge: {template_region['left'] + template_region['width']} (left + 100)")
    print(f"Top edge: {template_region['top']} (mouse Y {y} - 10)")
    print(f"Bottom edge: {template_region['top'] + template_region['height']} (top + 20)")
    
    # Ensure directory exists
    assets_dir = Path('assets/monitor_0')
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nCapturing pre-click image...")
    # Capture pre-click screenshot
    with mss.mss() as sct:
        screenshot = sct.grab(template_region)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        save_path = assets_dir / f'button_{index}_pre.png'
        img.save(save_path)
        print(f"Saved pre-click image: {save_path}")
        print(f"Image size: {img.size}")
    
    # Add countdown for post-click state
    print("\nPreparing to capture post-click state...")
    for i in range(3, 0, -1):
        print(f"\rClick button in {i}...", end="", flush=True)
        time.sleep(1)
    print("\rCapturing post-click state now!", flush=True)
    
    print("\nCapturing post-click image...")
    # Capture post-click screenshot in the same region
    with mss.mss() as sct:
        screenshot = sct.grab(template_region)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        save_path = assets_dir / f'button_{index}_post.png'
        img.save(save_path)
        print(f"Saved post-click image: {save_path}")
        print(f"Image size: {img.size}")
    
    # Save click coordinates (monitor-relative)
    coords_path = assets_dir / f'click_coords_{index}.txt'
    with open(coords_path, 'w') as f:
        f.write(f"{rel_x},{rel_y}")  # Save monitor-relative coordinates
    print(f"\nSaved coordinates to: {coords_path}")
    print(f"Coordinates saved: {rel_x},{rel_y}")
    
    # Save monitor info
    monitor_path = assets_dir / f'monitor_{index}.txt'
    with open(monitor_path, 'w') as f:
        monitor_info = f"{target_monitor['left']},{target_monitor['top']},{target_monitor['width']},{target_monitor['height']}"
        f.write(monitor_info)
    print(f"Saved monitor info to: {monitor_path}")
    print(f"Monitor info saved: {monitor_info}")
    
    return rel_x, rel_y, target_monitor

def verify_click(self, x, y, pre_click_template, post_click_template):
    """Verify that a click at (x,y) was successful by comparing pre and post click states"""
    current_region = self.capture_region(x, y, self.template_width, self.template_height)
    
    # Verify click was successful by checking if button state changed
    pre_click_similarity = cv2.matchTemplate(current_region, pre_click_template, cv2.TM_CCOEFF_NORMED)[0][0]
    post_click_similarity = cv2.matchTemplate(current_region, post_click_template, cv2.TM_CCOEFF_NORMED)[0][0]

    print(f"Pre-click similarity: {pre_click_similarity:.3f}")
    print(f"Post-click similarity: {post_click_similarity:.3f}")

    # Require post-click to be at least 10% different from pre-click
    if abs(post_click_similarity - pre_click_similarity) < 0.1:
        print("Click didn't change state, retrying...")
        return False
    
    return True

def click_button_with_verification(x, y, pre_click_img, post_click_img, monitor, max_attempts=3):
    """Click button and verify the state change"""
    # Calculate monitoring region (100x100 centered on click point)
    monitor_region = {
        "left": monitor["left"] + x - 50,
        "top": monitor["top"] + y - 50,
        "width": 100,
        "height": 100,
        "mon": monitor["name"]
    }
    
    # Calculate template region (100x25 centered on potential match)
    template_region = {
        "left": monitor["left"] + x - 50,
        "top": monitor["top"] + y - 12,
        "width": 100,
        "height": 25,
        "mon": monitor["name"]
    }
    
    for attempt in range(max_attempts):
        print(f"\nClick attempt {attempt + 1}...")
        
        # Verify pre-click state
        with mss.mss() as sct:
            current = np.array(sct.grab(template_region))
            current_bgr = cv2.cvtColor(current, cv2.COLOR_BGRA2BGR)
            result = cv2.matchTemplate(current_bgr, pre_click_img, cv2.TM_CCORR_NORMED)
            pre_confidence = np.max(result)
            print(f"Pre-click confidence: {pre_confidence:.3f}")
            
        if pre_confidence < 0.75:  # More lenient threshold
            print(f"Area doesn't match pre-click state")
            return False
            
        # Convert monitor-relative coordinates to screen coordinates for click
        screen_x = monitor["left"] + x
        screen_y = monitor["top"] + y
        print(f"Clicking at screen coordinates: ({screen_x}, {screen_y})")
        
        # Perform click
        pyautogui.moveTo(screen_x, screen_y, duration=0.5)
        time.sleep(0.5)
        pyautogui.click()
        
        # Verify state change in monitoring region
        if verify_click_state(monitor_region, pre_click_img, post_click_img, monitor):
            print("Click verified - state changed successfully!")
            return True
        
        print("Click didn't change state, retrying...")
        time.sleep(2.0)  # Wait longer between retries
    
    print("Failed to verify click after maximum attempts")
    return False

def check_calibration_data():
    """Check if calibration data exists"""
    assets_dir = Path('assets/monitor_0')
    if not assets_dir.exists():
        return False
        
    pre_click_files = sorted(assets_dir.glob('button_*_pre.png'))
    post_click_files = sorted(assets_dir.glob('button_*_post.png'))
    coords_files = sorted(assets_dir.glob('click_coords_*.txt'))
    monitor_files = sorted(assets_dir.glob('monitor_*.txt'))
    
    # Check if we have all required files for at least one button
    return len(pre_click_files) > 0 and \
           len(post_click_files) > 0 and \
           len(coords_files) > 0 and \
           len(monitor_files) > 0

def run_calibration():
    """Run calibration process and save data"""
    print("\nStarting calibration process...")
    print("Please capture 3 different button states")
    captured_positions = []
    
    root = tk.Tk()
    root.title("Button Calibration")
    
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    button_count = 0
    
    def update_mouse_pos():
        x, y = pyautogui.position()
        mouse_pos_label.config(text=f"Mouse position: ({x}, {y})")
        if not root.quit_flag:
            root.after(50, update_mouse_pos)
    
    def on_capture():
        nonlocal button_count
        capture_btn.config(state='disabled')
        status_label.config(text="Move mouse to button...")
        root.update()
        
        button_count += 1
        x, y, monitor = capture_button_states(button_count)
        captured_positions.append((x, y))
        
        captured_text = "Captured positions:\n"
        for i, (cx, cy) in enumerate(captured_positions, 1):
            captured_text += f"Button {i}: ({cx}, {cy})\n"
        captured_pos_label.config(text=captured_text)
        
        status_label.config(text=f"Captured button {button_count}")
        if button_count >= 3:
            done_btn.config(state='normal')
        else:
            capture_btn.config(state='normal')
    
    def on_done():
        root.quit_flag = True
        root.quit()
    
    root.quit_flag = False
    
    ttk.Label(frame, text="Click 'Capture', then move mouse over button").grid(row=0, column=0, columnspan=2)
    mouse_pos_label = ttk.Label(frame, text="Mouse position: (0, 0)")
    mouse_pos_label.grid(row=1, column=0, columnspan=2)
    capture_btn = ttk.Button(frame, text="Capture", command=on_capture)
    capture_btn.grid(row=2, column=0)
    done_btn = ttk.Button(frame, text="Done", command=on_done, state='disabled')
    done_btn.grid(row=2, column=1)
    status_label = ttk.Label(frame, text="Ready to capture")
    status_label.grid(row=3, column=0, columnspan=2)
    captured_pos_label = ttk.Label(frame, text="Captured positions:")
    captured_pos_label.grid(row=4, column=0, columnspan=2)
    
    update_mouse_pos()
    root.mainloop()
    root.destroy()
    
    print("\nCalibration complete!")
    return captured_positions

def find_button_in_region(search_region, template_img, target_monitor, original_coords, max_distance=250):
    """Find button in search region using template matching"""
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(search_region))
    img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    # Find all matches above threshold
    result = cv2.matchTemplate(img_bgr, template_img, cv2.TM_CCORR_NORMED)
    threshold = 0.75
    locations = np.where(result >= threshold)
    
    best_match = None
    best_confidence = 0
    
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        # These coordinates are relative to the search region
        match_x = pt[0] + search_region["left"] - target_monitor["left"]
        match_y = pt[1] + search_region["top"] - target_monitor["top"]
        
        # Calculate distance from original calibration position
        distance = ((match_x - original_coords[0]) ** 2 + (match_y - original_coords[1]) ** 2) ** 0.5
        confidence = result[pt[1], pt[0]]
        
        print(f"Found match at ({match_x}, {match_y}) relative to monitor")
        print(f"Distance from calibration: {distance:.1f}px")
        print(f"Confidence: {confidence:.3f}")
        
        # Only consider matches within max_distance of calibration point
        if distance <= max_distance and confidence > best_confidence:
            best_confidence = confidence
            best_match = {
                'rel_x': match_x,
                'rel_y': match_y,
                'confidence': confidence,
                'distance': distance
            }
    
    return best_match

def find_precise_button_location(template_img, target_monitor, current_x, current_y):
    """Find precise button location after moving to approximate position"""
    # Define a smaller search region around current position
    precise_region = {
        "left": target_monitor["left"] + current_x - 125,
        "top": target_monitor["top"] + current_y - 125,
        "width": 250,
        "height": 250,
        "mon": target_monitor["name"]
    }
    
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(precise_region))
    img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    # Find best match in the precise region
    result = cv2.matchTemplate(img_bgr, template_img, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= 0.8:  # Higher threshold for precise match
        match_x = max_loc[0] + precise_region["left"] - target_monitor["left"]
        match_y = max_loc[1] + precise_region["top"] - target_monitor["top"]
        return {
            'rel_x': match_x,
            'rel_y': match_y,
            'confidence': max_val
        }
    return None

def analyze_button_images(run_time=180):  # 180 seconds = 3 minutes
    if not check_calibration_data():
        print("No calibration data found. Running calibration...")
        run_calibration()
    else:
        print("Using existing calibration data...")
    
    print("=" * 50)
    
    target_monitor = get_monitor()
    if not target_monitor:
        print("Error: Could not find monitor 2!")
        return
    
    assets_dir = Path('assets/monitor_0')
    pre_click_files = sorted(assets_dir.glob('button_*_pre.png'))
    post_click_files = sorted(assets_dir.glob('button_*_post.png'))
    coords_files = sorted(assets_dir.glob('click_coords_*.txt'))
    
    if not pre_click_files:
        print("No button images found!")
        return
    
    print(f"\nFound {len(pre_click_files)} button variations")
    print("=" * 50)
    
    # Load all button templates and coordinates
    buttons = []
    for i, (pre_file, post_file, coords_file) in enumerate(zip(pre_click_files, post_click_files, coords_files), 1):
        pre_img = cv2.imread(str(pre_file))
        post_img = cv2.imread(str(post_file))
        if pre_img is None or post_img is None:
            print(f"Failed to load images for button {i}")
            continue
            
        with open(coords_file) as f:
            rel_x, rel_y = map(int, f.read().strip().split(','))
            
        if not validate_coordinates(rel_x, rel_y, target_monitor):
            print(f"Warning: Button {i} coordinates ({rel_x}, {rel_y}) are outside monitor 2 bounds!")
            continue
            
        buttons.append({
            'pre_img': pre_img,
            'post_img': post_img,
            'calibration_x': rel_x,
            'calibration_y': rel_y,
            'button_num': i
        })
        print(f"Loaded Button {i} calibration position: ({rel_x}, {rel_y})")
    
    if not buttons:
        print("No valid buttons found within monitor 2 bounds!")
        return
    
    print(f"\nLoaded {len(buttons)} valid buttons")
    print("\nStarting continuous monitoring...")
    print("Will keep searching until pre-click matches are found")
    print("=" * 50)
    
    # Initial parameters
    search_radius = 100  # Start with smaller radius
    confidence_threshold = 0.85  # Start with high confidence
    min_confidence = 0.75  # Don't go below this threshold
    max_search_radius = 400  # Maximum search radius
    
    iteration = 0
    matches_found = []
    
    while True:  # Keep searching until matches are found
        iteration += 1
        matches_found = []
        
        print(f"\nIteration {iteration}")
        print(f"Search radius: {search_radius}px")
        print(f"Confidence threshold: {confidence_threshold:.3f}")
        print(f"Using monitor: {target_monitor['name']} at ({target_monitor['left']}, {target_monitor['top']})")
        
        for button in buttons:
            # Define search region around calibration point
            search_region = {
                "left": target_monitor["left"] + button['calibration_x'] - search_radius,
                "top": target_monitor["top"] + button['calibration_y'] - search_radius,
                "width": search_radius * 2,
                "height": search_radius * 2,
                "mon": target_monitor["name"]
            }
            
            print(f"\nSearching for Button {button['button_num']} around ({button['calibration_x']}, {button['calibration_y']})")
            
            # Capture current screen region
            with mss.mss() as sct:
                screenshot = np.array(sct.grab(search_region))
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Find matches for pre-click template
            result = cv2.matchTemplate(img_bgr, button['pre_img'], cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence_threshold)
            
            for pt in zip(*locations[::-1]):
                # Calculate monitor-relative coordinates
                monitor_rel_x = button['calibration_x'] - search_radius + pt[0]
                monitor_rel_y = button['calibration_y'] - search_radius + pt[1]
                
                # Calculate distance from calibration point
                distance = ((monitor_rel_x - button['calibration_x']) ** 2 + 
                          (monitor_rel_y - button['calibration_y']) ** 2) ** 0.5
                
                confidence = result[pt[1], pt[0]]
                
                match = {
                    'rel_x': monitor_rel_x,
                    'rel_y': monitor_rel_y,
                    'confidence': confidence,
                    'distance': distance,
                    'button_num': button['button_num'],
                    'pre_img': button['pre_img'],
                    'post_img': button['post_img']
                }
                
                print(f"\nFound potential match for Button {button['button_num']} on {target_monitor['name']}:")
                print(f"Monitor-relative position: ({monitor_rel_x}, {monitor_rel_y})")
                print(f"Screen coordinates: ({target_monitor['left'] + monitor_rel_x}, {target_monitor['top'] + monitor_rel_y})")
                print(f"Confidence: {confidence:.3f}")
                print(f"Distance from calibration: {distance:.1f}px")
                
                # Move to match and verify
                screen_x = target_monitor["left"] + monitor_rel_x
                screen_y = target_monitor["top"] + monitor_rel_y
                print(f"Moving to position to verify match...")
                pyautogui.moveTo(screen_x, screen_y, duration=0.5)
                time.sleep(0.5)
                
                # Capture current state and verify it matches pre-click
                verify_region = {
                    "left": screen_x - 50,
                    "top": screen_y - 10,
                    "width": 100,
                    "height": 20,
                    "mon": target_monitor["name"]
                }
                
                with mss.mss() as sct:
                    current = np.array(sct.grab(verify_region))
                current_bgr = cv2.cvtColor(current, cv2.COLOR_BGRA2BGR)
                verify_result = cv2.matchTemplate(current_bgr, button['pre_img'], cv2.TM_CCOEFF_NORMED)
                verify_confidence = np.max(verify_result)
                
                print(f"Verification confidence: {verify_confidence:.3f}")
                
                if verify_confidence >= confidence_threshold:
                    print("Match verified!")
                    matches_found.append(match)
                else:
                    print("Match failed verification")
        
        if matches_found:
            print(f"\nFound {len(matches_found)} verified matches!")
            print("Moving between matches to verify positions...")
            
            for match in matches_found:
                screen_x = target_monitor["left"] + match['rel_x']
                screen_y = target_monitor["top"] + match['rel_y']
                print(f"\nMoving to Button {match['button_num']} at ({screen_x}, {screen_y})")
                pyautogui.moveTo(screen_x, screen_y, duration=0.5)
                time.sleep(1.0)
            
            print("\nAll matches verified!")
            break  # Exit the loop since we found matches
            
        else:
            print("\nNo verified matches found, adjusting search parameters...")
            
            # Adjust search parameters
            if search_radius < max_search_radius:
                search_radius += 50
                print(f"Increased search radius to {search_radius}px")
            elif confidence_threshold > min_confidence:
                confidence_threshold = max(min_confidence, confidence_threshold - 0.02)
                print(f"Lowered confidence threshold to {confidence_threshold:.3f}")
                search_radius = 100  # Reset search radius when lowering confidence
            else:
                print("\nReached minimum confidence threshold and maximum search radius")
                print("Starting over with initial parameters...")
                search_radius = 100
                confidence_threshold = 0.85
            
            # Small delay before next iteration
            time.sleep(1.0)
    
    print("\nAnalysis complete - found all pre-click matches!")
    print("=" * 50)
    return matches_found

if __name__ == "__main__":
    analyze_button_images() 