#!/usr/bin/env python3
import cv2
import numpy as np
import mss
import logging
import pytesseract
from pathlib import Path
import json
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
        self.load_calibration()
    
    def load_calibration(self):
        """Load calibration data from file"""
        calibration_file = Path('calibration.json')
        if not calibration_file.exists():
            raise ValueError("No calibration data found. Please run calibrate_targets.py first.")
        
        with calibration_file.open('r') as f:
            self.calibration_data = json.load(f)
        logger.info(f"Loaded {len(self.calibration_data)} calibration points")
    
    def check_region(self, region, expected_features):
        """Check if a region matches the expected features"""
        # Capture region
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        
        # Convert to grayscale for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        # Threshold to isolate text
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # OCR to get text
        text = pytesseract.image_to_string(thresh).strip()
        
        # Get color features
        hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        
        # Calculate average HSV values in center region
        center_region = hsv[img.shape[0]//4:3*img.shape[0]//4, 
                          img.shape[1]//4:3*img.shape[1]//4]
        avg_hsv = np.mean(center_region, axis=(0,1))
        
        # Compare features
        hsv_diff = np.abs(np.array(expected_features["hsv"]) - avg_hsv)
        hsv_match = np.all(hsv_diff < [10, 50, 50])  # Tolerances for H, S, V
        
        # Save debug image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_path = self.debug_dir / f'check_{timestamp}.png'
        cv2.imwrite(str(debug_path), img)
        
        logger.debug(f"Region check:")
        logger.debug(f"- Expected text: {expected_features['text']}")
        logger.debug(f"- Found text: {text}")
        logger.debug(f"- HSV match: {hsv_match}")
        
        # Return match score (0-1)
        score = 0
        if hsv_match:
            score += 0.5
        if text and expected_features["text"] and text.lower() in expected_features["text"].lower():
            score += 0.5
        
        return score
    
    def find_targets(self):
        """Find all calibrated targets"""
        found_targets = []
        
        # Check each calibration point
        for cal in self.calibration_data:
            region = cal["region"]
            score = self.check_region(region, cal["features"])
            
            if score > 0.5:  # Require at least HSV match or text match
                found_targets.append({
                    "x": cal["x"],
                    "y": cal["y"],
                    "score": score
                })
                logger.info(f"Found target at ({cal['x']}, {cal['y']}) with score {score:.2f}")
            else:
                logger.warning(f"Target not found at ({cal['x']}, {cal['y']})")
        
        return found_targets

if __name__ == "__main__":
    finder = TargetFinder()
    targets = finder.find_targets()
    
    if len(targets) == len(finder.calibration_data):
        logger.info("Success! Found all calibrated targets:")
        for t in targets:
            logger.info(f"- Target at ({t['x']}, {t['y']}) with score {t['score']:.2f}")
    else:
        logger.error(f"Only found {len(targets)}/{len(finder.calibration_data)} targets") 