import os
import sys
import time
import signal
import argparse
from datetime import datetime
import pyautogui
import numpy as np
from PIL import Image

# Update imports to use src directory
from src.image_matcher import ImageMatcher
from src.error_recovery import ErrorRecoveryHandler
from src.logging_config import setup_logging, log_error_with_context, log_match_result, save_debug_image
import mss
import json
from pathlib import Path
import threading

def force_quit():
    print("\nTimeout reached (30 seconds). Forcing script termination...")
    sys.exit(0)

def cleanup(sct=None, timeout_timer=None):
    """Cleanup resources"""
    if timeout_timer:
        timeout_timer.cancel()
    if sct:
        sct.close()

def capture_state(sct, x, y):
    """Capture the current state around the given coordinates"""
    region = {
        'left': x - 5,     # 5 pixels left of cursor
        'top': y - 5,      # 5 pixels above cursor
        'width': 10,       # 10 pixels wide
        'height': 10       # 10 pixels tall
    }
    return np.array(sct.grab(region)), region

def calibrate():
    """Capture both present and absent states for multiple targets"""
    targets = []
    with mss.mss() as sct:
        while True:  # Loop until user is done adding targets
            print(f"\nCurrently have {len(targets)} targets.")
            if len(targets) > 0 and input("Done adding targets? (y/n): ").lower() == 'y':
                break
                
            print("\n=== Button Present Calibration ===")
            print(f"Target #{len(targets) + 1}")
            print("1. Hover over the target button when it IS present (DO NOT CLICK)...")
            print("Make sure the button is fully visible!")
            input("Press Enter when ready...")
            
            # Get cursor position for present state
            x, y = pyautogui.position()
            print(f"Target position: ({x}, {y})")
            
            # Capture button present state
            present_img, region = capture_state(sct, x, y)
            
            print("\n=== Button Absent Calibration ===")
            print("2. Wait for the button to completely disappear at the SAME location...")
            print("Make sure there are no other UI elements in this area!")
            input("Press Enter when the button is completely gone...")
            
            # Capture button absent state at the same position
            absent_img, _ = capture_state(sct, x, y)
            
            # Calculate difference metrics
            diff = np.abs(present_img.astype(float) - absent_img.astype(float))
            mean_diff = np.mean(diff)
            std_diff = np.std(diff)
            
            # Validate the calibration
            if mean_diff < 5:
                print("\nWarning: The difference between present and absent states is very small.")
                print("This might indicate that the calibration didn't capture distinct states.")
                retry = input("Would you like to try calibrating this target again? (y/n): ")
                if retry.lower() == 'y':
                    continue
            
            # Save target data
            target = {
                'x': x,
                'y': y,
                'region': region,
                'present_pixels': present_img.tolist(),
                'absent_pixels': absent_img.tolist(),
                'mean_diff': float(mean_diff),
                'std_diff': float(std_diff)
            }
            
            targets.append(target)
            print(f"\nTarget #{len(targets)} saved at ({x}, {y})")
            print(f"Mean difference between states: {mean_diff:.2f}")
            print(f"Standard deviation of difference: {std_diff:.2f}")
        
        # Save all targets
        with open('basic_targets.json', 'w') as f:
            json.dump(targets, f)
        
        print(f"\nCalibration complete! Saved {len(targets)} targets.")
        for i, target in enumerate(targets, 1):
            print(f"Target {i} at ({target['x']}, {target['y']})")
        
        return targets

def load_calibration():
    """Load the saved calibration data"""
    try:
        with open('basic_targets.json', 'r') as f:
            targets = json.load(f)
            # Convert lists back to numpy arrays
            for target in targets:
                target['present_pixels'] = np.array(target['present_pixels'], dtype=np.float32)
                target['absent_pixels'] = np.array(target['absent_pixels'], dtype=np.float32)
            return targets
    except FileNotFoundError:
        return None

