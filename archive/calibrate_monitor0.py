import cv2
import numpy as np
import pyautogui
import time
import logging
import mss
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def capture_and_analyze():
    try:
        with mss.mss() as sct:
            # Get monitor 0 (the main display at 0,0)
            monitor = None
            for i, m in enumerate(sct.monitors[1:], 1):
                if m['left'] == 0 and m['top'] == 0:
                    monitor = m
                    logger.info(f"Found main display (monitor 0) at index {i}")
                    break
            
            if monitor is None:
                raise ValueError("Could not find monitor 0 (main display at 0,0)")
            
            logger.info(f"Monitor 0: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            logger.info("Please hover over the target button on monitor 0...")
            logger.info("DO NOT CLICK THE BUTTON!")
            input("Press Enter when ready (while hovering)...")
            
            # Get cursor position
            x, y = pyautogui.position()
            logger.info(f"Cursor position: ({x}, {y})")
            
            # Verify cursor is on monitor 0
            if not (monitor["left"] <= x < monitor["left"] + monitor["width"] and 
                   monitor["top"] <= y < monitor["top"] + monitor["height"]):
                logger.error(f"Cursor position ({x}, {y}) is not on monitor 0! Please try again.")
                return
            
            # Capture regions of different sizes around cursor
            regions = [
                (20, "tiny"),
                (30, "small"),
                (40, "medium"),
                (50, "large")
            ]
            
            debug_dir = Path('temp/debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Capture full monitor for context
            full_monitor = np.array(sct.grab(monitor))
            full_bgr = cv2.cvtColor(full_monitor, cv2.COLOR_BGRA2BGR)
            
            # Draw cursor position and monitor bounds
            cv2.circle(full_bgr, (x - monitor["left"], y - monitor["top"]), 10, (0, 0, 255), 2)
            cv2.rectangle(full_bgr, (0, 0), (monitor["width"]-1, monitor["height"]-1), (0, 255, 0), 1)
            
            cv2.imwrite(str(debug_dir / f'monitor0_full_{timestamp}.png'), full_bgr)
            
            # Save the target region first
            target_region = {
                'left': x - 15,
                'top': y - 15,
                'width': 30,
                'height': 30
            }
            target_screenshot = np.array(sct.grab(target_region))
            target_bgr = cv2.cvtColor(target_screenshot, cv2.COLOR_BGRA2BGR)
            cv2.imwrite('images/target.png', target_bgr)
            logger.info("Saved new target.png")
            
            for size, name in regions:
                # Capture region centered on cursor
                half_size = size // 2
                region = {
                    'left': x - half_size,
                    'top': y - half_size,
                    'width': size,
                    'height': size
                }
                
                # Capture and save both BGR and YUV versions
                screenshot = np.array(sct.grab(region))
                bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
                
                # Save both versions
                cv2.imwrite(str(debug_dir / f'target_{name}_bgr_{timestamp}.png'), bgr)
                cv2.imwrite(str(debug_dir / f'target_{name}_yuv_{timestamp}.png'), yuv)
                
                # Analyze and log color information
                hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
                avg_color_bgr = np.mean(bgr, axis=(0,1))
                avg_color_yuv = np.mean(yuv, axis=(0,1))
                avg_color_hsv = np.mean(hsv, axis=(0,1))
                
                logger.info(f"\nAnalysis for {name} region ({size}x{size}):")
                logger.info(f"Average BGR: {avg_color_bgr}")
                logger.info(f"Average YUV: {avg_color_yuv}")
                logger.info(f"Average HSV: {avg_color_hsv}")
                
                # Calculate color variance
                var_bgr = np.var(bgr, axis=(0,1))
                var_yuv = np.var(yuv, axis=(0,1))
                var_hsv = np.var(hsv, axis=(0,1))
                
                logger.info(f"BGR variance: {var_bgr}")
                logger.info(f"YUV variance: {var_yuv}")
                logger.info(f"HSV variance: {var_hsv}")
            
            logger.info("\nCapture and analysis complete. Debug images saved to temp/debug/")
            logger.info("Please check the debug images to verify the captured regions.")
            
    except Exception as e:
        logger.error(f"Error during capture: {str(e)}")

if __name__ == "__main__":
    capture_and_analyze() 