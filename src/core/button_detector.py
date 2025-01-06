"""
Button detection system for the Cursor Auto Accept application.
"""

import cv2
import numpy as np
import mss
from PIL import Image
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ButtonDetector:
    def __init__(self):
        """Initialize the button detector."""
        self.sct = mss.mss()
        self.monitors = self.sct.monitors[1:]  # Skip the "all" monitor
        
    def find_matches(self, template, monitor, center_x, center_y):
        """Find matches for the template around the given center position."""
        # Calculate search region
        search_region = {
            "left": center_x - ClickBotConfig.SEARCH_MARGIN_X,
            "top": center_y - ClickBotConfig.SEARCH_MARGIN_Y,
            "width": ClickBotConfig.SEARCH_MARGIN_X * 2,
            "height": ClickBotConfig.SEARCH_MARGIN_Y * 2,
            "mon": monitor["name"]
        }
        
        # Capture screen region
        screenshot = self.sct.grab(search_region)
        screen = np.array(Image.frombytes('RGB', screenshot.size, screenshot.rgb))
        
        # Convert to grayscale
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        
        # Perform template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Find matches above threshold
        matches = []
        threshold = ClickBotConfig.MATCH_THRESHOLD
        locations = np.where(result >= threshold)
        
        for pt in zip(*locations[::-1]):
            match = {
                "x": search_region["left"] + pt[0],
                "y": search_region["top"] + pt[1],
                "confidence": result[pt[1], pt[0]]
            }
            matches.append(match)
            
        return matches 