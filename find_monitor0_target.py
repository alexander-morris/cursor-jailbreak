import cv2
import numpy as np
import pyautogui
import time
import logging
import mss
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def find_targets():
    """Find target buttons on monitor 0 using template matching with scale variations"""
    try:
        with mss.mss() as sct:
            # Get monitor 0 (the main display at 0,0)
            monitor = None
            for i, m in enumerate(sct.monitors[1:], 1):
                if m['left'] == 0 and m['top'] == 0:
                    monitor = m
                    logger.info(f"Found main display (monitor 0) at index {i}")
                    break
            
            if monitor is None:
                raise ValueError("Could not find monitor 0 (main display at 0,0)")
            
            logger.info(f"Monitor 0: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Load target image
            target_path = Path('images/target.png')
            if not target_path.exists():
                raise ValueError("target.png not found in images directory")
            target_button = cv2.imread(str(target_path))
            if target_button is None:
                raise ValueError("Failed to load target.png")
            
            # Capture monitor
            screenshot = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Create debug image
            debug_img = img_bgr.copy()
            
            # Only search in the right half of the screen
            h, w = img_bgr.shape[:2]
            right_half_start = w // 2
            img_bgr = img_bgr[:, right_half_start:]
            
            # Draw search region on debug image
            cv2.line(debug_img, (right_half_start, 0), (right_half_start, h), (0, 255, 0), 2)
            cv2.putText(debug_img, "Search Region", (right_half_start + 10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Try different scales with more focused matching
            scales = [0.95, 1.0, 1.05]  # Very small scale variations
            methods = [
                (cv2.TM_CCOEFF_NORMED, 0.65),  # Slightly higher threshold for better precision
            ]
            best_matches = []
            
            for scale in scales:
                # Resize target image
                target_h, target_w = target_button.shape[:2]
                new_h, new_w = int(target_h * scale), int(target_w * scale)
                target_resized = cv2.resize(target_button, (new_w, new_h))
                
                # Convert both to YUV color space for better matching
                img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
                target_yuv = cv2.cvtColor(target_resized, cv2.COLOR_BGR2YUV)
                
                for method, threshold in methods:
                    # Match in YUV space
                    result = cv2.matchTemplate(img_yuv, target_yuv, method)
                    
                    # Find matches
                    locations = np.where(result >= threshold)
                    matches_found = len(locations[0])
                    logger.info(f"Scale {scale:.2f}, found {matches_found} matches above {threshold}")
                    
                    # Process matches
                    for pt in zip(*locations[::-1]):
                        x, y = pt[0], pt[1]
                        
                        # Convert x back to full screen coordinates
                        x += right_half_start
                        
                        # Skip if outside bounds
                        if x < right_half_start or x + new_w > monitor["width"] or y < 0 or y + new_h > monitor["height"]:
                            continue
                        
                        # Calculate center and confidence
                        center_x = x + new_w//2
                        center_y = y + new_h//2
                        confidence = result[y, pt[0]]  # Use original x for confidence lookup
                        
                        # Check if too close to existing match
                        too_close = False
                        for existing in best_matches:
                            ex, ey, _, _ = existing
                            if abs(center_x - ex) < 15 and abs(center_y - ey) < 15:  # Even smaller distance threshold
                                too_close = True
                                if confidence > existing[2]:
                                    best_matches.remove(existing)
                                    too_close = False
                                break
                        
                        if not too_close:
                            best_matches.append((center_x, center_y, confidence, scale))
                            logger.info(f"Found potential match at ({center_x}, {center_y}) "
                                      f"with confidence {confidence:.3f}")
                            
                            # Draw match on debug image
                            cv2.rectangle(debug_img, 
                                        (x, y),
                                        (x + new_w, y + new_h),
                                        (0, 255, 0), 2)
                            cv2.putText(debug_img,
                                      f"{confidence:.2f}",
                                      (x, y - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save debug image
            debug_dir = Path('temp/debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            cv2.imwrite(str(debug_dir / f'target_search_{timestamp}.png'), debug_img)
            
            # Convert best matches to screen coordinates
            found_targets = []
            for x, y, confidence, scale in best_matches:
                screen_x = monitor["left"] + int(x)
                screen_y = monitor["top"] + int(y)
                found_targets.append((screen_x, screen_y))
                logger.info(f"Found target at ({screen_x}, {screen_y}) with confidence {confidence:.3f} at scale {scale:.2f}")
            
            if found_targets:
                logger.info(f"Total targets found: {len(found_targets)}")
                return True, found_targets
            
            return False, None
            
    except Exception as e:
        logger.error(f"Error finding targets: {str(e)}")
        return False, None

def click_target(x, y):
    """Click a target at the given coordinates"""
    try:
        # Store original position
        original_x, original_y = pyautogui.position()
        
        # Move to target
        logger.info(f"Moving to target at ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        
        # Click and verify
        with mss.mss() as sct:
            # Capture before click
            before = np.array(sct.grab({
                'left': x - 10,
                'top': y - 10,
                'width': 20,
                'height': 20
            }))
            
            # Click
            pyautogui.click()
            time.sleep(0.5)  # Increased delay to ensure visual change is captured
            
            # Capture after click
            after = np.array(sct.grab({
                'left': x - 10,
                'top': y - 10,
                'width': 20,
                'height': 20
            }))
            
            # Check for visual change
            diff = cv2.absdiff(before, after)
            mean_diff = np.mean(diff)
            logger.info(f"Visual change: {mean_diff:.2f}")
            
            if mean_diff > 5:  # Increased threshold for visual change detection
                logger.info("Click successful - visual change detected")
                success = True
            else:
                logger.warning("No visual change detected after click")
                success = False
        
        # Restore cursor position
        pyautogui.moveTo(original_x, original_y, duration=0.2)
        return success
        
    except Exception as e:
        logger.error(f"Error clicking target: {str(e)}")
        return False

def main():
    try:
        logger.info("Starting target detection on monitor 0")
        logger.info("Press Ctrl+C to stop")
        
        while True:
            found, targets = find_targets()
            if found:
                for target_coords in targets:
                    if click_target(*target_coords):
                        time.sleep(0.5)  # Small delay between clicks
            time.sleep(0.1)  # Small delay between scans
            
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 