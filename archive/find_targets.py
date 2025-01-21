#!/usr/bin/env python3
import cv2
import numpy as np
import mss
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_two_targets(debug=True):
    """Find exactly two instances of target.png across all monitors"""
    try:
        # Load target image
        target_path = Path('images/target.png')
        if not target_path.exists():
            raise ValueError("target.png not found in images directory")
        target = cv2.imread(str(target_path))
        if target is None:
            raise ValueError("Failed to load target.png")
        
        logger.info(f"Target image size: {target.shape}")
        
        # Initialize screen capture
        sct = mss.mss()
        monitors = sct.monitors[1:]  # Skip the "all monitors" monitor
        logger.info(f"Found {len(monitors)} monitors")
        for i, m in enumerate(monitors):
            logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        
        found_targets = []
        
        # Create debug directory
        if debug:
            debug_dir = Path('temp/debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Search each monitor
        for monitor_index, monitor in enumerate(monitors):
            # Only search rightmost quarter of screen
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Create debug image
            if debug:
                debug_img = img_bgr.copy()
            
            h, w = img_bgr.shape[:2]
            right_quarter_start = int(w / 2)  # Start at 50% of width
            right_quarter = img_bgr[:, right_quarter_start:]
            
            # Draw search region on debug image
            if debug:
                cv2.line(debug_img, (right_quarter_start, 0), (right_quarter_start, h), (0, 255, 0), 2)
                cv2.putText(debug_img, "Search Region", (right_quarter_start + 10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Find matches with lower threshold
            result = cv2.matchTemplate(right_quarter, target, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            logger.info(f"Monitor {monitor_index} - Max confidence: {max_val:.3f}")
            
            # Use two thresholds: one for initial detection, one for confirmation
            initial_threshold = 0.6  # Lower threshold to catch more potential matches
            confirm_threshold = 0.75  # Lower confirmation threshold
            
            locations = np.where(result >= initial_threshold)
            matches_found = len(locations[0])
            logger.info(f"Monitor {monitor_index} - Found {matches_found} potential matches above {initial_threshold}")
            
            # Draw heatmap on debug image
            if debug:
                # Normalize result to 0-255 for visualization
                result_norm = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                result_color = cv2.applyColorMap(result_norm, cv2.COLORMAP_JET)
                # Resize to match target height
                result_resized = cv2.resize(result_color, (w//4, h))
                # Overlay on right quarter
                alpha = 0.3
                debug_img[:, right_quarter_start:] = cv2.addWeighted(
                    debug_img[:, right_quarter_start:], 1-alpha,
                    result_resized, alpha, 0
                )
            
            # Process matches
            for pt in zip(*locations[::-1]):
                # Get confidence score
                confidence = result[pt[1], pt[0]]
                
                # Convert to screen coordinates
                screen_x = monitor["left"] + (pt[0] + right_quarter_start) + target.shape[1]//2
                screen_y = monitor["top"] + pt[1] + target.shape[0]//2
                
                # Draw match on debug image
                if debug:
                    local_x = pt[0] + right_quarter_start
                    local_y = pt[1]
                    color = (0, 255, 0) if confidence >= confirm_threshold else (0, 165, 255)
                    cv2.rectangle(debug_img,
                                (local_x, local_y),
                                (local_x + target.shape[1], local_y + target.shape[0]),
                                color, 2)
                    cv2.putText(debug_img,
                              f"{confidence:.2f}",
                              (local_x, local_y - 5),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              0.5,
                              color,
                              1)
                
                # Only process high confidence matches
                if confidence >= confirm_threshold:
                    # Check if this match is close to any existing matches
                    is_duplicate = False
                    for x, y in found_targets:
                        if abs(screen_x - x) < 10 and abs(screen_y - y) < 10:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        found_targets.append((screen_x, screen_y))
                        logger.info(f"Found target at ({screen_x}, {screen_y}) on monitor {monitor_index} with confidence {confidence:.3f}")
                        
                        # Draw confirmed match on debug image
                        if debug:
                            cv2.circle(debug_img, (local_x + target.shape[1]//2, local_y + target.shape[0]//2),
                                     10, (0, 0, 255), 2)
                        
                        # If we have two targets, we're done
                        if len(found_targets) == 2:
                            if debug:
                                # Save final debug image
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                cv2.imwrite(str(debug_dir / f'monitor{monitor_index}_final_{timestamp}.png'), debug_img)
                            logger.info("Found both targets!")
                            return found_targets
            
            # Save debug image for this monitor
            if debug:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                cv2.imwrite(str(debug_dir / f'monitor{monitor_index}_{timestamp}.png'), debug_img)
        
        # If we get here, we didn't find two targets
        if found_targets:
            logger.warning(f"Only found {len(found_targets)} target(s)")
            return found_targets
        else:
            logger.warning("No targets found")
            return []
            
    except Exception as e:
        logger.error(f"Error finding targets: {str(e)}")
        return []

if __name__ == "__main__":
    targets = find_two_targets(debug=True)
    if len(targets) == 2:
        logger.info("Success! Found both targets:")
        for i, (x, y) in enumerate(targets, 1):
            logger.info(f"Target {i}: ({x}, {y})")
    else:
        logger.error(f"Failed to find both targets. Found {len(targets)} target(s)") 