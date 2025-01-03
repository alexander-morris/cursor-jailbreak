import cv2
import numpy as np
import pyautogui
import time
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import mss
from error_recovery import ErrorRecoveryHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_bot.log'),
        logging.StreamHandler()
    ]
)

class CursorAutoAccept:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sct = mss.mss()
        
        # Rate limiting: max 8 clicks per minute
        self.click_history = deque(maxlen=8)
        self.MAX_CLICKS_PER_MINUTE = 8
        
        # Ensure assets directory exists
        self.assets_dir = Path('assets')
        self.assets_dir.mkdir(exist_ok=True)
        
        # Initialize monitor info
        self.monitors = self.get_monitors()
        self.logger.info(f"Found {len(self.monitors)} monitors")
        for i, m in enumerate(self.monitors):
            self.logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
            # Create monitor-specific calibration image path
            self._ensure_monitor_calibration(i)
        
        # Initialize error recovery handler
        self.error_handler = ErrorRecoveryHandler()

    def get_monitors(self):
        """Get list of all monitors"""
        return self.sct.monitors[1:]  # Skip the "all monitors" monitor

    def _ensure_monitor_calibration(self, monitor_index):
        """Ensure calibration file exists for a monitor"""
        monitor_assets = self.assets_dir / f"monitor_{monitor_index}"
        monitor_assets.mkdir(exist_ok=True)
        return monitor_assets / 'accept_button.png'

    def capture_accept_button(self):
        """Capture accept button image for each monitor"""
        print("\nCalibration Process:")
        print("1. Position your cursor over an accept button")
        print("2. Press Enter to capture the button image")
        print("3. Repeat for each monitor\n")
        
        for i, monitor in enumerate(self.monitors):
            print(f"\nCalibrating monitor {i}...")
            input("Position cursor over accept button and press Enter...")
            
            # Get cursor position
            x, y = pyautogui.position()
            
            # Calculate monitor-relative coordinates
            rel_x = x - monitor["left"]
            rel_y = y - monitor["top"]
            
            # Define capture region around cursor
            region = {
                "left": monitor["left"] + max(0, rel_x - 50),
                "top": monitor["top"] + max(0, rel_y - 25),
                "width": 100,
                "height": 50
            }
            
            # Capture region
            screenshot = self.sct.grab(region)
            
            # Save calibration image
            calibration_file = self._ensure_monitor_calibration(i)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(calibration_file))
            
            print(f"Saved calibration image for monitor {i}")
        
        print("\nCalibration complete!")

    def can_click(self):
        """Check if we haven't exceeded rate limit"""
        now = datetime.now()
        # Remove clicks older than 1 minute
        while self.click_history and (now - self.click_history[0]) > timedelta(minutes=1):
            self.click_history.popleft()
        
        return len(self.click_history) < self.MAX_CLICKS_PER_MINUTE

    def find_and_click_accept(self):
        if not self.can_click():
            self.logger.info("Rate limit reached (8 clicks/minute). Waiting...")
            return False
            
        try:
            # Store current mouse position
            original_x, original_y = pyautogui.position()
            
            # Check each monitor with its specific calibration
            for monitor_index, monitor in enumerate(self.monitors):
                calibration_file = self._ensure_monitor_calibration(monitor_index)
                if not calibration_file.exists():
                    self.logger.warning(f"No calibration for monitor {monitor_index}")
                    continue

                try:
                    # Load the template image for this monitor
                    template = cv2.imread(str(calibration_file))
                    if template is None:
                        self.logger.error(f"Failed to load template for monitor {monitor_index}")
                        continue
                    
                    # Capture monitor
                    screenshot = self.sct.grab(monitor)
                    # Convert to CV2 format
                    img = np.array(screenshot)
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Template matching
                    result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val >= 0.8:  # Confidence threshold
                        # Calculate absolute screen coordinates
                        screen_x = monitor["left"] + max_loc[0] + template.shape[1]//2
                        screen_y = monitor["top"] + max_loc[1] + template.shape[0]//2
                        
                        # Click and restore cursor
                        pyautogui.click(screen_x, screen_y)
                        self.click_history.append(datetime.now())
                        self.logger.info(f"Clicked accept button at ({screen_x}, {screen_y}) on monitor {monitor_index}")
                        pyautogui.moveTo(original_x, original_y)
                        return True

                except Exception as e:
                    self.logger.error(f"Error processing monitor {monitor_index}: {str(e)}")
                    continue
            
            # Check for note icon and handle it
            for monitor in self.monitors:
                screenshot = self.sct.grab(monitor)
                img = np.array(screenshot)
                if self.error_handler.handle_error_case(img):
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return False

    def run(self):
        # Check if we need to calibrate any monitor
        need_calibration = False
        for i in range(len(self.monitors)):
            if not self._ensure_monitor_calibration(i).exists():
                need_calibration = True
                break

        if need_calibration:
            print("\nSome monitors need calibration. Starting calibration process...")
            self.capture_accept_button()
        
        self.logger.info("Starting Cursor Auto Accept Bot")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info(f"Rate limit: {self.MAX_CLICKS_PER_MINUTE} clicks per minute")
        
        last_not_found_log = 0  # To prevent spamming logs
        
        try:
            while True:
                if self.find_and_click_accept():
                    time.sleep(0.5)  # Short delay after successful click
                else:
                    # Only log "Accept button not found" once every 5 seconds
                    current_time = time.time()
                    if current_time - last_not_found_log >= 5:
                        self.logger.info("Still searching for accept button...")
                        last_not_found_log = current_time
                    time.sleep(0.2)  # Check frequently
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true", help="Run calibration process")
    args = parser.parse_args()
    
    bot = CursorAutoAccept()
    if args.capture:
        bot.capture_accept_button()
    else:
        bot.run() 