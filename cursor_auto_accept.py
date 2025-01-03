import pyautogui
import time
import logging
import sys
import argparse
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta
import mss
import numpy as np
import cv2
from PIL import Image

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

    def get_monitors(self):
        """Get list of all monitors"""
        return self.sct.monitors[1:]  # Skip the "all monitors" monitor

    def _ensure_monitor_calibration(self, monitor_index):
        """Ensure calibration file exists for a monitor"""
        monitor_assets = self.assets_dir / f"monitor_{monitor_index}"
        monitor_assets.mkdir(exist_ok=True)
        return monitor_assets / 'accept_button.png'

    def capture_accept_button(self, specific_monitor=None):
        """Capture the accept button image for one or all monitors"""
        if specific_monitor is not None:
            monitors_to_calibrate = [specific_monitor]
        else:
            monitors_to_calibrate = range(len(self.monitors))

        for monitor_index in monitors_to_calibrate:
            print(f"\n=== Cursor Auto Accept Calibration for Monitor {monitor_index} ===")
            print(f"Monitor at position: ({self.monitors[monitor_index]['left']}, {self.monitors[monitor_index]['top']})")
            print("1. Move Cursor to this monitor")
            print("2. Trigger an AI prompt")
            print("3. Move your mouse over the accept button")
            print("4. Keep it there for 5 seconds")
            print("5. Don't move until capture is complete")
            print("\nStarting capture in 5 seconds...")
            time.sleep(5)
            
            # Capture region around mouse
            x, y = pyautogui.position()
            region = {"top": y-20, "left": x-50, "width": 100, "height": 40}
            screenshot = self.sct.grab(region)
            
            # Convert to PIL Image and save
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            calibration_file = self._ensure_monitor_calibration(monitor_index)
            img.save(calibration_file)
            print(f"\nCalibration complete for monitor {monitor_index}!")
            print(f"Saved accept button image to {calibration_file}")
            
            if specific_monitor is None:
                input("\nPress Enter to continue to next monitor, or Ctrl+C to stop...")

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

def main():
    parser = argparse.ArgumentParser(description='Cursor Auto Accept Bot')
    parser.add_argument('--capture', action='store_true', help='Force recalibration by capturing new accept button images')
    parser.add_argument('--monitor', type=int, help='Calibrate a specific monitor (0-based index)')
    args = parser.parse_args()

    bot = CursorAutoAccept()
    
    if args.capture:
        bot.capture_accept_button(args.monitor)
        return

    bot.run()

if __name__ == "__main__":
    main() 