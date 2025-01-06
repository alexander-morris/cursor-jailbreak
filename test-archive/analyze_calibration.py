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

def preprocess_for_matching(img):
    """Preprocess image for better matching"""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Enhance edges
    edges = cv2.Canny(gray, 50, 150)
    
    # Dilate edges slightly to make them more robust
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    
    return dilated

def find_exact_match(screen_img, template_img, cal_x, cal_y, max_distance=5):
    """Find exact match within max_distance horizontally and up to 80px vertically"""
    # First pass: Use edge detection to find approximate location
    screen_edges = preprocess_for_matching(screen_img)
    template_edges = preprocess_for_matching(template_img)
    
    template_h, template_w = template_img.shape[:2]
    
    # Define asymmetric search region - wide vertically, narrow horizontally
    vertical_margin = 80  # Allow full 80px vertical movement
    horizontal_margin = 40  # Increased to accommodate template width
    
    # Calculate search boundaries
    search_top = max(0, cal_y - vertical_margin)
    search_bottom = min(screen_img.shape[0], cal_y + vertical_margin)
    search_left = max(0, cal_x - horizontal_margin)
    search_right = min(screen_img.shape[1], cal_x + horizontal_margin)
    
    print(f"\nDebug: Search region:")
    print(f"  Vertical range: {search_top} to {search_bottom} (±{vertical_margin}px)")
    print(f"  Horizontal range: {search_left} to {search_right} (±{horizontal_margin}px)")
    print(f"  Template size: {template_w}x{template_h}")
    print(f"  Target x: {cal_x} (±{max_distance}px)")
    
    # Get search regions for both edge and original images
    search_region_edges = screen_edges[search_top:search_bottom, search_left:search_right]
    
    if search_region_edges.shape[0] < template_h or search_region_edges.shape[1] < template_w:
        print("Search region too small for template")
        return None
    
    # Convert images to grayscale for direct matching
    if len(template_img.shape) == 3:
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template_img.copy()
    
    if len(screen_img.shape) == 3:
        screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    else:
        screen_gray = screen_img.copy()
    
    search_region_gray = screen_gray[search_top:search_bottom, search_left:search_right]
    
    # Try different scales
    scales = [1.0, 0.995, 1.005]
    best_match = None
    best_distance = float('inf')
    best_confidence = 0
    
    for scale in scales:
        if scale != 1.0:
            scaled_template_edges = cv2.resize(template_edges, 
                (int(template_w * scale), int(template_h * scale)),
                interpolation=cv2.INTER_NEAREST)
            scaled_template_gray = cv2.resize(template_gray,
                (int(template_w * scale), int(template_h * scale)),
                interpolation=cv2.INTER_LINEAR)
        else:
            scaled_template_edges = template_edges
            scaled_template_gray = template_gray
        
        scaled_h, scaled_w = scaled_template_edges.shape[:2]
        
        if search_region_edges.shape[0] < scaled_h or search_region_edges.shape[1] < scaled_w:
            continue
        
        # First pass: Match edges to find potential locations
        edge_result = cv2.matchTemplate(search_region_edges, scaled_template_edges, cv2.TM_CCOEFF_NORMED)
        edge_matches = np.where(edge_result >= 0.3)
        edge_confidences = edge_result[edge_matches[0], edge_matches[1]]
        
        print(f"\nFound {len(edge_matches[0])} potential edge matches")
        if len(edge_matches[0]) > 0:
            print(f"Edge confidence range: {np.min(edge_confidences):.4f} - {np.max(edge_confidences):.4f}")
        
        # Sort matches by confidence
        match_data = list(zip(edge_matches[1], edge_matches[0], edge_confidences))
        match_data.sort(key=lambda x: x[2], reverse=True)
        
        # Check top matches
        for pt_x, pt_y, edge_conf in match_data[:20]:
            # Calculate absolute position
            abs_x = search_left + pt_x
            abs_y = search_top + pt_y
            
            # Get ROI for both edge and direct matching
            roi_edges = search_region_edges[pt_y:pt_y+scaled_h, pt_x:pt_x+scaled_w]
            roi_gray = search_region_gray[pt_y:pt_y+scaled_h, pt_x:pt_x+scaled_w]
            
            if roi_edges.shape != scaled_template_edges.shape or roi_gray.shape != scaled_template_gray.shape:
                continue
            
            # Second pass: Direct template matching on grayscale
            direct_result = cv2.matchTemplate(roi_gray, scaled_template_gray, cv2.TM_CCOEFF_NORMED)
            direct_conf = direct_result[0][0]
            
            # Calculate edge overlap ratio
            edge_overlap = np.sum(roi_edges & scaled_template_edges) / np.sum(scaled_template_edges)
            
            # Calculate center based on actual button pixels
            match_x = abs_x + scaled_w // 2
            match_y = abs_y + scaled_h // 2
            
            # Calculate horizontal and vertical distances from calibration point
            h_distance = abs(match_x - cal_x)
            v_distance = abs(match_y - cal_y)
            
            # Only proceed if horizontal distance is within tolerance
            if h_distance <= max_distance and v_distance <= vertical_margin:
                print(f"\nChecking match at ({match_x}, {match_y}):")
                print(f"  Horizontal distance: {h_distance:.2f}px")
                print(f"  Vertical distance: {v_distance:.2f}px")
                print(f"  Edge confidence: {edge_conf:.4f}")
                print(f"  Direct confidence: {direct_conf:.4f}")
                print(f"  Edge overlap: {edge_overlap:.4f}")
                
                # Combined score weighted towards direct matching
                match_quality = (direct_conf * 0.5 + edge_overlap * 0.3 + edge_conf * 0.2)
                print(f"  Match quality: {match_quality:.4f}")
                
                if match_quality > 0.5:  # Require higher quality for combined matching
                    if h_distance < best_distance or (h_distance == best_distance and match_quality > best_confidence):
                        best_distance = h_distance
                        best_confidence = match_quality
                        best_match = (match_x, match_y, match_quality, h_distance)
                        print("  → Selected as best match so far")
    
    if best_match:
        print(f"\nFinal match results:")
        print(f"  Horizontal distance: {best_distance:.2f}px")
        print(f"  Vertical offset: {abs(best_match[1] - cal_y):.2f}px")
        print(f"  Match quality: {best_confidence:.4f}")
        print(f"  Position: ({best_match[0]}, {best_match[1]})")
        
        if best_distance <= max_distance:
            print(f"✓ Match within horizontal precision of {max_distance}px")
        else:
            print(f"⚠ Match outside horizontal precision of {max_distance}px")
    
    return best_match if best_match and best_distance <= max_distance else None

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