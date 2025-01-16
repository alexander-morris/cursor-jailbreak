import numpy as np
import pyautogui
import time
import mss
import json
import logging
from pathlib import Path
import sys
import os
import shutil
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clicker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure PyAutoGUI
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.05  # Small delay between PyAutoGUI commands

# Constants
CLICK_TIMEOUT = 5.0  # Wait up to 5 seconds between clicks
BUTTON_CHECK_INTERVAL = 0.5  # Check for button every 0.5 seconds
CACHE_DIR = os.path.expanduser("~/Library/Caches/Google/Chrome/Default/Cache")  # Chrome cache directory

def capture_button_samples(x, y, target_id):
    """Capture samples of what the button looks like when present and absent"""
    try:
        with mss.mss() as sct:
            # Capture region around target
            region = {
                'left': x - 25,
                'top': y - 25,
                'width': 50,
                'height': 50
            }
            
            # First capture when button is present
            logger.info(f"\nCalibrating target {target_id} at ({x}, {y})")
            logger.info("Please ensure button IS VISIBLE and press Enter...")
            input()
            screenshot = np.array(sct.grab(region))
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
            
            # Calculate metrics for present state
            y_channel = img_yuv[:, :, 0]
            blur = cv2.GaussianBlur(y_channel, (5, 5), 0)
            contrast = cv2.absdiff(y_channel, blur)
            present_contrast = float(np.mean(contrast))
            
            u_var = np.var(img_yuv[:, :, 1])
            v_var = np.var(img_yuv[:, :, 2])
            present_variance = float((u_var + v_var) / 2)
            
            # Now capture when button is absent
            logger.info("\nPlease ensure button is NOT VISIBLE and press Enter...")
            input()
            screenshot = np.array(sct.grab(region))
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
            
            # Calculate metrics for absent state
            y_channel = img_yuv[:, :, 0]
            blur = cv2.GaussianBlur(y_channel, (5, 5), 0)
            contrast = cv2.absdiff(y_channel, blur)
            absent_contrast = float(np.mean(contrast))
            
            u_var = np.var(img_yuv[:, :, 1])
            v_var = np.var(img_yuv[:, :, 2])
            absent_variance = float((u_var + v_var) / 2)
            
            # Return calibration data
            calibration = {
                'present': {
                    'contrast': present_contrast,
                    'color_variance': present_variance,
                },
                'absent': {
                    'contrast': absent_contrast,
                    'color_variance': absent_variance,
                },
                'timestamp': time.time()
            }
            
            logger.info(f"\nCalibrated target {target_id}:")
            logger.info(f"Present - contrast: {present_contrast:.2f}, variance: {present_variance:.2f}")
            logger.info(f"Absent  - contrast: {absent_contrast:.2f}, variance: {absent_variance:.2f}")
            return calibration
            
    except Exception as e:
        logger.error(f"Error capturing button samples: {str(e)}")
        return None

