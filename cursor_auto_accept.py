import cv2
import numpy as np
import pyautogui
import time
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
import mss

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_bot.log'),
        logging.StreamHandler()
    ]
)

class NoteDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sct = mss.mss()
        
        # Load note images
        self.images_dir = Path('images')
        self.note_icon = cv2.imread(str(self.images_dir / 'note-with-icon.png'))
        self.note_text = cv2.imread(str(self.images_dir / 'note-text.png'))
        
        if self.note_icon is None or self.note_text is None:
            raise ValueError("Failed to load note images")
        
        # Initialize monitor info
        self.monitors = self.get_monitors()
        self.logger.info(f"Found {len(self.monitors)} monitors")
        for i, m in enumerate(self.monitors):
            self.logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        
        # Add cooldown tracking
        self.last_action_time = None
        self.action_cooldown = 2.0  # seconds between actions

    def get_monitors(self):
        """Get list of all monitors"""
        return self.sct.monitors[1:]  # Skip the "all monitors" monitor

    def type_in_prompt(self, message, x_position):
        """Type a message into the prompt field and submit it
        Args:
            message: The text to type
            x_position: The x coordinate to align with (prompt will be 5px to the right)
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate prompt position:
            # - Black banner is 20px tall at bottom
            # - Prompt field is 30-70px above the banner
            monitor = self.monitors[2]  # Using monitor 2 where note was found
            screen_bottom = monitor["top"] + monitor["height"]
            prompt_y = screen_bottom - (20 + np.random.randint(35, 45))  # 35-45px above bottom banner
            prompt_x = x_position + 5 + np.random.randint(-2, 3)

            # Move to and click prompt field
            self.logger.info(f"Moving to prompt at ({prompt_x}, {prompt_y})")
            pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
            
            # Capture before-click image (larger area)
            before_click = self.sct.grab({"top": prompt_y - 20, "left": prompt_x - 20, 
                                        "width": 100, "height": 60})
            before_click = np.array(before_click)
            
            # Click and wait slightly longer
            pyautogui.click()
            time.sleep(0.5)
            
            # Capture after-click image
            after_click = self.sct.grab({"top": prompt_y - 20, "left": prompt_x - 20, 
                                       "width": 100, "height": 60})
            after_click = np.array(after_click)
            
            # Compare images with lower threshold
            diff = cv2.absdiff(before_click, after_click)
            changed = np.mean(diff) > 2  # Lower threshold for change detection
            
            if not changed:
                self.logger.warning("Click may not have registered - no visual change detected")
                # Try clicking again with different position in prompt field
                prompt_y = screen_bottom - (20 + np.random.randint(35, 45))  # New random position
                prompt_x += np.random.randint(-5, 6)
                pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
                pyautogui.click()
                time.sleep(0.5)
                
                # Check again
                after_retry = self.sct.grab({"top": prompt_y - 20, "left": prompt_x - 20, 
                                           "width": 100, "height": 60})
                after_retry = np.array(after_retry)
                diff = cv2.absdiff(before_click, after_retry)
                changed = np.mean(diff) > 2
                
                if not changed:
                    return False
                
            self.logger.info("Click successful - visual change detected")

            # Type the message
            self.logger.info(f"Typing message: '{message}'")
            pyautogui.write(message)
            time.sleep(0.2)

            # Press Command + Enter
            self.logger.info("Submitting prompt")
            pyautogui.hotkey('command', 'return')
            return True

        except Exception as e:
            self.logger.error(f"Error typing in prompt: {str(e)}")
            return False

    def handle_note_prompt(self, note_coords):
        """Handle clicking prompt and typing continue"""
        try:
            # Check cooldown
            if self.last_action_time and time.time() - self.last_action_time < self.action_cooldown:
                return False

            x, y = note_coords
            success = self.type_in_prompt("continue", x)
            
            if success:
                self.last_action_time = time.time()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error handling prompt: {str(e)}")
            return False

    def find_note(self):
        """Find note icon or text on any monitor"""
        try:
            # Check each monitor
            for monitor_index, monitor in enumerate(self.monitors):
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                # Convert to CV2 format
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Try matching note icon
                result = cv2.matchTemplate(img_bgr, self.note_icon, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.8:  # Confidence threshold
                    # Calculate absolute screen coordinates
                    screen_x = monitor["left"] + max_loc[0] + self.note_icon.shape[1]//2
                    screen_y = monitor["top"] + max_loc[1] + self.note_icon.shape[0]//2
                    self.logger.info(f"Found note icon at ({screen_x}, {screen_y}) on monitor {monitor_index}")
                    return True, (screen_x, screen_y)
                
                # Try matching note text
                result = cv2.matchTemplate(img_bgr, self.note_text, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.8:  # Confidence threshold
                    # Calculate absolute screen coordinates
                    screen_x = monitor["left"] + max_loc[0] + self.note_text.shape[1]//2
                    screen_y = monitor["top"] + max_loc[1] + self.note_text.shape[0]//2
                    self.logger.info(f"Found note text at ({screen_x}, {screen_y}) on monitor {monitor_index}")
                    return True, (screen_x, screen_y)
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error finding note: {str(e)}")
            return False, None

    def run(self):
        """Run continuous note detection"""
        self.logger.info("Starting Note Detection")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                found, coords = self.find_note()
                if found:
                    print(f"Found note at coordinates: {coords}")
                    if self.handle_note_prompt(coords):
                        self.logger.info("Successfully handled note prompt")
                    else:
                        self.logger.info("Skipped prompt handling (cooldown)")
                time.sleep(0.2)  # Short delay between checks
                
        except KeyboardInterrupt:
            self.logger.info("Detection stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

if __name__ == "__main__":
    detector = NoteDetector()
    detector.run() 