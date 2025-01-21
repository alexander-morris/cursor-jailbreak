import numpy as np
import pyautogui
import time
import mss
import json
import cv2
import os
from datetime import datetime

class SimpleButtonDetector:
    def __init__(self):
        self.sct = mss.mss()
        # Button is 5x wider than tall
        self.button_width = 100  # pixels
        self.button_height = 20  # pixels
        self.search_range = 300  # pixels to search above/below
        self.calibration_data = None
        self.debug_dir = "debug_captures"
        os.makedirs(self.debug_dir, exist_ok=True)
        self.button_threshold = 40.0  # Maximum difference to be considered a button
        self.consecutive_matches_needed = 3  # Number of consecutive matches needed to confirm button
    
    def save_debug_image(self, img, prefix, y_offset):
        """Save a debug image with timestamp and position info"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{self.debug_dir}/{prefix}_y{y_offset}_{timestamp}.png"
        # Convert from BGRA to BGR
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        cv2.imwrite(filename, img)
        print(f"Saved debug image: {filename}")
    
    def capture_region(self, x, y, width, height):
        """Capture a region of the screen"""
        region = {
            'left': x - width // 2,
            'top': y - height // 2,
            'width': width,
            'height': height
        }
        screenshot = np.array(self.sct.grab(region))
        # Ensure consistent dimensions
        if screenshot.shape[:2] != (height, width):
            screenshot = cv2.resize(screenshot, (width, height))
        return screenshot
    
    def calibrate(self):
        """Calibrate by capturing button and background states"""
        print("\n=== Button Calibration ===")
        print("1. Move cursor to the CENTER of the button...")
        input("Press Enter when ready...")
        
        # Get cursor position
        x, y = pyautogui.position()
        print(f"Center position: ({x}, {y})")
        
        # Capture button state
        button_img = self.capture_region(x, y, self.button_width, self.button_height)
        self.save_debug_image(button_img, "calibration_button", 0)
        
        print("\n2. Wait for the button to disappear...")
        input("Press Enter when the button is gone...")
        
        # Capture background state
        background = self.capture_region(x, y, self.button_width, self.button_height)
        self.save_debug_image(background, "calibration_background", 0)
        
        # Calculate difference metrics
        diff = np.abs(button_img.astype(float) - background.astype(float))
        mean_diff = np.mean(diff)
        
        print(f"\nMean difference between states: {mean_diff:.2f}")
        
        # Save calibration data
        self.calibration_data = {
            'x': x,
            'y': y,
            'button_state': button_img.tolist(),
            'background_state': background.tolist(),
            'mean_diff': float(mean_diff)
        }
        return True
    
    def check_for_button(self, x, y):
        """Check if button-like object exists at coordinates"""
        current = self.capture_region(x, y, self.button_width, self.button_height)
        button_ref = np.array(self.calibration_data['button_state'])
        background_ref = np.array(self.calibration_data['background_state'])
        
        # Ensure all arrays have the same shape
        if current.shape != button_ref.shape:
            button_ref = cv2.resize(button_ref, (current.shape[1], current.shape[0]))
        if current.shape != background_ref.shape:
            background_ref = cv2.resize(background_ref, (current.shape[1], current.shape[0]))
        
        # Calculate similarities
        diff_to_button = np.mean(np.abs(current - button_ref))
        diff_to_background = np.mean(np.abs(current - background_ref))
        
        print(f"Similarity scores - Button: {diff_to_button:.3f}, Background: {diff_to_background:.3f}")
        
        # Save debug image if potential match
        if diff_to_button < self.button_threshold:
            y_offset = y - self.calibration_data['y']
            self.save_debug_image(current, "potential_match", y_offset)
            return True, diff_to_button
        
        return False, diff_to_button
    
    def verify_click(self, x, y):
        """Verify if clicking caused a state change"""
        before = self.capture_region(x, y, self.button_width, self.button_height)
        y_offset = y - self.calibration_data['y']
        self.save_debug_image(before, "before_click", y_offset)
        
        # Click
        original_x, original_y = pyautogui.position()
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.click()
        pyautogui.moveTo(original_x, original_y, duration=0.1)
        
        # Wait for state change
        time.sleep(0.2)
        
        # Check if state changed
        after = self.capture_region(x, y, self.button_width, self.button_height)
        self.save_debug_image(after, "after_click", y_offset)
        
        diff = np.mean(np.abs(after - before))
        
        print(f"State change after click: {diff:.2f}")
        return diff > 20  # Significant change threshold
    
    def run(self):
        """Main detection loop"""
        if not self.calibration_data:
            if not self.calibrate():
                return
        
        print("\nStarting button detection...")
        print("Press Ctrl+C to stop")
        
        base_x = self.calibration_data['x']
        base_y = self.calibration_data['y']
        last_click_time = 0
        min_click_interval = 0.5  # Reduced from 1.0
        consecutive_matches = 0
        last_match_y = None
        
        while True:
            try:
                current_time = time.time()
                if current_time - last_click_time >= min_click_interval:
                    # Check positions above and below
                    for y_offset in range(-self.search_range, self.search_range + 1, 20):
                        check_y = base_y + y_offset
                        is_button, similarity = self.check_for_button(base_x, check_y)
                        
                        if is_button:
                            print(f"\nPotential button at y={check_y} (offset={y_offset})")
                            
                            # Check if this is a consecutive match at the same position
                            if last_match_y == check_y:
                                consecutive_matches += 1
                            else:
                                consecutive_matches = 1
                                last_match_y = check_y
                            
                            if consecutive_matches >= self.consecutive_matches_needed:
                                if self.verify_click(base_x, check_y):
                                    print("Click verified - state changed!")
                                    last_click_time = current_time
                                    consecutive_matches = 0
                                    last_match_y = None
                                    break
                                else:
                                    print("Click verification failed")
                                    consecutive_matches = 0
                                    last_match_y = None
                        else:
                            if last_match_y == check_y:
                                consecutive_matches = 0
                                last_match_y = None
                
                print(".", end="", flush=True)
                time.sleep(0.02)  # Reduced from 0.1
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                break
        
        self.sct.close()

if __name__ == "__main__":
    detector = SimpleButtonDetector()
    detector.run() 