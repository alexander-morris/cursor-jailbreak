import cv2
import numpy as np
import pyautogui
import time
import logging
import os
from image_matcher import ImageMatcher
from datetime import datetime

# Configure PyAutoGUI
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Add small delay between actions

class ClickBot:
    def __init__(self):
        self.matcher = ImageMatcher(threshold=0.85)  # Higher threshold for more precision
        
        # Load target image once at startup
        self.target_path = os.path.join(os.path.dirname(__file__), "images", "target.png")
        if not os.path.exists(self.target_path):
            raise ValueError(f"Target image not found at {self.target_path}")
        
        # Set up logging
        log_dir = os.path.join(os.path.dirname(__file__), "temp", "logs")
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'clickbot.log')),
                logging.StreamHandler()
            ]
        )
        
        # Create temp directory if it doesn't exist
        self.temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Load and preprocess target image once
        self.target_image = cv2.imread(self.target_path)
        if self.target_image is None:
            raise ValueError(f"Failed to load target image: {self.target_path}")
    
    def capture_screen(self):
        """Capture the current screen."""
        try:
            screenshot = pyautogui.screenshot()
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logging.error(f"Error capturing screen: {str(e)}")
            return None
    
    def click_target(self, match):
        """Click at the center of the matched target."""
        try:
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Only move and click if we're not already at the target
            if abs(current_x - match.center_x) > 5 or abs(current_y - match.center_y) > 5:
                # Move to target center and click
                pyautogui.moveTo(match.center_x, match.center_y, duration=0.2)
                pyautogui.click()
                
                logging.info(f"Clicked target at ({match.center_x}, {match.center_y}) with confidence {match.confidence:.2f}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error clicking target: {str(e)}")
            return False
    
    def run(self, check_interval=1.0):
        """Run the clickbot continuously."""
        logging.info("Starting ClickBot...")
        logging.info(f"Using target image: {self.target_path}")
        
        last_click_time = 0
        consecutive_fails = 0
        
        while True:
            try:
                # Add longer delay if we've had multiple failures
                if consecutive_fails > 5:
                    time.sleep(check_interval * 2)
                    consecutive_fails = 0
                
                # Capture screen
                screen = self.capture_screen()
                if screen is None:
                    consecutive_fails += 1
                    time.sleep(check_interval)
                    continue
                
                # Save screen to temp file for matcher
                temp_screen_path = os.path.join(self.temp_dir, "current_screen.png")
                cv2.imwrite(temp_screen_path, screen)
                
                # Find matches
                self.matcher.load_images(temp_screen_path, self.target_path)
                matches = self.matcher.find_matches()
                
                if matches:
                    # Sort matches by quality
                    matches.sort(key=lambda m: (
                        m.quality.structural_similarity * 0.4 +
                        m.confidence * 0.3 +
                        m.quality.edge_similarity * 0.2 +
                        m.quality.histogram_similarity * 0.1
                    ), reverse=True)
                    
                    # Get best match
                    best_match = matches[0]
                    
                    # Only click if we're very confident and enough time has passed since last click
                    current_time = time.time()
                    if (best_match.confidence > 0.9 and 
                        best_match.quality.structural_similarity > 0.8 and
                        current_time - last_click_time > 2.0):
                        if self.click_target(best_match):
                            last_click_time = current_time
                            consecutive_fails = 0
                            time.sleep(1.0)  # Short delay after successful click
                            continue
                
                # Wait before next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info("ClickBot stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                consecutive_fails += 1
                time.sleep(check_interval)
        
        # Cleanup
        try:
            os.remove(os.path.join(self.temp_dir, "current_screen.png"))
        except:
            pass

if __name__ == "__main__":
    bot = ClickBot()
    bot.run() 