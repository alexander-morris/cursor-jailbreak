#!/usr/bin/env python3
import mss
import json
import time
import pyautogui
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_position():
    """Wait for user to hover over a target and press Enter"""
    logger.info("Hover over a target button and press Enter...")
    while True:
        try:
            # Check if user pressed Enter
            if input() == '':
                x, y = pyautogui.position()
                return x, y
        except KeyboardInterrupt:
            return None, None

def get_monitor_info():
    """Get information about all monitors"""
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # Skip the "all monitors" monitor
        logger.info(f"Found {len(monitors)} monitors:")
        for i, m in enumerate(monitors):
            logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        return monitors

def calibrate_coordinates():
    """Let user hover over target buttons and save coordinates"""
    # Get monitor info
    monitors = get_monitor_info()
    
    # Create coordinates file
    coords_file = Path('target_coords.json')
    if coords_file.exists():
        logger.info("\nLoading existing coordinates...")
        with coords_file.open('r') as f:
            coords = json.load(f)
    else:
        coords = []
    
    logger.info("\nCalibration Instructions:")
    logger.info("1. Hover mouse over a target button")
    logger.info("2. Press Enter to save the position")
    logger.info("3. Type 'q' and press Enter when done")
    logger.info("4. Type 'c' and press Enter to clear all coordinates and start over")
    
    while True:
        # Show current coordinates
        if coords:
            logger.info("\nCurrent coordinates:")
            for i, c in enumerate(coords):
                logger.info(f"{i+1}. ({c['x']}, {c['y']}) on monitor {c['monitor']}")
        
        # Get user input
        response = input("\nPress Enter to add a target, 'q' to finish, or 'c' to clear: ").lower()
        if response == 'q':
            break
        elif response == 'c':
            coords = []
            logger.info("Cleared all coordinates")
            continue
        
        # Get current mouse position
        x, y = pyautogui.position()
        
        # Determine which monitor contains these coordinates
        monitor_index = None
        for i, m in enumerate(monitors):
            if (m['left'] <= x <= m['left'] + m['width'] and
                m['top'] <= y <= m['top'] + m['height']):
                monitor_index = i
                break
        
        if monitor_index is None:
            logger.warning("Position was outside all monitors")
            continue
        
        # Add coordinates
        coords.append({
            "x": x,
            "y": y,
            "monitor": monitor_index,
            "timestamp": time.time()
        })
        logger.info(f"Added target at ({x}, {y}) on monitor {monitor_index}")
    
    # Save coordinates
    with coords_file.open('w') as f:
        json.dump(coords, f, indent=2)
    logger.info(f"\nSaved {len(coords)} coordinates to {coords_file}")
    return coords

if __name__ == "__main__":
    try:
        coords = calibrate_coordinates()
        if len(coords) >= 2:
            logger.info("\nSuccess! Calibrated coordinates for all targets")
        else:
            logger.warning(f"\nWarning: Only calibrated {len(coords)} target(s)")
    except Exception as e:
        logger.error(f"Error: {str(e)}") 