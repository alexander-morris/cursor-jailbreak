import numpy as np
import pyautogui
import time
import logging
import mss
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TargetClicker:
    def __init__(self):
        self.sct = mss.mss()
        self.calibration_file = Path('target_calibration.json')
        self.target_data = None
        self.similarity_threshold = 5  # Maximum average pixel difference allowed
        
    def calibrate(self):
        """Calibrate by capturing target area before and after click"""
        try:
            logger.info("Please hover over the target button (DO NOT CLICK YET)...")
            input("Press Enter when ready...")
            
            # Get cursor position
            x, y = pyautogui.position()
            logger.info(f"Target position: ({x}, {y})")
            
            # Capture small area around cursor (10x10 pixels)
            region = {
                'left': x - 5,
                'top': y - 5,
                'width': 10,
                'height': 10
            }
            
            # Capture before state
            before_click = np.array(self.sct.grab(region))
            before_pixels = before_click.tolist()
            
            logger.info("Now click the target button...")
            input("Press Enter after clicking...")
            
            # Small delay to ensure visual change is complete
            time.sleep(0.5)
            
            # Capture after state
            after_click = np.array(self.sct.grab(region))
            after_pixels = after_click.tolist()
            
            # Save calibration data
            self.target_data = {
                'x': x,
                'y': y,
                'region': region,
                'before_pixels': before_pixels,
                'after_pixels': after_pixels
            }
            
            with self.calibration_file.open('w') as f:
                json.dump(self.target_data, f)
            
            logger.info("Calibration complete! Target data saved.")
            return True
            
        except Exception as e:
            logger.error(f"Error during calibration: {str(e)}")
            return False
    
    def load_calibration(self):
        """Load calibration data"""
        try:
            if not self.calibration_file.exists():
                logger.error("No calibration file found. Please run calibration first.")
                return False
            
            with self.calibration_file.open('r') as f:
                self.target_data = json.load(f)
            
            # Convert lists back to numpy arrays
            self.target_data['before_pixels'] = np.array(self.target_data['before_pixels'])
            self.target_data['after_pixels'] = np.array(self.target_data['after_pixels'])
            
            logger.info(f"Loaded calibration data for target at ({self.target_data['x']}, {self.target_data['y']})")
            return True
            
        except Exception as e:
            logger.error(f"Error loading calibration: {str(e)}")
            return False
    
    def check_and_click(self):
        """Check if target is in before state and click if it is"""
        try:
            # Capture current state
            current = np.array(self.sct.grab(self.target_data['region']))
            
            # Compare with before state (using similarity threshold)
            pixel_diff = np.abs(current - self.target_data['before_pixels'])
            mean_diff = np.mean(pixel_diff)
            
            if mean_diff < self.similarity_threshold:
                logger.info(f"Target detected (diff: {mean_diff:.2f})")
                
                # Store original position
                original_x, original_y = pyautogui.position()
                
                # Move to target and click
                x, y = self.target_data['x'], self.target_data['y']
                logger.info(f"Clicking at ({x}, {y})")
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                
                # Verify click worked
                time.sleep(0.5)  # Wait for visual change
                after = np.array(self.sct.grab(self.target_data['region']))
                
                # Compare with expected after state
                after_diff = np.abs(after - self.target_data['after_pixels'])
                after_mean_diff = np.mean(after_diff)
                
                if after_mean_diff < self.similarity_threshold:
                    logger.info("Click successful - visual state matches expected")
                else:
                    logger.warning(f"Click may have failed - unexpected visual state (diff: {after_mean_diff:.2f})")
                
                # Restore cursor position
                pyautogui.moveTo(original_x, original_y, duration=0.2)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking target: {str(e)}")
            return False
    
    def run(self):
        """Main loop"""
        if not self.load_calibration():
            logger.info("Running calibration...")
            if not self.calibrate():
                return
        
        logger.info("Starting target monitoring")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                self.check_and_click()
                time.sleep(0.1)  # Small delay between checks
                
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except Exception as e:
            logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    clicker = TargetClicker()
    clicker.run() 