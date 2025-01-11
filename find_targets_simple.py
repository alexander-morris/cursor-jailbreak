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

class TargetFinder:
    def __init__(self):
        self.sct = mss.mss()
        self.monitors = self.sct.monitors[1:]  # Skip the "all monitors" monitor
        self.debug_dir = Path('temp/debug')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Load target image
        target_path = Path('images/target.png')
        if not target_path.exists():
            raise ValueError("target.png not found in images directory")
        self.target = cv2.imread(str(target_path))
        if self.target is None:
            raise ValueError("Failed to load target.png")
        
        logger.info(f"Target image size: {self.target.shape}")
        
    def find_targets(self, debug=True):
        """Find target buttons across all monitors"""
        found_targets = []
        
        # Search each monitor
        for monitor_index, monitor in enumerate(self.monitors):
            # Capture right half of screen
            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Create debug image
            if debug:
                debug_img = img_bgr.copy()
            
            h, w = img_bgr.shape[:2]
            right_half_start = w // 2
            right_half = img_bgr[:, right_half_start:]
            
            # Draw search region on debug image
            if debug:
                cv2.line(debug_img, (right_half_start, 0), (right_half_start, h), (0, 255, 0), 2)
                cv2.putText(debug_img, "Search Region", (right_half_start + 10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Find matches
            result = cv2.matchTemplate(right_half, self.target, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            logger.info(f"Monitor {monitor_index} - Max confidence: {max_val:.3f}")
            
            # Use two thresholds for better reliability
            initial_threshold = 0.6  # Lower threshold to catch potential matches
            confirm_threshold = 0.75  # Higher threshold for confirmation
            
            locations = np.where(result >= initial_threshold)
            matches_found = len(locations[0])
            logger.info(f"Monitor {monitor_index} - Found {matches_found} potential matches")
            
            # Draw heatmap on debug image
            if debug:
                result_norm = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                result_color = cv2.applyColorMap(result_norm, cv2.COLORMAP_JET)
                result_resized = cv2.resize(result_color, (w//2, h))
                alpha = 0.3
                debug_img[:, right_half_start:] = cv2.addWeighted(
                    debug_img[:, right_half_start:], 1-alpha,
                    result_resized, alpha, 0
                )
            
            # Group matches that are close together
            grouped_matches = []
            for pt in zip(*locations[::-1]):
                x = pt[0] + right_half_start + self.target.shape[1]//2
                y = pt[1] + self.target.shape[0]//2
                confidence = result[pt[1], pt[0]]
                
                # Check if this match is close to any existing matches
                is_duplicate = False
                for existing in grouped_matches:
                    if abs(x - existing["x"]) < 10 and abs(y - existing["y"]) < 10:
                        if confidence > existing["confidence"]:
                            existing.update({"x": x, "y": y, "confidence": confidence})
                        is_duplicate = True
                        break
                
                if not is_duplicate and confidence >= confirm_threshold:
                    grouped_matches.append({
                        "x": x + monitor["left"],
                        "y": y + monitor["top"],
                        "confidence": confidence,
                        "monitor": monitor_index
                    })
                    
                    # Draw match on debug image
                    if debug:
                        cv2.circle(debug_img, (x, y), 10, (0, 0, 255), 2)
                        cv2.putText(debug_img, f"{confidence:.2f}", (x, y - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            found_targets.extend(grouped_matches)
            
            # Save debug image
            if debug:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                cv2.imwrite(str(self.debug_dir / f'monitor{monitor_index}_{timestamp}.png'), debug_img)
        
        # Sort by confidence
        found_targets.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Log results
        if found_targets:
            logger.info(f"Found {len(found_targets)} targets:")
            for t in found_targets:
                logger.info(f"- Monitor {t['monitor']}: ({t['x']}, {t['y']}) with confidence {t['confidence']:.2f}")
        else:
            logger.warning("No targets found")
        
        return found_targets

if __name__ == "__main__":
    finder = TargetFinder()
    targets = finder.find_targets()
    
    if len(targets) >= 2:
        logger.info("Success! Found at least 2 targets")
    else:
        logger.error(f"Only found {len(targets)} target(s)") 