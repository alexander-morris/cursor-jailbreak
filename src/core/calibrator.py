"""
Calibration system for the Cursor Auto Accept application.
"""

import cv2
import numpy as np
from pathlib import Path
import mss
import pyautogui
import time
from PIL import Image
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

class Calibrator:
    def __init__(self):
        """Initialize the calibrator."""
        self.assets_dir = Path(ClickBotConfig.ASSETS_DIR)
        self.debug_dir = Path(ClickBotConfig.DEBUG_DIR)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def capture_button_state(self, button_index, monitor):
        """Capture button before and after click."""
        logger.info(f"Capturing button {button_index} state...")
        
        # Get screen coordinates
        x, y = pyautogui.position()
        
        # Convert screen coordinates to monitor-relative coordinates
        if x < 0:
            rel_x = abs(x - monitor["left"])
        else:
            rel_x = x - monitor["left"]
            
        if y < 0:
            rel_y = abs(y)
        else:
            rel_y = y - monitor["top"]
        
        logger.info(f"Mouse at screen coordinates: ({x}, {y})")
        logger.info(f"Monitor-relative coordinates: ({rel_x}, {rel_y})")
        
        # Calculate region around cursor (70x20 pixels, centered on mouse)
        template_region = {
            "left": x - 35,
            "top": y - 10,
            "width": 70,
            "height": 20,
            "mon": monitor["name"]
        }
        
        # Capture pre-click image
        monitor_dir = self.assets_dir / f'monitor_{monitor["name"]}'
        monitor_dir.mkdir(exist_ok=True)
        
        with mss.mss() as sct:
            screenshot = sct.grab(template_region)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            pre_path = monitor_dir / f'button_{button_index}_pre.png'
            img.save(pre_path)
            logger.info(f"Saved pre-click image: {pre_path}")
        
        # Wait for click
        time.sleep(3)  # Give time for click
        
        # Capture post-click image
        with mss.mss() as sct:
            screenshot = sct.grab(template_region)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            post_path = monitor_dir / f'button_{button_index}_post.png'
            img.save(post_path)
            logger.info(f"Saved post-click image: {post_path}")
        
        # Save coordinates
        coords_path = monitor_dir / f'click_coords_{button_index}.txt'
        with open(coords_path, 'w') as f:
            f.write(f"{rel_x},{rel_y}")
        logger.info(f"Saved coordinates: {rel_x},{rel_y}")
        
        # Save monitor info
        monitor_info_path = monitor_dir / f'monitor_{button_index}.txt'
        with open(monitor_info_path, 'w') as f:
            monitor_info = f"{monitor['left']},{monitor['top']},{monitor['width']},{monitor['height']}"
            f.write(monitor_info)
        logger.info(f"Saved monitor info: {monitor_info}")
        
        return rel_x, rel_y
        
    def check_calibration_data(self, monitor_name):
        """Check if calibration data exists for the specified monitor."""
        monitor_dir = self.assets_dir / f'monitor_{monitor_name}'
        if not monitor_dir.exists():
            return False
            
        pre_files = sorted(monitor_dir.glob('button_*_pre.png'))
        post_files = sorted(monitor_dir.glob('button_*_post.png'))
        coords_files = sorted(monitor_dir.glob('click_coords_*.txt'))
        monitor_files = sorted(monitor_dir.glob('monitor_*.txt'))
        
        return len(pre_files) > 0 and \
               len(post_files) > 0 and \
               len(coords_files) > 0 and \
               len(monitor_files) > 0
               
    def load_calibration_data(self, monitor_name):
        """Load calibration data for the specified monitor."""
        monitor_dir = self.assets_dir / f'monitor_{monitor_name}'
        if not self.check_calibration_data(monitor_name):
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
            
        return buttons 