import numpy as np
import pyautogui
import time
import mss
import json

class SimpleButtonDetector:
    def __init__(self):
        self.sct = mss.mss()
        # Button is 5x wider than tall
        self.button_width = 100  # pixels
        self.button_height = 20  # pixels
        self.search_range = 300  # pixels to search above/below
        self.calibration_data = None
    
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
        """Calibrate by capturing button and background states"""
        print("\n=== Button Calibration ===")
        print("1. Move cursor to the CENTER of the button...")
        input("Press Enter when ready...")
        
        # Get cursor position
        x, y = pyautogui.position()
        print(f"Center position: ({x}, {y})")
        
        # Capture button state
        button_img = self.capture_region(x, y, self.button_width, self.button_height)
        
        print("\n2. Wait for the button to disappear...")
        input("Press Enter when the button is gone...")
        
        # Capture background state
        background = self.capture_region(x, y, self.button_width, self.button_height)
        
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
        
        # Calculate similarities
        diff_to_button = np.mean(np.abs(current - button_ref))
        diff_to_background = np.mean(np.abs(current - background_ref))
        
        # More similar to button than background
        return diff_to_button < diff_to_background, diff_to_button
    
    def verify_click(self, x, y):
        """Verify if clicking caused a state change"""
        before = self.capture_region(x, y, self.button_width, self.button_height)
        
        # Click
        original_x, original_y = pyautogui.position()
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.click()
        pyautogui.moveTo(original_x, original_y, duration=0.1)
        
        # Wait for state change
        time.sleep(0.2)
        
        # Check if state changed
        after = self.capture_region(x, y, self.button_width, self.button_height)
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
        min_click_interval = 1.0
        
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
                            if self.verify_click(base_x, check_y):
                                print("Click verified - state changed!")
                                last_click_time = current_time
                                break
                            else:
                                print("Click verification failed")
                
                print(".", end="", flush=True)
                time.sleep(0.1)
                
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