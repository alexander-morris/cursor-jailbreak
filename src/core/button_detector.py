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
        
    def preprocess_with_edges(self, image):
        """Apply edge detection preprocessing."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Apply Canny edge detection with optimized parameters
        edges = cv2.Canny(gray, 30, 120, L2gradient=True)
        
        # Dilate edges for better connectivity
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        return edges
        
    def calculate_edge_overlap(self, region_edges, template_edges):
        """Calculate edge overlap ratio between region and template."""
        if region_edges.shape != template_edges.shape:
            return 0.0
            
        intersection = np.sum(region_edges & template_edges)
        template_sum = np.sum(template_edges)
        
        if template_sum == 0:
            return 0.0
            
        return intersection / template_sum
        
    def find_matches(self, monitor, buttons, confidence_threshold=0.75, test_image=None):
        """Find matches for calibrated buttons in the given monitor."""
        logger.info("Finding matches for calibrated buttons...")
        matches = []
        
        # Get screen image
        if test_image is not None:
            screen_bgr = test_image
        else:
            with mss.mss() as sct:
                screen = sct.grab(monitor)
                screen_bgr = np.array(screen)
                if len(screen_bgr.shape) == 3 and screen_bgr.shape[2] == 4:
                    screen_bgr = cv2.cvtColor(screen_bgr, cv2.COLOR_BGRA2BGR)
        
        # Validate screen capture
        if screen_bgr is None or screen_bgr.size == 0:
            logger.error("Failed to capture screen or empty screen image")
            return matches
            
        screen_h, screen_w = screen_bgr.shape[:2]
        logger.info(f"Screen dimensions: {screen_w}x{screen_h}")
        
        for button in buttons:
            # Get template from button data
            template = button["template"]
            if template is None:
                logger.error(f"No template found for button {button['index']}")
                continue
                
            # Get template dimensions
            template_h, template_w = template.shape[:2]
            
            # Get calibration point
            cal_x = button["x"]
            cal_y = button["y"]
            
            logger.info(f"Processing button {button['index']} at ({cal_x}, {cal_y})")
            
            # Validate calibration point
            if cal_x < 0 or cal_x >= screen_w or cal_y < 0 or cal_y >= screen_h:
                logger.error(f"Calibration point ({cal_x}, {cal_y}) is outside screen bounds")
                continue
            
            # Define search region with gold standard margins
            vertical_margin = 100  # Gold standard: 100px
            horizontal_margin = 50  # Gold standard: 50px
            
            search_top = max(0, cal_y - vertical_margin)
            search_bottom = min(screen_h, cal_y + vertical_margin)
            search_left = max(0, cal_x - horizontal_margin)
            search_right = min(screen_w, cal_x + horizontal_margin)
            
            # Validate search region
            if search_right <= search_left or search_bottom <= search_top:
                logger.error(f"Invalid search region: [{search_left}:{search_right}, {search_top}:{search_bottom}]")
                continue
                
            # Extract search region
            try:
                img_bgr = screen_bgr[search_top:search_bottom, search_left:search_right]
                if img_bgr is None or img_bgr.size == 0:
                    logger.error("Failed to extract search region or empty region")
                    continue
                    
                logger.info(f"Search region dimensions: {img_bgr.shape[1]}x{img_bgr.shape[0]}")
                
                # Get edge images for first pass
                img_edges = self.preprocess_with_edges(img_bgr)
                template_edges = self.preprocess_with_edges(template)
                
                # Try gold standard scales
                scales = [0.995, 1.0, 1.005]  # Gold standard scale range
                best_match = None
                best_quality = 0
                
                for scale in scales:
                    # Scale template
                    if scale != 1.0:
                        scaled_w = int(template_w * scale)
                        scaled_h = int(template_h * scale)
                        scaled_template = cv2.resize(template, (scaled_w, scaled_h),
                                                  interpolation=cv2.INTER_NEAREST)
                        scaled_template_edges = cv2.resize(template_edges, (scaled_w, scaled_h),
                                                        interpolation=cv2.INTER_NEAREST)
                    else:
                        scaled_template = template
                        scaled_template_edges = template_edges
                        scaled_w, scaled_h = template_w, template_h
                        
                    # Skip if scaled template is too large
                    if img_edges.shape[0] < scaled_h or img_edges.shape[1] < scaled_w:
                        logger.warning(f"Scaled template ({scaled_w}x{scaled_h}) too large for search region")
                        continue
                    
                    # First pass: Match edges with lower threshold (gold standard)
                    edge_result = cv2.matchTemplate(img_edges, scaled_template_edges, cv2.TM_CCOEFF_NORMED)
                    edge_matches = np.where(edge_result >= 0.2)  # Gold standard threshold
                    
                    logger.info(f"Found {len(edge_matches[0])} potential matches at scale {scale:.3f}")
                    
                    for pt in zip(*edge_matches[::-1]):
                        # Calculate monitor-relative coordinates
                        match_x = search_left + pt[0] + scaled_w // 2
                        match_y = search_top + pt[1] + scaled_h // 2
                        
                        # Extract match region for verification
                        match_left = match_x - template_w // 2
                        match_top = match_y - template_h // 2
                        match_right = match_left + template_w
                        match_bottom = match_top + template_h
                        
                        # Ensure match region is within bounds
                        if (match_left < 0 or match_right > screen_w or
                            match_top < 0 or match_bottom > screen_h):
                            continue
                        
                        try:
                            match_region = screen_bgr[match_top:match_bottom, match_left:match_right]
                            if match_region is None or match_region.size == 0:
                                continue
                                
                            # Calculate match quality components (gold standard weights)
                            direct_conf = cv2.matchTemplate(match_region, template, cv2.TM_CCORR_NORMED)[0][0]
                            edge_conf = edge_result[pt[1], pt[0]]
                            
                            # Calculate edge overlap
                            match_edges = self.preprocess_with_edges(match_region)
                            edge_overlap = np.sum(match_edges & template_edges) / np.sum(template_edges)
                            
                            # Gold standard weighted scoring
                            match_quality = (direct_conf * 0.65 + edge_overlap * 0.20 + edge_conf * 0.15)
                            
                            if match_quality > best_quality:
                                best_quality = match_quality
                                best_match = {
                                    'x': match_x,
                                    'y': match_y,
                                    'confidence': match_quality,
                                    'scale': scale,
                                    'button_index': button["index"]
                                }
                        except Exception as e:
                            logger.error(f"Error processing match region: {str(e)}")
                            continue
                            
            except Exception as e:
                logger.error(f"Error processing search region: {str(e)}")
                continue
            
            if best_match is not None:
                matches.append(best_match)
                logger.info(f"\nBest match for button {button['index']}:")
                logger.info(f"  Position: ({best_match['x']}, {best_match['y']})")
                logger.info(f"  Scale: {best_match['scale']:.3f}")
                logger.info(f"  Quality: {best_match['confidence']:.3f}")
        
        return matches 