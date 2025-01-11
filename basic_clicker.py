import numpy as np
import pyautogui
import time
import mss
import json
from pathlib import Path
import argparse
import threading
import sys

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
    """Capture both present and absent states of the target"""
    with mss.mss() as sct:
        while True:  # Loop until we get good calibration
            print("\n=== Button Present Calibration ===")
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
                retry = input("Would you like to try calibration again? (y/n): ")
                if retry.lower() == 'y':
                    continue
            
            # Save calibration data
            data = {
                'x': x,
                'y': y,
                'region': region,
                'present_pixels': present_img.tolist(),
                'absent_pixels': absent_img.tolist(),
                'mean_diff': float(mean_diff),
                'std_diff': float(std_diff)
            }
            
            with open('basic_target.json', 'w') as f:
                json.dump(data, f)
            
            print("\nCalibration complete!")
            print(f"Position: ({x}, {y})")
            print(f"Mean difference between states: {mean_diff:.2f}")
            print(f"Standard deviation of difference: {std_diff:.2f}")
            print("\nNote: The script will scan:")
            print(f"- Up to 100 pixels ABOVE {y}")
            print(f"- Up to 150 pixels BELOW {y}")
            print("for the target button")
            return data

def load_calibration():
    """Load the saved calibration data"""
    try:
        with open('basic_target.json', 'r') as f:
            data = json.load(f)
            data['present_pixels'] = np.array(data['present_pixels'])
            data['absent_pixels'] = np.array(data['absent_pixels'])
            return data
    except FileNotFoundError:
        return None

def find_button_in_region(current_full, target_template, similarity_threshold=0.65):
    """Scan the region to find the button, returns best match position"""
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
        diff = np.abs(window.astype(float) - target_template.astype(float))
        small_diff_ratio = np.mean(diff < 10)  # Percentage of very small differences
        similarity = (1 - np.mean(diff) / 255) * 0.7 + small_diff_ratio * 0.3  # Weighted score
        
        # Show significant matches
        if similarity > 0.6:  # Show more potential matches
            print(f"Found potential match at y={y} with similarity {similarity:.3f}")
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_y = y
    
    print(f"Best match: y={best_y} with similarity {best_similarity:.3f}")
    return best_similarity, best_y

def check_button_present(current, calibration_data, similarity_threshold=0.65):
    """Check if button is present using both calibrated states"""
    present_ref = calibration_data['present_pixels']
    absent_ref = calibration_data['absent_pixels']
    
    # Calculate similarity with more weight on exact matches
    diff_present = np.abs(current.astype(float) - present_ref.astype(float))
    similarity_to_present = 1 - np.mean(diff_present) / 255
    
    diff_absent = np.abs(current.astype(float) - absent_ref.astype(float))
    similarity_to_absent = 1 - np.mean(diff_absent) / 255
    
    # Button is present if it's significantly different from the absent state
    # This means similarity_to_absent should be low (< 0.85)
    is_present = similarity_to_absent < 0.85
    
    # Debug output for similarity scores
    print(f"\nSimilarity scores - Present: {similarity_to_present:.3f}, Absent: {similarity_to_absent:.3f}")
    if is_present:
        print("MATCH DETECTED!")
    
    return is_present, similarity_to_present

def run_clicker(dev_mode=False):
    """Main loop to check target area and click when matched"""
    sct = None
    timeout_timer = None
    try:
        # Set up 30-second timeout only in dev mode
        if dev_mode:
            timeout_timer = threading.Timer(30.0, force_quit)
            timeout_timer.start()
            print("Development mode: Script will terminate after 30 seconds")
        
        # Load or create calibration
        data = load_calibration()
        if not data:
            print("No calibration found.")
            data = calibrate()
        
        print(f"\nMonitoring target at ({data['x']}, {data['y']})...")
        print("Press Ctrl+C to stop")
        
        sct = mss.mss()
        last_feedback_time = time.time()
        last_click_time = 0
        min_click_interval = 0.5  # Reduced to 0.5 seconds between clicks
        consecutive_matches = 0  # Track consecutive matches
        
        while True:
            try:
                current_time = time.time()
                
                # Only check for button if enough time has passed since last click
                if current_time - last_click_time >= min_click_interval:
                    # Capture current state
                    current = np.array(sct.grab(data['region']))
                    
                    # Check if button is present
                    is_present, similarity = check_button_present(current, data)
                    
                    if is_present:
                        consecutive_matches += 1
                        # Only click if we've seen the button for a few frames
                        if consecutive_matches >= 2:
                            print(f"\nTarget matched (similarity: {similarity:.3f})!")
                            print(f"Clicking at ({data['x']}, {data['y']})")
                            
                            # Store original position
                            original_x, original_y = pyautogui.position()
                            
                            try:
                                # Move and click
                                pyautogui.moveTo(data['x'], data['y'], duration=0.1)
                                pyautogui.click()
                                
                                # Return to original position
                                pyautogui.moveTo(original_x, original_y, duration=0.1)
                                
                                # Update last click time
                                last_click_time = current_time
                                consecutive_matches = 0  # Reset after click
                                
                                # Small delay after click
                                time.sleep(0.1)
                                
                            except Exception as e:
                                print(f"Click failed: {str(e)}")
                    else:
                        consecutive_matches = 0  # Reset if no match
                
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
        cleanup(sct, timeout_timer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Basic target clicker with calibration')
    parser.add_argument('--calibrate', action='store_true', help='Run in calibration mode')
    parser.add_argument('--dev', action='store_true', help='Development mode: Enable 30-second timeout')
    args = parser.parse_args()
    
    if args.calibrate:
        print("Running calibration...")
        calibrate()
    else:
        run_clicker(dev_mode=args.dev) 