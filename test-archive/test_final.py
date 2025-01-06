import cv2
import numpy as np
from PIL import Image
import os
import logging
import pyautogui
import time
from datetime import datetime
import mss

# Set up logging
logging.basicConfig(level=logging.INFO)

def find_cursor_monitor():
    """Find the monitor containing the Cursor application."""
    logging.info("Searching for monitor with Cursor application...")
    
    # Load reference image
    ref_path = os.path.join("images", "cursor-screen-head.png")
    reference_img = cv2.imread(ref_path)
    if reference_img is None:
        logging.error(f"Reference image not found at {ref_path}")
        return None
        
    with mss.mss() as sct:
        # Check each monitor
        for i, monitor in enumerate(sct.monitors[1:], 1):
            logging.info(f"Checking monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Capture top portion of monitor
            area = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": 50  # Only check top 50 pixels
            }
            
            try:
                # Capture and convert to numpy array
                screenshot = sct.grab(area)
                screen_img = np.array(screenshot)
                
                # Convert to BGR (OpenCV format)
                screen_img = screen_img[:, :, :3]
                
                # Template matching
                result = cv2.matchTemplate(screen_img, reference_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                logging.info(f"Monitor {i} match confidence: {max_val:.3f}")
                
                if max_val > 0.8:  # High confidence threshold
                    logging.info(f"Found Cursor application on monitor {i}")
                    return monitor
                    
            except Exception as e:
                logging.warning(f"Error checking monitor {i}: {str(e)}")
                continue
    
    logging.warning("Could not find Cursor application, falling back to primary monitor")
    return sct.monitors[1]

def test_final():
    """Test the complete click bot functionality."""
    
    # Configure pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    
    # Find the correct monitor first
    monitor = find_cursor_monitor()
    if not monitor:
        logging.error("Failed to find Cursor monitor")
        return
        
    logging.info(f"Using monitor: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
    
    # Load target image
    target_path = os.path.join("images", "target.png")
    target = Image.open(target_path)
    target = target.convert('RGB')
    target_np = np.array(target)
    target_bgr = cv2.cvtColor(target_np, cv2.COLOR_RGB2BGR)
    
    # Take screenshot of the correct monitor
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        screen_np = np.array(screenshot)
        screen_bgr = screen_np[:, :, :3]  # Remove alpha channel
    
    # Save raw screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("debug_output/screenshots", exist_ok=True)
    screen_path = f"debug_output/screenshots/raw_screen_{timestamp}.png"
    cv2.imwrite(screen_path, screen_bgr)
    logging.info(f"Saved raw screenshot: {screen_path}")
    
    # Log shapes
    logging.info(f"Target shape: {target_bgr.shape}, dtype: {target_bgr.dtype}")
    logging.info(f"Screen shape: {screen_bgr.shape}, dtype: {screen_bgr.dtype}")
    
    # Perform template matching
    result = cv2.matchTemplate(screen_bgr, target_bgr, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    # Get all matches above threshold
    threshold = 0.8  # High confidence threshold
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))  # Convert to list of (x,y) coordinates
    
    logging.info(f"\nFound {len(matches)} matches with confidence >= {threshold}")
    logging.info(f"Best match confidence: {max_val:.4f}")
    logging.info(f"Best match location: {max_loc}")
    
    if max_val >= threshold:
        # Save debug image
        debug_img = screen_bgr.copy()
        x, y = max_loc
        h, w = target_bgr.shape[:2]
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(debug_img, f"Conf: {max_val:.4f}", (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
        debug_path = f"debug_output/final_match_{timestamp}.png"
        cv2.imwrite(debug_path, debug_img)
        logging.info(f"Saved debug image: {debug_path}")
        
        # Calculate click position (center of match)
        click_x = monitor['left'] + x + w // 2  # Add monitor offset
        click_y = monitor['top'] + y + h // 2   # Add monitor offset
        logging.info(f"Click position: ({click_x}, {click_y})")
        
        # Ask for confirmation before clicking
        response = input(f"\nFound target with {max_val:.2%} confidence at ({click_x}, {click_y}). Click? [y/N] ")
        if response.lower() == 'y':
            # Save current mouse position
            original_x, original_y = pyautogui.position()
            
            try:
                # Move to target and click
                pyautogui.moveTo(click_x, click_y, duration=0.2)
                time.sleep(0.1)  # Short pause
                pyautogui.click()
                time.sleep(0.1)  # Short pause
                
                # Return to original position
                pyautogui.moveTo(original_x, original_y, duration=0.1)
                logging.info("Click executed successfully")
                
            except Exception as e:
                logging.error(f"Error during click operation: {str(e)}")
        else:
            logging.info("Click operation skipped by user")
    else:
        logging.info(f"No matches found above threshold {threshold}")

if __name__ == "__main__":
    test_final() 