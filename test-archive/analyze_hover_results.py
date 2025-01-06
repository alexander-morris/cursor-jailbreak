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
from skimage.metrics import structural_similarity as ssim

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_monitor(button_index=None):
    """Get monitor based on button index (0-based) or monitor 2 if no index provided"""
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
    
    if button_index is not None:
        if button_index < 0 or button_index >= len(monitors):
            print(f"Error: Monitor {button_index} not found!")
            return None
        target_monitor = monitors[button_index]
        print(f"\nSelected monitor {button_index}: {target_monitor['width']}x{target_monitor['height']} at ({target_monitor['left']}, {target_monitor['top']})")
    else:
        if len(monitors) < 3:
            print("Error: Monitor 2 (third monitor) not found!")
            return None
        target_monitor = monitors[2]  # Default to monitor 2 if no index provided
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
    
    # Calculate region around cursor (70x20 pixels, centered on mouse)
    template_region = {
        "left": x - 35,  # 35px to the left of mouse
        "top": y - 10,   # 10px above mouse
        "width": 70,     # 35px to the right of mouse
        "height": 20,    # 10px below mouse
        "mon": target_monitor["name"]
    }
    
    print(f"\nDebug: Template capture region:")
    print(f"Left edge: {template_region['left']} (mouse X {x} - 35)")
    print(f"Right edge: {template_region['left'] + template_region['width']} (left + 70)")
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

def verify_match(img, template, correlation_threshold=0.7):
    """Verify if an image patch matches the template."""
    # Ensure same size
    if img.shape != template.shape:
        print("Size mismatch in verify_match")
        return False
        
    # Calculate verification metrics
    correlation = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED)[0][0]
    mse = np.mean((img.astype("float") - template.astype("float")) ** 2)
    mse_score = 1 - (mse / 255**2)  # Normalize to 0-1 range
    ssim_score = ssim(img, template, channel_axis=2, win_size=3)  # Use small window size for small images
    
    # Calculate final score (weighted average)
    final_score = (correlation * 0.6) + (mse_score * 0.3) + (ssim_score * 0.1)
    
    print("Verification scores:")
    print(f"  Correlation: {correlation:.3f}")
    print(f"  MSE Score: {mse_score:.3f}")
    print(f"  SSIM Score: {ssim_score:.3f}")
    print(f"  Final Score: {final_score:.3f}")
    
    # More lenient thresholds
    return correlation >= correlation_threshold and mse_score >= 0.95 and final_score >= 0.65