def find_button_in_region(current_full, target_template, similarity_threshold=0.65):
    """Scan the region to find the button, returns best match position"""
    try:
        current_full = current_full.astype(np.float32)
        target_template = target_template.astype(np.float32)
        
        template_height, template_width = target_template.shape[:2]  # Get dimensions from template
        best_similarity = 0
        best_y = None
        
        # Debug info about scanning region
        print(f"\nScanning region: {current_full.shape}")
        print(f"Template size: {target_template.shape}")
        
        # Scan through the region vertically
        for y in range(current_full.shape[0] - template_height):
            # Extract a window of the same size as our template
            window = current_full[y:y + template_height, :template_width]
            if window.shape != target_template.shape:
                continue
                
            # Calculate similarity with more weight on exact matches
            diff = np.abs(window - target_template)
            small_diff_ratio = np.mean(diff < 10)  # Percentage of very small differences
            similarity = (1 - np.mean(diff) / 255) * 0.7 + small_diff_ratio * 0.3  # Weighted score
            
            # Only show very strong matches
            if similarity > 0.8:  # Show more potential matches
                print(f"Strong match at y={y} with similarity {similarity:.3f}")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_y = y
        
        if best_similarity > 0.6:
            print(f"Best match: y={best_y} with similarity {best_similarity:.3f}")
        return best_similarity, best_y
    except Exception as e:
        print(f"Error finding button in region: {str(e)}")
        return 0.0, None

def check_button_present(current, calibration_data, similarity_threshold=0.65):
    """Check if button is present using both calibrated states"""
    try:
        present_ref = np.array(calibration_data['present_pixels'], dtype=np.float32)
        absent_ref = np.array(calibration_data['absent_pixels'], dtype=np.float32)
        current = current.astype(np.float32)
        
        # Calculate similarity with more weight on exact matches
        diff_present = np.abs(current - present_ref)
        similarity_to_present = 1 - np.mean(diff_present) / 255
        
        diff_absent = np.abs(current - absent_ref)
        similarity_to_absent = 1 - np.mean(diff_absent) / 255
        
        # Button is present if it's significantly different from the absent state
        # This means similarity_to_absent should be low (< 0.85)
        is_present = similarity_to_absent < 0.85
        
        # Only output debug info if there's a significant change
        if is_present:
            print(f"\nMatch detected! Present: {similarity_to_present:.3f}, Absent: {similarity_to_absent:.3f}")
        
        return is_present, similarity_to_present
    except Exception as e:
        print(f"Error checking button presence: {str(e)}")
        return False, 0.0

class ClickStats:
    def __init__(self):
        self.total_clicks = 0
        self.successful_clicks = 0
        self.start_time = time.time()
        self.last_click_time = None
        
    def record_click(self, success=True):
        self.total_clicks += 1
        if success:
            self.successful_clicks += 1
        self.last_click_time = time.time()
    
    def get_stats(self):
        runtime = time.time() - self.start_time
        hours = runtime / 3600
        clicks_per_hour = self.total_clicks / hours if hours > 0 else 0
        success_rate = (self.successful_clicks / self.total_clicks * 100) if self.total_clicks > 0 else 0
        
        return {
            'runtime_hours': hours,
            'total_clicks': self.total_clicks,
            'successful_clicks': self.successful_clicks,
            'clicks_per_hour': clicks_per_hour,
            'success_rate': success_rate
        }
    
    def print_stats(self):
        stats = self.get_stats()
        print("\nSession Statistics:")
        print(f"Runtime: {stats['runtime_hours']:.2f} hours")
        print(f"Total Clicks: {stats['total_clicks']}")
        print(f"Successful Clicks: {stats['successful_clicks']}")
        print(f"Clicks/Hour: {stats['clicks_per_hour']:.1f}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")

def verify_click(sct, target, pre_click_state):
    """Verify click was successful by comparing screen state before and after"""
    time.sleep(0.2)  # Wait for UI to update
    post_click_state = np.array(sct.grab(target['region']))
    
    # Calculate difference between states
    diff = np.abs(post_click_state.astype(float) - pre_click_state.astype(float))
    mean_diff = np.mean(diff)
    
    # If states are very similar, click probably didn't work
    return mean_diff > 10  # Threshold for significant change

