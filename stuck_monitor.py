import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
import threading
import sys

class StuckMonitor:
    def __init__(self):
        self.sct = mss.mss()
        self.calibration_file = Path('stuck_calibration.json')
        self.last_change_time = time.time()
        self.last_content = None
        self.stall_threshold = 30  # 30 seconds before considering stuck
        
        # Set up the 30-second timeout for testing
        self.timeout_timer = threading.Timer(30.0, self.force_quit)
        self.timeout_timer.start()
    
    def force_quit(self):
        print("\nTimeout reached (30 seconds). Forcing script termination...")
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.cancel()
        if hasattr(self, 'sct'):
            self.sct.close()
    
    def calibrate(self):
        """Calibrate both composer area and continue button location"""
        data = {}
        
        print("\nCalibration Process:")
        print("\n1. Composer Area Calibration:")
        print("Move cursor to TOP-LEFT corner of composer area...")
        input("Press Enter when ready...")
        top_left_x, top_left_y = pyautogui.position()
        
        print("\nMove cursor to BOTTOM-RIGHT corner of composer area...")
        input("Press Enter when ready...")
        bottom_right_x, bottom_right_y = pyautogui.position()
        
        # Calculate composer region
        composer_region = {
            'left': top_left_x,
            'top': top_left_y,
            'width': bottom_right_x - top_left_x,
            'height': bottom_right_y - top_left_y
        }
        data['composer'] = composer_region
        
        print("\n2. Continue Button Calibration:")
        print("Move cursor to the continue/prompt input field...")
        input("Press Enter when ready...")
        prompt_x, prompt_y = pyautogui.position()
        data['prompt'] = {'x': prompt_x, 'y': prompt_y}
        
        # Save calibration
        with self.calibration_file.open('w') as f:
            json.dump(data, f)
        
        print("\nCalibration complete!")
        print(f"Monitoring composer area: {composer_region['width']}x{composer_region['height']} pixels")
        print(f"Continue button at: ({prompt_x}, {prompt_y})")
        return data
    
    def load_calibration(self):
        """Load saved calibration data"""
        try:
            with self.calibration_file.open('r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def check_for_changes(self, current, previous):
        """Check if the composer content has changed"""
        if previous is None:
            return True
        
        diff = np.abs(current - previous)
        mean_diff = np.mean(diff)
        return mean_diff > 2  # Small threshold for visual changes
    
    def send_continue_message(self, prompt_x, prompt_y):
        """Send the continue message"""
        # Store original cursor position
        original_x, original_y = pyautogui.position()
        
        try:
            # Move to prompt and click
            pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
            pyautogui.click()
            time.sleep(0.2)
            
            # Type continue message
            message = "continue"
            pyautogui.write(message)
            time.sleep(0.2)
            
            # Send message (Command + Return on macOS)
            pyautogui.hotkey('command', 'return')
            print(f"\nSent continue message at {time.strftime('%H:%M:%S')}")
            
        finally:
            # Restore cursor position
            pyautogui.moveTo(original_x, original_y, duration=0.2)
    
    def run(self):
        """Main monitoring loop"""
        try:
            # Load or create calibration
            data = self.load_calibration()
            if not data:
                print("No calibration found.")
                data = self.calibrate()
            
            print("\nMonitoring for stuck states...")
            print("Press Ctrl+C to stop")
            print("Script will automatically terminate after 30 seconds")
            
            while True:
                try:
                    # Capture current state of composer area
                    current = np.array(self.sct.grab(data['composer']))
                    
                    # Check for changes
                    if self.check_for_changes(current, self.last_content):
                        self.last_change_time = time.time()
                        print(".", end="", flush=True)  # Progress indicator
                    
                    # Check for stall
                    time_since_change = time.time() - self.last_change_time
                    if time_since_change >= self.stall_threshold:
                        print(f"\nStuck detected! No changes for {time_since_change:.1f} seconds")
                        self.send_continue_message(data['prompt']['x'], data['prompt']['y'])
                        self.last_change_time = time.time()  # Reset timer
                    
                    # Update last content
                    self.last_content = current
                    
                    # Small delay between checks
                    time.sleep(0.5)
                    
                except KeyboardInterrupt:
                    print("\nStopped by user")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    break
        finally:
            self.cleanup()

if __name__ == "__main__":
    monitor = StuckMonitor()
    try:
        monitor.run()
    finally:
        monitor.cleanup() 