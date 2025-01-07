"""
Button detection system for the Cursor Auto Accept application.
"""

import cv2
import numpy as np
import mss
from PIL import Image, ImageDraw
import time
from pathlib import Path
from skimage.metrics import structural_similarity as ssim
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ButtonDetector:
    def __init__(self):
        """Initialize the button detector."""
        self.debug_dir = Path(ClickBotConfig.DEBUG_DIR)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def verify_match(self, img, template, correlation_threshold=0.7):
        """Verify if an image patch matches the template."""
        # Ensure same size and format
        if img.shape != template.shape:
            logger.warning("Size mismatch in verify_match")
            return False, 0.0
            
        # Convert both to BGR if needed
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if len(template.shape) == 2:
            template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
            
        # Calculate verification metrics
        correlation = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED)[0][0]
        mse = np.mean((img.astype("float") - template.astype("float")) ** 2)
        mse_score = 1 - (mse / 255**2)  # Normalize to 0-1 range
        ssim_score = ssim(img, template, channel_axis=2, win_size=3)  # Use small window size for small images
        
        # Calculate final score (weighted average)
        final_score = (correlation * 0.6) + (mse_score * 0.3) + (ssim_score * 0.1)
        
        logger.info("Verification scores:")
        logger.info(f"  Correlation: {correlation:.3f}")
        logger.info(f"  MSE Score: {mse_score:.3f}")
        logger.info(f"  SSIM Score: {ssim_score:.3f}")
        logger.info(f"  Final Score: {final_score:.3f}")
        
        # More lenient thresholds matching original code
        is_match = correlation >= correlation_threshold and mse_score >= 0.95 and final_score >= 0.65
        return is_match, final_score
        
    def find_matches(self, monitor, buttons, confidence_threshold=0.75):
        """Find matches for calibrated buttons in the current screen."""
        logger.info("Finding matches for calibrated buttons...")
        
        # Take a full screenshot of the monitor
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            screen = np.array(screenshot)
            screen_bgr = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
            
        matches = []
        for button in buttons:
            template = button['template']
            template_h, template_w = template.shape[:2]
            
            # Calculate search region around calibration point
            cal_x, cal_y = button['x'], button['y']
            
            # Calculate center offset for template
            center_x = template_w // 2
            center_y = template_h // 2
            
            # Search parameters
            search_margin_x = 40  # pixels to search horizontally
            search_margin_y = 80  # pixels to search vertically
            
            # Define search region around calibration point
            search_region = {
                "left": monitor["left"] + cal_x - search_margin_x - center_x,
                "top": monitor["top"] + cal_y - search_margin_y - center_y,
                "width": (search_margin_x * 2) + template_w,
                "height": (search_margin_y * 2) + template_h,
                "mon": monitor["name"]
            }
            
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
            cv2.imwrite(str(self.debug_dir / f'search_region_{button["index"]}.png'), debug_search)
            
            # Find matches
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCORR_NORMED)
            locations = np.where(result >= confidence_threshold)
            
            logger.info(f"Found {len(locations[0])} potential matches for button {button['index']}")
            
            best_match = None
            best_confidence = 0
            
            for pt in zip(*locations[::-1]):  # Switch columns and rows
                # Calculate monitor-relative coordinates
                match_x = cal_x - search_margin_x + pt[0]
                match_y = cal_y - search_margin_y + pt[1]
                
                # Calculate distance from calibration point
                distance = ((match_x - cal_x) ** 2 + (match_y - cal_y) ** 2) ** 0.5
                confidence = result[pt[1], pt[0]]
                
                logger.info(f"\nFound match:")
                logger.info(f"  Template position in search region: ({pt[0]}, {pt[1]})")
                logger.info(f"  Monitor-relative position: ({match_x}, {match_y})")
                logger.info(f"  Distance from calibration: {distance:.1f}px")
                logger.info(f"  Confidence: {confidence:.3f}")
                
                # Save match region for debugging
                match_region = {
                    "left": monitor["left"] + match_x - center_x,
                    "top": monitor["top"] + match_y - center_y,
                    "width": template_w,
                    "height": template_h,
                    "mon": monitor["name"]
                }
                
                with mss.mss() as sct:
                    match_img = np.array(sct.grab(match_region))
                match_bgr = cv2.cvtColor(match_img, cv2.COLOR_BGRA2BGR)
                cv2.imwrite(str(self.debug_dir / f'match_{button["index"]}_{len(matches)}.png'), match_bgr)
                
                # Verify match with multiple metrics
                is_match, match_confidence = self.verify_match(match_bgr, template, confidence_threshold)
                
                if is_match and match_confidence > best_confidence:
                    best_confidence = match_confidence
                    best_match = {
                        'button_index': button['index'],
                        'x': match_x,
                        'y': match_y,
                        'confidence': match_confidence,
                        'template': template,
                        'distance': distance
                    }
            
            if best_match:
                matches.append(best_match)
                logger.info(f"\nBest match for button {button['index']}:")
                logger.info(f"  Position: ({best_match['x']}, {best_match['y']})")
                logger.info(f"  Distance: {best_match['distance']:.1f}px")
                logger.info(f"  Confidence: {best_match['confidence']:.3f}")
        
        return matches
        
    def create_visualization(self, monitor, matches):
        """Create a visualization of the matches on the screen."""
        logger.info("Creating visualization of matches...")
        
        # Take a full screenshot
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            screen = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
        # Create a drawing context
        draw = ImageDraw.Draw(screen)
        
        # Colors for different buttons
        colors = ['red', 'green', 'blue']
        
        # Draw matches
        for match in matches:
            x, y = match['x'], match['y']
            template = match['template']
            h, w = template.shape[:2]
            confidence = match['confidence']
            button_index = match['button_index']
            color = colors[(button_index - 1) % len(colors)]
            
            # Draw rectangle around match
            draw.rectangle(
                [(x, y), (x + w, y + h)],
                outline=color,
                width=2
            )
            
            # Draw text with button index, confidence, and distances
            text = f"Button {button_index} ({confidence:.2f})"
            text2 = f"H: {match['h_distance']}px V: {match['v_distance']}px"
            draw.text((x, y - 30), text, fill=color)
            draw.text((x, y - 15), text2, fill=color)
            
        # Save visualization
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        vis_path = self.debug_dir / f'matches_{timestamp}.png'
        screen.save(vis_path)
        logger.info(f"Saved visualization to: {vis_path}")
        
        return vis_path 