def load_button_calibrations():
    """Load button calibration data for all targets"""
    try:
        with open('button_calibrations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Error loading button calibrations: {str(e)}")
        return {}

def save_button_calibrations(calibrations):
    """Save button calibration data for all targets"""
    try:
        with open('button_calibrations.json', 'w') as f:
            json.dump(calibrations, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving button calibrations: {str(e)}")
        return False

def check_button_present(x, y, calibration):
    """Check if button is present using calibrated values"""
    try:
        with mss.mss() as sct:
            # Capture region around target
            region = {
                'left': x - 25,
                'top': y - 25,
                'width': 50,
                'height': 50
            }
            screenshot = np.array(sct.grab(region))
            
            # Convert BGRA to BGR
            img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Convert to YUV color space
            img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
            
            # Calculate metrics
            y_channel = img_yuv[:, :, 0]
            blur = cv2.GaussianBlur(y_channel, (5, 5), 0)
            contrast = cv2.absdiff(y_channel, blur)
            avg_contrast = np.mean(contrast)
            
            u_var = np.var(img_yuv[:, :, 1])
            v_var = np.var(img_yuv[:, :, 2])
            color_variance = (u_var + v_var) / 2
            
            # Compare with calibration
            present_contrast_diff = abs(avg_contrast - calibration['present']['contrast'])
            present_variance_diff = abs(color_variance - calibration['present']['color_variance'])
            
            absent_contrast_diff = abs(avg_contrast - calibration['absent']['contrast'])
            absent_variance_diff = abs(color_variance - calibration['absent']['color_variance'])
            
            # Log values for debugging
            logger.debug(f"Button check at ({x}, {y}):")
            logger.debug(f"  Current - contrast: {avg_contrast:.2f}, variance: {color_variance:.2f}")
            logger.debug(f"  Present diff - contrast: {present_contrast_diff:.2f}, variance: {present_variance_diff:.2f}")
            logger.debug(f"  Absent diff  - contrast: {absent_contrast_diff:.2f}, variance: {absent_variance_diff:.2f}")
            
            # Button is present if it's closer to the "present" calibration than the "absent" calibration
            # AND the differences are within reasonable thresholds
            is_present = (present_contrast_diff < absent_contrast_diff and 
                        present_variance_diff < absent_variance_diff and
                        present_contrast_diff < 5 and 
                        present_variance_diff < 100)
            
            if is_present:
                logger.info(f"Button detected at ({x}, {y})")
            
            return is_present
            
    except Exception as e:
        logger.error(f"Error checking button: {str(e)}")
        return False

def clear_cache():
    """Clear Chrome browser cache"""
    try:
        if os.path.exists(CACHE_DIR):
            logger.info("Clearing Chrome cache...")
            cache_data_dir = os.path.join(CACHE_DIR, "Cache_Data")
            
            # Clear files in main cache directory
            for item in os.listdir(CACHE_DIR):
                item_path = os.path.join(CACHE_DIR, item)
                try:
                    if item != "Cache_Data":  # Skip Cache_Data directory
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                except Exception as e:
                    logger.error(f"Error removing {item_path}: {str(e)}")
            
            # Clear files in Cache_Data directory
            if os.path.exists(cache_data_dir):
                for item in os.listdir(cache_data_dir):
                    item_path = os.path.join(cache_data_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                    except Exception as e:
                        logger.error(f"Error removing {item_path}: {str(e)}")
            
            logger.info("Cache cleared successfully")
            return True
        else:
            logger.warning(f"Cache directory not found at {CACHE_DIR}")
            return False
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

def perform_click(x, y):
    """Perform simple click action with cache clearing"""
    try:
        # Clear cache first
        clear_cache()
        
        # Store original position
        original_x, original_y = pyautogui.position()
        
        # Move and click
        logger.info(f"Moving to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.05)
        pyautogui.click()
        time.sleep(0.5)
        
        # Return to original position
        pyautogui.moveTo(original_x, original_y, duration=0.05)
        logger.info("Click completed")
        return True
    except Exception as e:
        logger.error(f"Error performing click: {str(e)}")
        return False

def load_calibration():
    """Load the saved calibration data"""
    try:
        with open('click_targets.json', 'r') as f:
            targets = json.load(f)
            logger.info(f"Loaded {len(targets)} targets from calibration")
            return targets
    except FileNotFoundError:
        logger.error("No calibration found. Please run setup_monitors.py first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading calibration: {str(e)}")
        sys.exit(1)

def run_clicker():
    """Main loop to check target areas and click when matched"""
    try:
        # Load calibration
        targets = load_calibration()
        
        # Load or create button calibrations
        button_calibrations = load_button_calibrations()
        
        # Check if we need to calibrate any targets
        for i, target in enumerate(targets):
            target_id = f"target_{target['x']}_{target['y']}"
            if target_id not in button_calibrations:
                logger.info(f"\nNo calibration found for target {i+1}. Let's calibrate it...")
                calibration = capture_button_samples(target['x'], target['y'], i+1)
                if calibration:
                    button_calibrations[target_id] = calibration
                    save_button_calibrations(button_calibrations)
                else:
                    logger.error(f"Failed to calibrate target {i+1}")
                    return
        
        logger.info("\nMonitoring targets:")
        for i, target in enumerate(targets, 1):
            logger.info(f"Target {i} at ({target['x']}, {target['y']})")
        logger.info("Press Ctrl+C to stop")
        
        click_count = 0
        last_click_time = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Only proceed if enough time has passed since last click
                if (current_time - last_click_time) >= CLICK_TIMEOUT:
                    # Check each target
                    for target in targets:
                        x, y = target['x'], target['y']
                        target_id = f"target_{x}_{y}"
                        
                        # Check if button is present using calibration
                        if check_button_present(x, y, button_calibrations[target_id]):
                            if perform_click(x, y):
                                click_count += 1
                                last_click_time = current_time
                                logger.info(f"Total clicks: {click_count}")
                                break  # Only click one button per cycle
                
                # Small delay between checks
                time.sleep(BUTTON_CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\nStopped by user")
                break
            except Exception as e:
                logger.error(f"Error in click loop: {str(e)}")
                time.sleep(1.0)  # Wait after error
        
        logger.info("Clicker stopped gracefully")
        
    except Exception as e:
        logger.error(f"Fatal error in clicker: {str(e)}")
    finally:
        logger.info(f"Clicker shutting down. Total clicks: {click_count}")

if __name__ == "__main__":
    run_clicker() 