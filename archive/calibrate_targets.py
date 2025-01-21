#!/usr/bin/env python3
import cv2
import numpy as np
import mss
import logging
import pyautogui
import pytesseract
from pathlib import Path
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TargetCalibrator:
    def __init__(self):
        self.sct = mss.mss()
        self.monitors = self.sct.monitors[1:]  # Skip the "all monitors" monitor
        self.calibration_data = []
        self.debug_dir = Path('temp/debug')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def wait_for_click(self):
        """Wait for user to click and return the coordinates"""
        logger.info("Please click on a target button...")
        x, y = pyautogui.position()
        while True:
            new_x, new_y = pyautogui.position()
            if (x, y) != (new_x, new_y):
                x, y = new_x, new_y
            if pyautogui.mouseDown():
                time.sleep(0.1)  # Wait for click to complete
                return x, y
    
    def capture_region(self, x, y, size=100):
        """Capture a region around the clicked coordinates"""
        # Find which monitor contains these coordinates
        for monitor in self.monitors:
            if (monitor["left"] <= x <= monitor["left"] + monitor["width"] and
                monitor["top"] <= y <= monitor["top"] + monitor["height"]):
                # Calculate region bounds
                left = max(x - size//2, monitor["left"])
                top = max(y - size//2, monitor["top"])
                width = min(size, monitor["left"] + monitor["width"] - left)
                height = min(size, monitor["top"] + monitor["height"] - top)
                
                region = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
                
                screenshot = self.sct.grab(region)
                return np.array(screenshot), region
        return None, None
    
    def process_region(self, img):
        """Process the captured region to extract text and features"""
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
        
        return {
            "text": text,
            "hsv": avg_hsv.tolist(),
            "timestamp": datetime.now().isoformat()
        }
    
    def calibrate(self):
        """Run the calibration process"""
        logger.info("Starting calibration process...")
        logger.info("Found %d monitors:", len(self.monitors))
        for i, m in enumerate(self.monitors):
            logger.info("Monitor %d: %dx%d at (%d, %d)", 
                       i, m["width"], m["height"], m["left"], m["top"])
        
        logger.info("\nCalibration Instructions:")
        logger.info("1. Click on each target button")
        logger.info("2. Press 'q' when done")
        logger.info("3. The script will save the calibration data\n")
        
        while True:
            # Wait for click
            x, y = self.wait_for_click()
            logger.info(f"Click detected at ({x}, {y})")
            
            # Capture and process region
            img, region = self.capture_region(x, y)
            if img is None:
                logger.warning("Click was outside all monitors")
                continue
            
            # Save debug image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            cv2.imwrite(str(self.debug_dir / f'calibration_{timestamp}.png'), img)
            
            # Process region
            features = self.process_region(img)
            
            # Add calibration data
            self.calibration_data.append({
                "x": x,
                "y": y,
                "region": region,
                "features": features
            })
            
            logger.info(f"Captured target {len(self.calibration_data)}:")
            logger.info(f"- Position: ({x}, {y})")
            logger.info(f"- Text found: {features['text']}")
            logger.info(f"- HSV values: {features['hsv']}\n")
            
            # Check if done
            if len(self.calibration_data) >= 2:
                response = input("Press Enter to add another target, or 'q' to finish: ")
                if response.lower() == 'q':
                    break
        
        # Save calibration data
        self.save_calibration()
        logger.info("Calibration complete!")
    
    def save_calibration(self):
        """Save calibration data to file"""
        calibration_file = Path('calibration.json')
        with calibration_file.open('w') as f:
            json.dump(self.calibration_data, f, indent=2)
        logger.info(f"Saved calibration data to {calibration_file}")

if __name__ == "__main__":
    calibrator = TargetCalibrator()
    calibrator.calibrate() 