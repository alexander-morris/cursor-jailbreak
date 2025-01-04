#!/usr/bin/env python3
import cv2
import numpy as np
import mss
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_targets(debug=True):
    """Find target buttons across all monitors"""
    # Initialize screen capture
    with mss.mss() as sct:
        # Load target images (both normal and inverted)
        target = cv2.imread('images/target.png')
        if target is None:
            raise ValueError("Failed to load images/target.png")
        
        # Create inverted target
        target_inv = cv2.bitwise_not(target)
        
        # Load calibrated coordinates
        coords_file = Path('target_coords.json')
        if not coords_file.exists():
            raise ValueError("No calibration data found. Please run calibrate_coords.py first.")
        
        with coords_file.open('r') as f:
            calibrated_coords = json.load(f)
        logger.info(f"Loaded {len(calibrated_coords)} calibrated coordinates")
        
        # Create debug directory
        if debug:
            debug_dir = Path('temp/debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Get list of monitors (skip first which is "all monitors")
        monitors = sct.monitors[1:]
        logger.info(f"Searching {len(monitors)} monitors")
        
        found_targets = []
        
        # Search each monitor
        for monitor_index, monitor in enumerate(monitors):
            # Get calibrated coordinates for this monitor
            monitor_coords = [c for c in calibrated_coords if c["monitor"] == monitor_index]
            if not monitor_coords:
                logger.info(f"Monitor {monitor_index} has no calibrated targets, skipping")
                continue
            
            logger.info(f"Monitor {monitor_index} has {len(monitor_coords)} calibrated targets")
            
            # Capture screen
            screenshot = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Create debug image
            if debug:
                debug_img = img_bgr.copy()
            
            # Calculate monitor DPI scale factor
            dpi_scale = monitor["width"] / monitors[0]["width"]  # Use first monitor as reference
            if abs(dpi_scale - 1.0) > 0.1:  # Only scale if difference is significant
                logger.info(f"Monitor {monitor_index} has DPI scale factor: {dpi_scale:.2f}")
                scaled_target = cv2.resize(target, None, fx=dpi_scale, fy=dpi_scale)
                scaled_target_inv = cv2.resize(target_inv, None, fx=dpi_scale, fy=dpi_scale)
            else:
                scaled_target = target
                scaled_target_inv = target_inv
            
            # For each calibrated coordinate, search nearby region
            for coord in monitor_coords:
                # Convert global coordinates to local image coordinates
                local_x = int(coord["x"] - monitor["left"])
                local_y = int(coord["y"] - monitor["top"])
                
                # Define search region (200x200 pixels around calibrated point)
                region_size = 300
                x1 = max(0, local_x - region_size//2)
                y1 = max(0, local_y - region_size//2)
                x2 = min(img_bgr.shape[1], local_x + region_size//2)
                y2 = min(img_bgr.shape[0], local_y + region_size//2)
                
                # Draw search region on debug image
                if debug:
                    cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_img, "Search Region", (x1, y1-5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Extract region
                region = img_bgr[y1:y2, x1:x2]
                
                # Convert region to YUV color space (best for digital displays)
                region_yuv = cv2.cvtColor(region, cv2.COLOR_BGR2YUV)
                
                best_match = None
                best_confidence = 0
                best_is_inverted = False
                
                # Try both normal and inverted targets
                for template, is_inverted in [(scaled_target, False), (scaled_target_inv, True)]:
                    # Skip if region is smaller than template
                    if region.shape[0] < template.shape[0] or region.shape[1] < template.shape[1]:
                        continue
                    
                    # Convert template to YUV color space
                    template_yuv = cv2.cvtColor(template, cv2.COLOR_BGR2YUV)
                    
                    # Use TM_SQDIFF_NORMED method (inverted for better comparison)
                    result = cv2.matchTemplate(region_yuv, template_yuv, cv2.TM_SQDIFF_NORMED)
                    result = 1 - result  # Invert so higher values are better matches
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_confidence:
                        best_confidence = max_val
                        best_match = (max_loc[0] + x1, max_loc[1] + y1)
                        best_is_inverted = is_inverted
                
                # If good match found, add to results
                if best_confidence >= 0.6:  # Lower threshold since we're using normalized images
                    screen_x = monitor["left"] + best_match[0] + scaled_target.shape[1]//2
                    screen_y = monitor["top"] + best_match[1] + scaled_target.shape[0]//2
                    
                    found_targets.append({
                        "x": screen_x,
                        "y": screen_y,
                        "confidence": float(best_confidence),
                        "monitor": monitor_index,
                        "is_inverted": best_is_inverted,
                        "calibrated_x": coord["x"],
                        "calibrated_y": coord["y"]
                    })
                    
                    logger.info(f"Found target on monitor {monitor_index} at ({screen_x}, {screen_y}) "
                              f"with confidence {best_confidence:.3f} "
                              f"{'(inverted) ' if best_is_inverted else ''}"
                              f"near calibrated point ({coord['x']}, {coord['y']})")
                    
                    # Draw match on debug image
                    if debug:
                        cv2.circle(debug_img, best_match, 10, (0, 0, 255), 2)
                        cv2.putText(debug_img, 
                                  f"{best_confidence:.2f}{'i' if best_is_inverted else ''}",
                                  (best_match[0], best_match[1]-15),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                else:
                    logger.warning(f"No good match found near calibrated point ({coord['x']}, {coord['y']})")
            
            # Save debug image
            if debug:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                cv2.imwrite(str(debug_dir / f'monitor{monitor_index}_{timestamp}.png'), debug_img)
        
        # Sort by confidence
        found_targets.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Log summary
        if found_targets:
            logger.info(f"\nFound {len(found_targets)} targets:")
            for t in found_targets:
                logger.info(f"- Monitor {t['monitor']}: ({t['x']}, {t['y']}) "
                          f"with confidence {t['confidence']:.3f} "
                          f"{'(inverted) ' if t['is_inverted'] else ''}"
                          f"near ({t['calibrated_x']}, {t['calibrated_y']})")
        else:
            logger.warning("No targets found")
        
        return found_targets

if __name__ == "__main__":
    try:
        targets = find_targets(debug=True)
        if len(targets) >= 2:
            logger.info("\nSuccess! Found at least 2 targets")
        else:
            logger.error(f"\nFailed: Only found {len(targets)} target(s)")
    except Exception as e:
        logger.error(f"Error: {str(e)}") 