import cv2
import numpy as np
import mss
import time
from pathlib import Path
from PIL import Image, ImageDraw
import logging
import pyautogui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calibrate():
    """Calibrate by capturing the accept button template"""
    logger.info("\n=== Calibration Step ===")
    logger.info("1. Move your cursor to monitor 2")
    logger.info("2. Position cursor over an accept button")
    logger.info("3. Keep it there for 5 seconds")
    logger.info("\nStarting capture in 5 seconds...")
    time.sleep(5)
    
    # Get mouse position
    click_x, click_y = pyautogui.position()
    logger.info(f"Mouse position: ({click_x}, {click_y})")
    
    # Capture region around mouse
    with mss.mss() as sct:
        # Original working size: 80x40
        region = {"top": click_y-20, "left": click_x-40, "width": 80, "height": 40}
        screenshot = sct.grab(region)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        
        # Save debug image of captured region
        debug_dir = Path('debug')
        debug_dir.mkdir(exist_ok=True)
        img.save(debug_dir / "calibration_region.png")
        
        # Convert to OpenCV format
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # Ensure template is in correct orientation (80x40)
        if img_bgr.shape[0] != 40 or img_bgr.shape[1] != 80:
            logger.warning(f"Template has wrong dimensions: {img_bgr.shape}, rotating...")
            img_bgr = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
            logger.info(f"New template dimensions: {img_bgr.shape}")
        
        # Save template
        assets_dir = Path('assets')
        monitor_assets = assets_dir / "monitor_0"
        monitor_assets.mkdir(exist_ok=True, parents=True)
        calibration_file = monitor_assets / 'accept_button.png'
        coords_file = monitor_assets / 'click_coords.txt'
        
        cv2.imwrite(str(calibration_file), img_bgr)  # Save in BGR format
        # Save click offset from template top-left (center of template)
        with open(coords_file, 'w') as f:
            f.write(f"40,20")  # Center of 80x40 region
            
        logger.info(f"Saved template to {calibration_file}")
        logger.info(f"Final template size: {img_bgr.shape}")
        return calibration_file

def test_template_matching(calibration_file):
    """Test template matching with debug output"""
    logger.info("\n=== Testing Template Matching ===")
    
    # Load template
    template = cv2.imread(str(calibration_file))
    if template is None:
        logger.error(f"Failed to load template from {calibration_file}")
        return
    
    # Ensure template is in correct orientation (80x40)
    if template.shape[0] != 40 or template.shape[1] != 80:
        logger.warning(f"Loaded template has wrong dimensions: {template.shape}, rotating...")
        template = cv2.rotate(template, cv2.ROTATE_90_CLOCKWISE)
        logger.info(f"New template dimensions: {template.shape}")
    
    logger.info(f"Template size: {template.shape}")
    
    # Save template for debugging
    debug_dir = Path('debug')
    debug_dir.mkdir(exist_ok=True)
    cv2.imwrite(str(debug_dir / "template.png"), template)
    
    # Get monitors
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # Skip the "all monitors" monitor
        logger.info(f"Found {len(monitors)} monitors")
        for i, m in enumerate(monitors):
            logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        
        # Monitor 2 would be index 1
        monitor_index = 2  # Use monitor 2 (index 2)
        if monitor_index >= len(monitors):
            logger.error(f"Monitor {monitor_index} not found")
            return
            
        monitor = monitors[monitor_index]
        logger.info(f"\nUsing monitor {monitor_index}: {monitor}")
        
        # Capture full monitor
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Save full screenshot for debugging
        cv2.imwrite(str(debug_dir / "full_screen.png"), img_bgr)
        
        # Try different thresholds
        thresholds = [0.6, 0.7, 0.8, 0.85, 0.9]
        
        for threshold in thresholds:
            logger.info(f"\nTrying threshold: {threshold}")
            
            # Template matching
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            
            # Find all matches above threshold
            locations = np.where(result >= threshold)
            matches = []
            
            # Group nearby matches
            used = set()
            for y, x in zip(*locations):
                point = (x, y)
                if point in used:
                    continue
                    
                # Mark nearby points as used
                for dx in range(-10, 11):
                    for dy in range(-10, 11):
                        used.add((x + dx, y + dy))
                        
                matches.append({
                    'confidence': result[y, x],
                    'x': x,
                    'y': y,
                    'width': template.shape[1],
                    'height': template.shape[0]
                })
                
                if len(matches) >= 3:  # Stop after finding 3 matches
                    break
            
            # Draw matches on debug image
            debug_img = img_bgr.copy()
            for match in matches:
                x, y = match['x'], match['y']
                w, h = match['width'], match['height']
                confidence = match['confidence']
                
                # Draw rectangle
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Draw confidence value
                cv2.putText(debug_img, f"{confidence:.2f}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
            # Save debug image
            cv2.imwrite(str(debug_dir / f"matches_t{threshold:.2f}.png"), debug_img)
            
            logger.info(f"Found {len(matches)} matches at threshold {threshold}:")
            for i, match in enumerate(matches):
                logger.info(f"Match {i+1}: confidence={match['confidence']:.2f} at ({match['x']}, {match['y']})")
                
            # Also save the correlation result for debugging
            cv2.normalize(result, result, 0, 255, cv2.NORM_MINMAX)
            cv2.imwrite(str(debug_dir / f"correlation_t{threshold:.2f}.png"), result)

def main():
    # First calibrate
    calibration_file = calibrate()
    
    # Wait a moment for user to trigger some accept buttons
    logger.info("\nWaiting 5 seconds for you to trigger some accept buttons...")
    time.sleep(5)
    
    # Then test matching
    test_template_matching(calibration_file)

if __name__ == "__main__":
    main() 