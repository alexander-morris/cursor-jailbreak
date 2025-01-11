import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
import platform
import threading
import sys

def force_quit():
    print("\nTimeout reached (30 seconds). Forcing script termination...")
    sys.exit(0)

# Verify we're on macOS for Command key usage
if platform.system() != "Darwin":
    print("Warning: This script uses macOS-specific key commands.")
    print("Modifications needed for Windows/Linux compatibility.")

class ComposerMonitor:
    def __init__(self):
        self.sct = mss.mss()
        self.calibration_file = Path('composer_calibration.json')
        self.stall_timeout = 60  # 1 minute timeout
        self.last_change_time = time.time()
        self.last_content = None
        
        # Set up the 30-second timeout
        self.timeout_timer = threading.Timer(30.0, force_quit)
        self.timeout_timer.start()
        
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.cancel()
        if hasattr(self, 'sct'):
            self.sct.close()
    
    def calibrate(self):
        """Calibrate the composer area and prompt location"""
        print("\nCalibration Process:")
        print("1. Move cursor to TOP-LEFT corner of composer area...")
        input("   Press Enter when ready...")
        top_left_x, top_left_y = pyautogui.position()
        
        print("\n2. Move cursor to BOTTOM-RIGHT corner of composer area...")
        input("   Press Enter when ready...")
        bottom_right_x, bottom_right_y = pyautogui.position()
        
        print("\n3. Move cursor to the PROMPT input field...")
        input("   Press Enter when ready...")
        prompt_x, prompt_y = pyautogui.position()
        
        # Calculate composer region
        region = {
            'left': top_left_x,
            'top': top_left_y,
            'width': bottom_right_x - top_left_x,
            'height': bottom_right_y - top_left_y
        }
        
        # Save calibration data
        data = {
            'region': region,
            'prompt': {
                'x': prompt_x,
                'y': prompt_y
            }
        }
        
        with self.calibration_file.open('w') as f:
            json.dump(data, f)
        
        print("\nCalibration complete!")
        print(f"Monitoring area: {region['width']}x{region['height']} pixels")
        print(f"Prompt location: ({prompt_x}, {prompt_y})")
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
        """Send the continuation message"""
        # Store original cursor position
        original_x, original_y = pyautogui.position()
        
        try:
            # Move to prompt
            pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
            pyautogui.click()
            time.sleep(0.2)  # Short delay after click
            
            # Type message
            message = "please continue by debugging - run your script, watch the logs, and verify the results. improve as necessary"
            pyautogui.write(message)
            time.sleep(0.2)  # Short delay after typing
            
            # Send message (Command + Return on macOS)
            pyautogui.hotkey('command', 'return')
            
            print(f"\nSent continuation message at {time.strftime('%H:%M:%S')}")
            
        finally:
            # Always restore cursor position
            pyautogui.moveTo(original_x, original_y, duration=0.2)
    
    def run(self):
        """Main monitoring loop"""
        try:
            # Load or create calibration
            data = self.load_calibration()
            if not data:
                print("No calibration found.")
                data = self.calibrate()
            
            print("\nMonitoring composer area...")
            print("Press Ctrl+C to stop")
            print("Script will automatically terminate after 30 seconds")
            
            while True:
                try:
                    # Capture current state of composer area
                    current = np.array(self.sct.grab(data['region']))
                    
                    # Check for changes
                    if self.check_for_changes(current, self.last_content):
                        self.last_change_time = time.time()
                    
                    # Check for stall
                    time_since_change = time.time() - self.last_change_time
                    if time_since_change >= self.stall_timeout:
                        print(f"\nComposer stalled for {time_since_change:.1f} seconds")
                        self.send_continue_message(data['prompt']['x'], data['prompt']['y'])
                        self.last_change_time = time.time()  # Reset timer
                    
                    # Update last content
                    self.last_content = current
                    
                    # Short delay between checks
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
    monitor = ComposerMonitor()
    try:
        monitor.run()
    finally:
        monitor.cleanup() 