def run_clicker(dev_mode=False):
    """Main loop to check target areas and click when matched"""
    sct = None
    timeout_timer = None
    stats = ClickStats()
    
    try:
        # Set up 30-second timeout only in dev mode
        if dev_mode:
            timeout_timer = threading.Timer(30.0, force_quit)
            timeout_timer.start()
            print("Development mode: Script will terminate after 30 seconds")
        
        # Load or create calibration
        targets = load_calibration()
        if not targets:
            print("No calibration found.")
            targets = calibrate()
        
        print("\nMonitoring targets:")
        for i, target in enumerate(targets, 1):
            print(f"Target {i} at ({target['x']}, {target['y']})")
        print("Press Ctrl+C to stop")
        
        sct = mss.mss()
        last_feedback_time = time.time()
        last_click_time = 0
        min_click_interval = 5.0  # Minimum seconds between clicks
        consecutive_matches = {i: 0 for i in range(len(targets))}  # Track consecutive matches per target
        
        while True:
            try:
                current_time = time.time()
                
                # Only check for buttons if enough time has passed since last click
                if current_time - last_click_time >= min_click_interval:
                    # Check each target
                    for i, target in enumerate(targets):
                        # Capture current state for this target
                        current = np.array(sct.grab(target['region']))
                        
                        # Check if button is present
                        is_present, similarity = check_button_present(current, target)
                        
                        if is_present:
                            consecutive_matches[i] += 1
                            # Only click if we've seen the button for a few frames
                            if consecutive_matches[i] >= 2:
                                print(f"\nTarget {i+1} matched (similarity: {similarity:.3f})!")
                                print(f"Clicking at ({target['x']}, {target['y']})")
                                
                                # Store original position and screen state
                                original_x, original_y = pyautogui.position()
                                pre_click_state = current.copy()
                                
                                try:
                                    # Move and click
                                    pyautogui.moveTo(target['x'], target['y'], duration=0.1)
                                    pyautogui.click()
                                    
                                    # Verify click
                                    click_success = verify_click(sct, target, pre_click_state)
                                    stats.record_click(click_success)
                                    
                                    if click_success:
                                        print("Click verified successful!")
                                    else:
                                        print("Click verification failed - no UI change detected")
                                    
                                    # Return to original position
                                    pyautogui.moveTo(original_x, original_y, duration=0.1)
                                    
                                    # Update last click time
                                    last_click_time = current_time
                                    # Reset consecutive matches for all targets
                                    consecutive_matches = {i: 0 for i in range(len(targets))}
                                    
                                    # Print current stats every 10 clicks
                                    if stats.total_clicks % 10 == 0:
                                        stats.print_stats()
                                    
                                    # Small delay after click
                                    time.sleep(0.1)
                                    
                                    # Break after clicking one target
                                    break
                                    
                                except Exception as e:
                                    print(f"Click failed: {str(e)}")
                                    stats.record_click(False)
                        else:
                            consecutive_matches[i] = 0  # Reset if no match
                
                # Visual feedback every second
                if current_time - last_feedback_time >= 1.0:
                    print(".", end="", flush=True)
                    last_feedback_time = current_time
                
                # Very small delay between scans
                time.sleep(0.02)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                break
    finally:
        # Print final stats
        print("\nFinal Statistics:")
        stats.print_stats()
        cleanup(sct, timeout_timer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Multi-target clicker with calibration')
    parser.add_argument('--calibrate', action='store_true', help='Run in calibration mode')
    parser.add_argument('--dev', action='store_true', help='Development mode: Enable 30-second timeout')
    args = parser.parse_args()
    
    if args.calibrate:
        print("Running calibration...")
        calibrate()
    else:
        run_clicker(dev_mode=args.dev) 