import cv2
import numpy as np
from pathlib import Path
import mss
import pyautogui
import time
from PIL import Image

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

def load_calibration_data():
    """Load calibration data from assets directory"""
    assets_dir = Path('assets/monitor_0')
    if not assets_dir.exists():
        print("No calibration data found!")
        return None
    
    pre_click_files = sorted(assets_dir.glob('button_*_pre.png'))
    post_click_files = sorted(assets_dir.glob('button_*_post.png'))
    coords_files = sorted(assets_dir.glob('click_coords_*.txt'))
    
    if not pre_click_files:
        print("No button images found!")
        return None
    
    buttons = []
    for i, (pre_file, post_file, coords_file) in enumerate(zip(pre_click_files, post_click_files, coords_files), 1):
        pre_img = cv2.imread(str(pre_file))
        post_img = cv2.imread(str(post_file))
        if pre_img is None or post_img is None:
            print(f"Failed to load images for button {i}")
            continue
            
        with open(coords_file) as f:
            cal_x, cal_y = map(int, f.read().strip().split(','))
        
        buttons.append({
            'pre_img': pre_img,
            'post_img': post_img,
            'cal_x': cal_x,
            'cal_y': cal_y,
            'button_num': i
        })
        print(f"Loaded Button {i}:")
        print(f"  Calibration position: ({cal_x}, {cal_y})")
        print(f"  Template size: {pre_img.shape[1]}x{pre_img.shape[0]}")
    
    return buttons

def find_exact_match(screen_img, template_img, cal_x, cal_y, max_distance=25):
    """Find exact match within max_distance of calibration point"""
    # Convert both images to grayscale for more robust matching
    if len(screen_img.shape) == 3:
        screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    else:
        screen_gray = screen_img
        
    if len(template_img.shape) == 3:
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template_img
    
    # Try different matching methods
    methods = [
        (cv2.TM_CCORR_NORMED, 0.8),
        (cv2.TM_CCOEFF_NORMED, 0.6)
    ]
    
    best_match = None
    best_distance = float('inf')
    best_confidence = 0
    best_method = None
    
    template_h, template_w = template_img.shape[:2]
    
    for method, threshold in methods:
        result = cv2.matchTemplate(screen_gray, template_gray, method)
        locations = np.where(result >= threshold)
        
        for pt in zip(*locations[::-1]):
            # Calculate center of match
            match_x = pt[0] + template_w // 2
            match_y = pt[1] + template_h // 2
            
            # Calculate distance from calibration point
            distance = ((match_x - cal_x) ** 2 + (match_y - cal_y) ** 2) ** 0.5
            confidence = result[pt[1], pt[0]]
            
            if distance <= max_distance and confidence > best_confidence:
                best_confidence = confidence
                best_distance = distance
                best_match = (match_x, match_y, confidence, distance)
                best_method = method
    
    if best_match:
        print(f"Best match found using method: {best_method}")
    
    return best_match

def verify_match(current_img, template_img, threshold=0.75):
    """Verify if current image matches template using multiple methods"""
    # Convert images to grayscale
    if len(current_img.shape) == 3:
        current_gray = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
    else:
        current_gray = current_img
        
    if len(template_img.shape) == 3:
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template_img
    
    # Method 1: Template matching
    result = cv2.matchTemplate(current_gray, template_gray, cv2.TM_CCORR_NORMED)
    correlation = np.max(result)
    
    # Method 2: Mean squared error
    if current_gray.shape == template_gray.shape:
        mse = np.mean((current_gray - template_gray) ** 2)
        mse_score = 1 - (mse / 255**2)
    else:
        mse_score = 0
    
    # Method 3: Structural similarity
    if current_gray.shape == template_gray.shape:
        try:
            from skimage.metrics import structural_similarity as ssim
            ssim_score = ssim(current_gray, template_gray)
        except ImportError:
            ssim_score = 0
    else:
        ssim_score = 0
    
    # Combine scores with weights
    final_score = (0.6 * correlation + 0.3 * mse_score + 0.1 * ssim_score)
    
    print(f"Verification scores:")
    print(f"  Correlation: {correlation:.3f}")
    print(f"  MSE Score: {mse_score:.3f}")
    print(f"  SSIM Score: {ssim_score:.3f}")
    print(f"  Final Score: {final_score:.3f}")
    
    return final_score >= threshold

def analyze_calibration():
    """Analyze calibration data and find exact matches"""
    target_monitor = get_monitor()
    if not target_monitor:
        return
    
    buttons = load_calibration_data()
    if not buttons:
        return
    
    print("\nStarting analysis...")
    print("Will search for exact matches near calibration points")
    print("=" * 50)
    
    # Take full screenshot of monitor 2
    monitor_region = {
        "left": target_monitor["left"],
        "top": target_monitor["top"],
        "width": target_monitor["width"],
        "height": target_monitor["height"],
        "mon": target_monitor["name"]
    }
    
    with mss.mss() as sct:
        screen = np.array(sct.grab(monitor_region))
    screen_bgr = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
    
    for button in buttons:
        print(f"\nAnalyzing Button {button['button_num']}:")
        print(f"Looking for match near ({button['cal_x']}, {button['cal_y']})")
        
        match = find_exact_match(
            screen_bgr, 
            button['pre_img'],
            button['cal_x'],
            button['cal_y']
        )
        
        if match:
            match_x, match_y, confidence, distance = match
            print(f"Found match!")
            print(f"  Match position: ({match_x}, {match_y})")
            print(f"  Distance from calibration: {distance:.1f}px")
            print(f"  Confidence: {confidence:.3f}")
            
            # Move to match position to verify
            screen_x = target_monitor["left"] + match_x
            screen_y = target_monitor["top"] + match_y
            print(f"Moving to match position...")
            pyautogui.moveTo(screen_x, screen_y, duration=0.5)
            time.sleep(0.5)  # Wait for mouse movement
            
            # Verify match by capturing current state
            template_h, template_w = button['pre_img'].shape[:2]
            verify_region = {
                "left": screen_x - template_w // 2,
                "top": screen_y - template_h // 2,
                "width": template_w,
                "height": template_h,
                "mon": target_monitor["name"]
            }
            
            with mss.mss() as sct:
                current = np.array(sct.grab(verify_region))
            current_bgr = cv2.cvtColor(current, cv2.COLOR_BGRA2BGR)
            
            # Save debug images
            debug_dir = Path('debug')
            debug_dir.mkdir(exist_ok=True)
            cv2.imwrite(str(debug_dir / f'button_{button["button_num"]}_template.png'), button['pre_img'])
            cv2.imwrite(str(debug_dir / f'button_{button["button_num"]}_current.png'), current_bgr)
            
            if verify_match(current_bgr, button['pre_img']):
                print("Match verified!")
                print("Saving debug images to debug directory")
            else:
                print("Match failed verification")
                print("Saving debug images to debug directory")
        else:
            print("No match found within 25px of calibration point")
    
    print("\nAnalysis complete!")
    print("=" * 50)

if __name__ == "__main__":
    analyze_calibration() 