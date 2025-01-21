import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
import cv2

class ButtonDetector:
    def __init__(self):
        self.sct = mss.mss()
        self.button_width = 50  # Will be set during calibration
        self.button_height = 10  # Will be set during calibration
        self.search_range = 300  # Pixels to search above and below
        self.calibration_data = None
        self.last_click_pos = None
        self.successful_matches = []  # Track successful button detections
    
    def capture_region(self, x, y, width, height):
        """Capture a region of the screen"""
        region = {
            'left': x - width // 2,
            'top': y - height // 2,
            'width': width,
            'height': height
        }
        return np.array(self.sct.grab(region))
    
    def calibrate(self):
        """Calibrate by capturing the button state"""
        print("\n=== Button Calibration ===")
        print("1. Move cursor to the CENTER of the button...")
        input("Press Enter when ready...")
        
        # Get cursor position
        x, y = pyautogui.position()
        print(f"Center position: ({x}, {y})")
        
        # Capture initial state with estimated button size
        initial_width = 100  # Start with a wider area
        initial_height = 40  # Start with a taller area
        initial_region = self.capture_region(x, y, initial_width, initial_height)
        
        print("\n2. Wait for the button to disappear...")
        input("Press Enter when the button is gone...")
        
        # Capture background state
        background = self.capture_region(x, y, initial_width, initial_height)
        
        # Calculate difference to find button
        diff = cv2.absdiff(initial_region, background)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
        
        # Find contours to detect button shape
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # Get the largest contour (likely the button)
            button_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(button_contour)
            self.button_width = w
            self.button_height = h
            print(f"\nDetected button size: {w}x{h} pixels")
            
            # Save calibration data
            self.calibration_data = {
                'center_x': x,
                'center_y': y,
                'width': w,
                'height': h,
                'template': initial_region[y:y+h, x:x+w].tolist(),
                'background': background[y:y+h, x:x+w].tolist()
            }
            
            # Save for debugging
            cv2.imwrite('button_template.png', initial_region[y:y+h, x:x+w])
            cv2.imwrite('button_background.png', background[y:y+h, x:x+w])
            
            return True
        else:
            print("Failed to detect button shape. Please try again.")
            return False
    
    def find_button(self, center_x, search_y_start, search_y_end):
        """Search for button in vertical range"""
        if not self.calibration_data:
            print("Please calibrate first!")
            return None
        
        template = np.array(self.calibration_data['template'])
        h, w = template.shape[:2]
        
        # Capture search area
        search_region = {
            'left': center_x - w // 2,
            'top': search_y_start,
            'width': w,
            'height': search_y_end - search_y_start
        }
        search_img = np.array(self.sct.grab(search_region))
        
        # Convert to grayscale
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        search_gray = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(search_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.8:  # Good match threshold
            match_x = center_x
            match_y = search_y_start + max_loc[1] + h//2
            return (match_x, match_y, max_val)
        
        return None
    
    def verify_click(self, x, y):
        """Verify if clicking changed the state"""
        # Capture before click
        before = self.capture_region(x, y, self.button_width, self.button_height)
        
        # Click
        original_x, original_y = pyautogui.position()
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.click()
        pyautogui.moveTo(original_x, original_y, duration=0.1)
        
        # Wait for state change
        time.sleep(0.2)
        
        # Capture after click
        after = self.capture_region(x, y, self.button_width, self.button_height)
        
        # Compare states
        diff = cv2.absdiff(before, after)
        mean_diff = np.mean(diff)
        
        # If significant change, consider it a successful click
        if mean_diff > 30:
            self.successful_matches.append({
                'x': x,
                'y': y,
                'template': before.tolist()
            })
            return True
        
        return False
    
    def run(self):
        """Main detection loop"""
        if not self.calibration_data:
            if not self.calibrate():
                return
        
        print("\nStarting button detection...")
        print("Press Ctrl+C to stop")
        
        center_x = pyautogui.position()[0]  # Use current X position
        last_click_time = 0
        min_click_interval = 0.5
        
        while True:
            try:
                current_time = time.time()
                if current_time - last_click_time >= min_click_interval:
                    # Search in vertical range
                    y_mid = pyautogui.position()[1]  # Current Y position
                    search_start = y_mid - self.search_range
                    search_end = y_mid + self.search_range
                    
                    match = self.find_button(center_x, search_start, search_end)
                    if match:
                        x, y, confidence = match
                        print(f"\nFound potential button at ({x}, {y}) with confidence {confidence:.3f}")
                        
                        if self.verify_click(x, y):
                            print("Click verified - button state changed!")
                            last_click_time = current_time
                        else:
                            print("Click verification failed - no state change detected")
                    
                    print(".", end="", flush=True)
                
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                break
        
        self.sct.close()

if __name__ == "__main__":
    detector = ButtonDetector()
    detector.run() 