def analyze_button_images(run_time=30):  # 30 seconds
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
    
    # Take full monitor screenshot for visualization
    with mss.mss() as sct:
        monitor_region = {
            "left": target_monitor["left"],
            "top": target_monitor["top"],
            "width": target_monitor["width"],
            "height": target_monitor["height"],
            "mon": target_monitor["name"]
        }
        full_screenshot = np.array(sct.grab(monitor_region))
    full_screenshot_bgr = cv2.cvtColor(full_screenshot, cv2.COLOR_BGRA2BGR)
    visualization = full_screenshot_bgr.copy()
    
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
        print(f"Template size: {pre_img.shape[1]}x{pre_img.shape[0]}")
        
        # Draw calibration point on visualization
        cv2.circle(visualization, (rel_x, rel_y), 5, (0, 0, 255), -1)  # Red dot
        cv2.putText(visualization, f"Cal {i}", (rel_x + 10, rel_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    if not buttons:
        print("No valid buttons found within monitor 2 bounds!")
        return
    
    print(f"\nLoaded {len(buttons)} valid buttons")
    print("\nStarting analysis...")
    print("=" * 50)
    
    # Create debug directory
    debug_dir = Path('debug')
    debug_dir.mkdir(exist_ok=True)
    
    # Search parameters
    search_margin_x = 40  # pixels to search horizontally
    search_margin_y = 80  # pixels to search vertically
    confidence_threshold = 0.80  # Slightly relaxed from 0.85
    
    for button in buttons:
        print(f"\nAnalyzing Button {button['button_num']}...")
        cal_x, cal_y = button['calibration_x'], button['calibration_y']
        print(f"Calibration position: ({cal_x}, {cal_y})")
        
        # Get template dimensions
        template_h, template_w = button['pre_img'].shape[:2]
        print(f"Template size: {template_w}x{template_h}")
        
        # Calculate center offset for template
        center_x = template_w // 2
        center_y = template_h // 2
        print(f"Template center offset: ({center_x}, {center_y})")
        
        # Define search region around calibration point
        search_region = {
            "left": target_monitor["left"] + cal_x - search_margin_x - center_x,
            "top": target_monitor["top"] + cal_y - search_margin_y - center_y,
            "width": (search_margin_x * 2) + template_w,
            "height": (search_margin_y * 2) + template_h,
            "mon": target_monitor["name"]
        }
        
        print(f"\nSearch region:")
        print(f"  Monitor position: ({target_monitor['left']}, {target_monitor['top']})")
        print(f"  Calibration point (monitor-relative): ({cal_x}, {cal_y})")
        print(f"  Search region position: ({search_region['left']}, {search_region['top']})")
        print(f"  Search region size: {search_region['width']}x{search_region['height']}")
        print(f"  X search range: {cal_x - search_margin_x} to {cal_x + search_margin_x}")
        print(f"  Y search range: {cal_y - search_margin_y} to {cal_y + search_margin_y}")
        
        # Take screenshot of search region
        with mss.mss() as sct:
            screenshot = np.array(sct.grab(search_region))
        img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        # Save search region for debugging
        debug_search = img_bgr.copy()
        # Draw calibration point (should be at center of search region)
        center_search_x = search_margin_x + center_x
        center_search_y = search_margin_y + center_y
        cv2.circle(debug_search, (center_search_x, center_search_y), 3, (0, 0, 255), -1)
        # Draw template box
        cv2.rectangle(debug_search, 
                     (center_search_x - center_x, center_search_y - center_y),
                     (center_search_x + center_x, center_search_y + center_y),
                     (0, 255, 0), 1)
        cv2.imwrite(str(debug_dir / f'search_region_{button["button_num"]}.png'), debug_search)
        
        # Find matches
        result = cv2.matchTemplate(img_bgr, button['pre_img'], cv2.TM_CCORR_NORMED)
        locations = np.where(result >= confidence_threshold)
        
        print(f"\nFound {len(locations[0])} potential matches")
        
        best_match = None
        best_distance = float('inf')
        
        for pt in zip(*locations[::-1]):
            # Calculate monitor-relative coordinates
            match_x = cal_x - search_margin_x + pt[0]
            match_y = cal_y - search_margin_y + pt[1]
            
            # Calculate distance from calibration point
            distance = ((match_x - cal_x) ** 2 + (match_y - cal_y) ** 2) ** 0.5
            confidence = result[pt[1], pt[0]]
            
            print(f"\nFound match:")
            print(f"  Template position in search region: ({pt[0]}, {pt[1]})")
            print(f"  Monitor-relative position: ({match_x}, {match_y})")
            print(f"  Distance from calibration: {distance:.1f}px")
            print(f"  Confidence: {confidence:.3f}")
            
            # Save match region for debugging
            match_region = {
                "left": target_monitor["left"] + match_x - center_x,
                "top": target_monitor["top"] + match_y - center_y,
                "width": template_w,
                "height": template_h,
                "mon": target_monitor["name"]
            }
            
            with mss.mss() as sct:
                match_img = np.array(sct.grab(match_region))
            match_bgr = cv2.cvtColor(match_img, cv2.COLOR_BGRA2BGR)
            
            # Draw center point on match image
            match_debug = match_bgr.copy()
            cv2.circle(match_debug, (center_x, center_y), 3, (0, 0, 255), -1)
            
            # Save debug image
            cv2.imwrite(str(debug_dir / f'match_{button["button_num"]}_{int(match_x)}_{int(match_y)}.png'), match_debug)
            
            # Verify match with slightly relaxed thresholds
            if verify_match(match_bgr, button['pre_img'], correlation_threshold=0.7):
                print("Match verified!")
                print(f"Final position: ({match_x}, {match_y})")
                
                # Update best match if this is closer
                if distance < best_distance:
                    best_match = (match_x, match_y)
                    best_distance = distance
            else:
                print("Match failed verification")
        
        # Draw best match on visualization if found
        if best_match:
            match_x, match_y = best_match
            cv2.circle(visualization, (match_x, match_y), 5, (255, 0, 0), -1)  # Blue dot
            cv2.putText(visualization, f"Match {button['button_num']}", (match_x + 10, match_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            # Draw line between calibration point and match
            cv2.line(visualization, (cal_x, cal_y), (match_x, match_y), (0, 255, 0), 1)
    
    # Save visualization
    cv2.imwrite(str(debug_dir / 'calibration_matches.png'), visualization)
    
    print("\nAnalysis complete!")
    print("=" * 50)

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

def analyze_single_screenshot():
    """Take a single screenshot and analyze it for potential matches"""
    print("Taking full screen screenshot and analyzing...")
    print("=" * 50)
    
    target_monitor = get_monitor()
    if not target_monitor:
        print("Error: Could not find monitor 2!")
        return
    
    # Take full monitor screenshot
    with mss.mss() as sct:
        monitor_region = {
            "left": target_monitor["left"],
            "top": target_monitor["top"],
            "width": target_monitor["width"],
            "height": target_monitor["height"],
            "mon": target_monitor["name"]
        }
        full_screenshot = np.array(sct.grab(monitor_region))
    
    # Convert to BGR for OpenCV
    screenshot_bgr = cv2.cvtColor(full_screenshot, cv2.COLOR_BGRA2BGR)
    visualization = screenshot_bgr.copy()
    
    # Load calibration data
    assets_dir = Path('assets/monitor_0')
    pre_click_files = sorted(assets_dir.glob('button_*_pre.png'))
    coords_files = sorted(assets_dir.glob('click_coords_*.txt'))
    
    if not pre_click_files:
        print("No button images found!")
        return
    
    # Create debug directory
    debug_dir = Path('debug')
    debug_dir.mkdir(exist_ok=True)
    
    # Define colors for each button (BGR format)
    button_colors = [
        (0, 255, 0),    # Green for button 1
        (0, 255, 255),  # Yellow for button 2
        (0, 0, 255)     # Red for button 3
    ]
    
    # Load and analyze each button
    for i, (pre_file, coords_file) in enumerate(zip(pre_click_files, coords_files), 1):
        print(f"\nAnalyzing Button {i}...")
        
        # Load template and coordinates
        template = cv2.imread(str(pre_file))
        if template is None:
            print(f"Failed to load template {pre_file}")
            continue
            
        with open(coords_file) as f:
            cal_x, cal_y = map(int, f.read().strip().split(','))
        
        print(f"Calibration position: ({cal_x}, {cal_y})")
        
        # Draw calibration point
        color = button_colors[i-1]
        cv2.circle(visualization, (cal_x, cal_y), 8, color, -1)
        cv2.putText(visualization, f"Cal {i}", (cal_x + 15, cal_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        
        # Find all matches in the screenshot
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCORR_NORMED)
        
        # Get matches
        matches = []
        template_h, template_w = template.shape[:2]
        
        # Flatten result array and get indices of top matches
        flat_result = result.flatten()
        top_indices = np.argsort(flat_result)[-50:]  # Get more initial matches
        
        for idx in top_indices[::-1]:  # Process highest confidence first
            # Convert flat index back to 2D coordinates
            y_idx, x_idx = np.unravel_index(idx, result.shape)
            confidence = flat_result[idx]
            
            if confidence < 0.9:  # Only consider very high confidence matches
                continue
                
            match_x = x_idx + template_w//2
            match_y = y_idx + template_h//2
            
            # Add to matches list
            matches.append({
                'x': match_x,
                'y': match_y,
                'confidence': confidence
            })
        
        # Group matches by x-axis position (within 20px)
        x_groups = {}
        for match in matches:
            grouped = False
            for base_x in x_groups:
                if abs(match['x'] - base_x) <= 20:
                    x_groups[base_x].append(match)
                    grouped = True
                    break
            if not grouped:
                x_groups[match['x']] = [match]
        
        # Find best match in each x-position group
        best_matches = []
        for base_x, group in x_groups.items():
            # Sort by confidence first, then y-position
            group.sort(key=lambda m: (m['confidence'], m['y']), reverse=True)
            best_matches.append(group[0])
        
        # Sort final matches by confidence
        best_matches.sort(key=lambda m: m['confidence'], reverse=True)
        top_matches = best_matches[:5]
        
        print(f"\nTop {len(top_matches)} matches for Button {i} (grouped by x-position):")
        for idx, match in enumerate(top_matches, 1):
            print(f"Match {idx}:")
            print(f"  Position: ({match['x']}, {match['y']})")
            print(f"  Confidence: {match['confidence']:.3f}")
            
            # Draw match on visualization
            cv2.circle(visualization, (match['x'], match['y']), 6, color, -1)
            cv2.putText(visualization, f"{match['confidence']:.3f}", 
                       (match['x'] + 10, match['y'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw line to calibration point
            cv2.line(visualization, (cal_x, cal_y), 
                    (match['x'], match['y']), color, 1)
    
    # Add legend
    legend_y = 30
    for i, color in enumerate(button_colors, 1):
        cv2.putText(visualization, f"Button {i}", (10, legend_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        legend_y += 25
    
    # Save the visualization
    cv2.imwrite(str(debug_dir / 'top_matches.png'), visualization)
    print("\nSaved visualization to debug/top_matches.png")
    print("=" * 50)

if __name__ == "__main__":
    analyze_single_screenshot() 