"""
Calibration system for the Cursor Auto Accept application.
"""

import time
import mss
import cv2
import numpy as np
from pathlib import Path
import pyautogui
import traceback
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

class Calibrator:
    def __init__(self):
        """Initialize the calibrator."""
        self.base_dir = Path(ClickBotConfig.BASE_DIR)
        self.assets_dir = self.base_dir / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
    def get_monitor_dir(self, monitor):
        """Get the directory for a specific monitor's calibration data."""
        try:
            monitor_hash = f"{monitor['left']}_{monitor['top']}_{monitor['width']}_{monitor['height']}"
            monitor_dir = self.assets_dir / f"monitor_{monitor_hash}"
            monitor_dir.mkdir(parents=True, exist_ok=True)
            return monitor_dir
        except Exception as e:
            logger.error(f"Failed to create monitor directory: {e}")
            logger.error(traceback.format_exc())
            raise
        
    def capture_button_state(self, button_index, monitor):
        """Capture the state of a button."""
        try:
            logger.info(f"Capturing button {button_index} state...")
            
            # Get current mouse position
            mouse_x, mouse_y = pyautogui.position()
            
            # Log debug info
            logger.info("Debug: Screen coordinates before conversion:")
            logger.info(f"Mouse X: {mouse_x}, Mouse Y: {mouse_y}")
            logger.info(f"Monitor left: {monitor['left']}, Monitor top: {monitor['top']}")
            
            # Convert screen coordinates to monitor-relative coordinates
            if mouse_x < 0:
                logger.info(f"Debug: Converting negative X: {mouse_x} -> {abs(mouse_x - monitor['left'])}")
                rel_x = abs(mouse_x - monitor['left'])
            else:
                logger.info(f"Debug: Converting positive X: {mouse_x} -> {mouse_x - monitor['left']}")
                rel_x = mouse_x - monitor['left']
                
            if mouse_y < 0:
                logger.info(f"Debug: Converting negative Y: {mouse_y} -> {abs(mouse_y - monitor['top'])}")
                rel_y = abs(mouse_y - monitor['top'])
            else:
                logger.info(f"Debug: Converting positive Y: {mouse_y} -> {mouse_y - monitor['top']}")
                rel_y = mouse_y - monitor['top']
            
            logger.info(f"Mouse at screen coordinates: ({mouse_x}, {mouse_y})")
            logger.info(f"Monitor-relative coordinates: ({rel_x}, {rel_y})")
            logger.info(f"Using monitor: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Calculate template capture region
            template_left = mouse_x - 35  # Center the mouse position
            template_right = template_left + 70
            template_top = mouse_y - 10
            template_bottom = template_top + 20
            
            logger.info("Debug: Template capture region:")
            logger.info(f"Left edge: {template_left} (mouse X {mouse_x} - 35)")
            logger.info(f"Right edge: {template_right} (left + 70)")
            logger.info(f"Top edge: {template_top} (mouse Y {mouse_y} - 10)")
            logger.info(f"Bottom edge: {template_bottom} (top + 20)")
            
            # Get monitor-specific directory
            monitor_dir = self.get_monitor_dir(monitor)
            
            # Capture pre-click state
            logger.info("Preparing to capture pre-click state...")
            logger.info("Hover over button in 3...")
            time.sleep(1)
            logger.info("Hover over button in 2...")
            time.sleep(1)
            logger.info("Hover over button in 1...")
            time.sleep(1)
            logger.info("Capturing pre-click state now!")
            
            logger.info("Capturing pre-click image...")
            with mss.mss() as sct:
                # Capture region around mouse
                region = {
                    'left': template_left,
                    'top': template_top,
                    'width': 70,
                    'height': 20,
                    'mon': monitor.get('mon', 1)  # Default to first monitor if not specified
                }
                logger.info(f"Debug: Capture region: {region}")
                pre_click = np.array(sct.grab(region))
                pre_click = cv2.cvtColor(pre_click, cv2.COLOR_BGRA2BGR)
                
            # Save pre-click image
            pre_click_path = monitor_dir / f'button_{button_index}_pre.png'
            cv2.imwrite(str(pre_click_path), pre_click)
            logger.info(f"Saved pre-click image: {pre_click_path}")
            logger.info(f"Image size: {pre_click.shape[:2][::-1]}")
            
            # Capture post-click state
            logger.info("Preparing to capture post-click state...")
            logger.info("Click button in 3...")
            time.sleep(1)
            logger.info("Click button in 2...")
            time.sleep(1)
            logger.info("Click button in 1...")
            time.sleep(1)
            logger.info("Capturing post-click state now!")
            
            logger.info("Capturing post-click image...")
            with mss.mss() as sct:
                post_click = np.array(sct.grab(region))
                post_click = cv2.cvtColor(post_click, cv2.COLOR_BGRA2BGR)
                
            # Save post-click image
            post_click_path = monitor_dir / f'button_{button_index}_post.png'
            cv2.imwrite(str(post_click_path), post_click)
            logger.info(f"Saved post-click image: {post_click_path}")
            logger.info(f"Image size: {post_click.shape[:2][::-1]}")
            
            # Save coordinates
            coords_path = monitor_dir / f'click_coords_{button_index}.txt'
            with open(coords_path, 'w') as f:
                f.write(f"{rel_x},{rel_y}")
            logger.info(f"Saved coordinates to: {coords_path}")
            logger.info(f"Coordinates saved: {rel_x},{rel_y}")
            
            # Save monitor info
            monitor_path = monitor_dir / f'monitor_{button_index}.txt'
            with open(monitor_path, 'w') as f:
                f.write(f"{monitor['left']},{monitor['top']},{monitor['width']},{monitor['height']}")
            logger.info(f"Saved monitor info to: {monitor_path}")
            logger.info(f"Monitor info saved: {monitor['left']},{monitor['top']},{monitor['width']},{monitor['height']}")
            
            return rel_x, rel_y, pre_click, post_click
            
        except Exception as e:
            logger.error(f"Error capturing button state: {e}")
            logger.error(traceback.format_exc())
            raise
        
    def check_calibration_data(self, monitor):
        """Check if calibration data exists for the specified monitor."""
        try:
            monitor_dir = self.get_monitor_dir(monitor)
            if not monitor_dir.exists():
                return False
                
            pre_files = sorted(monitor_dir.glob('button_*_pre.png'))
            post_files = sorted(monitor_dir.glob('button_*_post.png'))
            coords_files = sorted(monitor_dir.glob('click_coords_*.txt'))
            monitor_files = sorted(monitor_dir.glob('monitor_*.txt'))
            
            has_data = len(pre_files) > 0 and \
                      len(post_files) > 0 and \
                      len(coords_files) > 0 and \
                      len(monitor_files) > 0
                      
            logger.info(f"Checking calibration data in {monitor_dir}:")
            logger.info(f"  Pre-click images: {len(pre_files)}")
            logger.info(f"  Post-click images: {len(post_files)}")
            logger.info(f"  Coordinate files: {len(coords_files)}")
            logger.info(f"  Monitor files: {len(monitor_files)}")
            logger.info(f"  Has complete data: {has_data}")
            
            return has_data
            
        except Exception as e:
            logger.error(f"Error checking calibration data: {e}")
            logger.error(traceback.format_exc())
            return False
               
    def load_calibration_data(self, monitor):
        """Load calibration data for the specified monitor."""
        try:
            monitor_dir = self.get_monitor_dir(monitor)
            if not self.check_calibration_data(monitor):
                return None
                
            pre_files = sorted(monitor_dir.glob('button_*_pre.png'))
            coords_files = sorted(monitor_dir.glob('click_coords_*.txt'))
            
            buttons = []
            for i, (pre_file, coords_file) in enumerate(zip(pre_files, coords_files), 1):
                template = cv2.imread(str(pre_file))
                if template is None:
                    logger.error(f"Failed to load template {pre_file}")
                    continue
                    
                with open(coords_file) as f:
                    x, y = map(int, f.read().strip().split(','))
                    
                buttons.append({
                    'template': template,
                    'x': x,
                    'y': y,
                    'index': i
                })
                logger.info(f"Loaded button {i} data:")
                logger.info(f"  Template: {pre_file}")
                logger.info(f"  Coordinates: ({x}, {y})")
                
            return buttons
            
        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")
            logger.error(traceback.format_exc())
            return None 