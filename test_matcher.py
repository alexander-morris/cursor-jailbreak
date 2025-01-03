import cv2
import numpy as np
from PIL import Image
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_simple_match():
    # Load target image
    target_path = os.path.join("images", "target.png")
    target = Image.open(target_path)
    target = target.convert('RGB')
    target_np = np.array(target)
    
    # Load a raw screenshot
    screenshots_dir = os.path.join("debug_output", "screenshots")
    screenshots = sorted(os.listdir(screenshots_dir))
    if not screenshots:
        logging.error("No screenshots found!")
        return
        
    screenshot_path = os.path.join(screenshots_dir, screenshots[-1])  # Get most recent
    logging.info(f"Testing with screenshot: {screenshot_path}")
    
    screenshot = Image.open(screenshot_path)
    screenshot = screenshot.convert('RGB')
    screenshot_np = np.array(screenshot)
    
    # Convert both to BGR for OpenCV
    target_bgr = cv2.cvtColor(target_np, cv2.COLOR_RGB2BGR)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # Log shapes and data types
    logging.info(f"Target shape: {target_bgr.shape}, dtype: {target_bgr.dtype}")
    logging.info(f"Screenshot shape: {screenshot_bgr.shape}, dtype: {screenshot_bgr.dtype}")
    
    # Perform template matching
    result = cv2.matchTemplate(screenshot_bgr, target_bgr, cv2.TM_CCOEFF_NORMED)
    
    # Get all matches above various thresholds
    thresholds = [0.001, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9]
    for threshold in thresholds:
        locations = np.where(result >= threshold)
        match_count = len(locations[0])
        if match_count > 0:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            logging.info(f"\nThreshold {threshold}:")
            logging.info(f"Found {match_count} matches")
            logging.info(f"Best match confidence: {max_val:.4f}")
            logging.info(f"Best match location: {max_loc}")
            
            # Save debug image for best match
            debug_img = screenshot_bgr.copy()
            x, y = max_loc
            h, w = target_bgr.shape[:2]
            cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(debug_img, f"Conf: {max_val:.4f}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            debug_path = f"debug_output/test_match_t{threshold:.3f}.png"
            cv2.imwrite(debug_path, debug_img)
            logging.info(f"Saved debug image: {debug_path}")
        else:
            logging.info(f"\nThreshold {threshold}: No matches found")

if __name__ == "__main__":
    test_simple_match() 