"""
StuckMonitor - Monitor screen regions for inactivity and perform recovery actions.

This module provides functionality to:
1. Select and monitor a specific screen region
2. Detect when the region becomes static (no changes)
3. Perform configurable recovery actions

Usage:
    python stuck_monitor.py [--debug] [--interval SECONDS]

Example:
    python stuck_monitor.py --debug --interval 0.5
"""

import os
import sys
import time
import signal
import argparse
import numpy as np
import mss
import pyautogui
from PIL import Image
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass

from src.logging_config import setup_logging

@dataclass
class Region:
    """Screen region coordinates and dimensions."""
    left: int
    top: int
    width: int
    height: int

@dataclass
class ActionPoint:
    """Coordinates for action click."""
    x: int
    y: int

class StuckMonitor:
    """Monitor screen regions for inactivity and perform recovery actions."""
    
    def __init__(self, debug: bool = False, interval: float = 1.0):
        """Initialize the StuckMonitor.
        
        Args:
            debug: Enable debug logging
            interval: Scan interval in seconds
        """
        self.logger = setup_logging('stuck_monitor', debug)
        self.debug = debug
        self.interval = interval
        self.running = False
        
        # Initialize screen capture
        self.sct = mss.mss()
        
        # Region data
        self.region: Optional[Region] = None
        self.reference_state: Optional[np.ndarray] = None
        self.action_click: Optional[ActionPoint] = None
        self.stuck_command: Optional[str] = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
        
        self.logger.info(f"StuckMonitor initialized - Debug: {debug}, Interval: {interval}s")

    def select_region(self) -> None:
        """Interactive region selection and configuration.
        
        Guides the user through:
        1. Selecting region corners
        2. Setting action click position
        3. Configuring stuck command
        """
        print("\nSelect the region to monitor:")
        print("1. Move your mouse to the top-left corner")
        input("Press Enter when ready...")
        time.sleep(0.5)
        start_x, start_y = pyautogui.position()
        
        print("\n2. Move your mouse to the bottom-right corner")
        input("Press Enter when ready...")
        time.sleep(0.5)
        end_x, end_y = pyautogui.position()
        
        # Create region
        self.region = Region(
            left=min(start_x, end_x),
            top=min(start_y, end_y),
            width=abs(end_x - start_x),
            height=abs(end_y - start_y)
        )
        
        # Capture initial state
        print("\nCapturing reference state...")
        region_dict = {'left': self.region.left, 'top': self.region.top, 
                      'width': self.region.width, 'height': self.region.height}
        self.reference_state = np.array(self.sct.grab(region_dict)).astype(np.float32)
        
        print("\n3. Move your mouse to where you want to click when stuck")
        input("Press Enter when ready...")
        time.sleep(0.5)
        action_x, action_y = pyautogui.position()
        self.action_click = ActionPoint(x=action_x, y=action_y)
        
        print("\n4. Enter the command to type when stuck (e.g. /stuck):")
        self.stuck_command = input("> ").strip()
        
        print(f"\nMonitoring region: {self.region.width}x{self.region.height} "
              f"at ({self.region.left}, {self.region.top})")
        print(f"Action click position: ({self.action_click.x}, {self.action_click.y})")
        print(f"Stuck command: {self.stuck_command}")

    def check_for_change(self, current: np.ndarray, reference: np.ndarray) -> Tuple[bool, float]:
        """Check if current state is different from reference.
        
        Args:
            current: Current screen state as numpy array
            reference: Reference state to compare against
            
        Returns:
            Tuple of (is_different, difference_amount)
        """
        try:
            current = current.astype(np.float32)
            
            # Calculate difference
            diff = np.abs(current - reference)
            mean_diff = np.mean(diff)
            
            # State is different if mean difference is significant
            is_different = mean_diff > 5  # Lowered threshold for significant change
            
            if is_different and self.debug:
                self.logger.debug(f"Change detected! Mean difference: {mean_diff:.2f}")
            
            return is_different, mean_diff
            
        except Exception as e:
            self.logger.error(f"Error checking for change: {str(e)}")
            return False, 0.0

    def perform_action(self) -> bool:
        """Perform recovery action when screen is stuck.
        
        The action sequence is:
        1. Click at configured position
        2. Type configured command
        3. Press Command+Enter
        4. Return to original cursor position
        
        Returns:
            bool: True if action was successful
        """
        try:
            if not self.action_click or not self.stuck_command:
                self.logger.error("Action not configured")
                return False
                
            # Store original position
            original_x, original_y = pyautogui.position()
            
            # Move and click to activate input
            pyautogui.moveTo(self.action_click.x, self.action_click.y, duration=0.1)
            pyautogui.click()
            time.sleep(0.2)  # Wait for input focus
            
            # Type the command
            pyautogui.write(self.stuck_command)
            time.sleep(0.1)  # Small delay before key combo
            
            # Press Command+Enter
            pyautogui.hotkey('command', 'return')
            
            # Return to original position
            pyautogui.moveTo(original_x, original_y, duration=0.1)
            
            self.logger.info(f"Performed stuck action: click at ({self.action_click.x}, {self.action_click.y}), "
                           f"typed '{self.stuck_command}', pressed Cmd+Enter")
            return True
            
        except Exception as e:
            self.logger.error(f"Error performing action: {str(e)}")
            return False

    def run(self) -> None:
        """Main monitoring loop.
        
        Continuously monitors the selected region for changes:
        - Updates reference state when changes are detected
        - Performs recovery action if no changes for 30 seconds
        - Maintains action cooldown to prevent rapid clicking
        """
        if not self.region:
            self.select_region()
        
        self.running = True
        self.logger.info("Starting StuckMonitor")
        consecutive_changes = 0
        last_change_time = time.time()
        stuck_action_cooldown = 5.0  # Minimum time between actions
        last_action_time = 0
        last_state = self.reference_state
        
        try:
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Capture current state
                    region_dict = {'left': self.region.left, 'top': self.region.top, 
                                 'width': self.region.width, 'height': self.region.height}
                    current = np.array(self.sct.grab(region_dict)).astype(np.float32)
                    
                    # Check for change from last state
                    is_different, mean_diff = self.check_for_change(current, last_state)
                    
                    if is_different:
                        consecutive_changes += 1
                        if consecutive_changes >= 2:
                            self.logger.info(f"Change detected (difference: {mean_diff:.3f})")
                            last_change_time = current_time
                            consecutive_changes = 0
                            last_state = current  # Update reference to current state
                    else:
                        consecutive_changes = 0
                        # Check if stuck (no changes for 30 seconds)
                        if current_time - last_change_time > 30:
                            # Only perform action if cooldown has elapsed
                            if current_time - last_action_time >= stuck_action_cooldown:
                                self.logger.warning("No changes detected for 30 seconds - performing action!")
                                if self.perform_action():
                                    last_action_time = current_time
                                    last_change_time = current_time  # Reset stuck timer
                    
                    # Status update every 30 seconds
                    if int(current_time) % 30 == 0:
                        self.logger.info("Monitor running - watching for changes")
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {str(e)}")
                    time.sleep(self.interval)
                    
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            self.stop()
            sys.exit(1)

    def stop(self) -> None:
        """Clean shutdown of the monitor."""
        self.logger.info("Stopping StuckMonitor")
        self.running = False
        if hasattr(self, 'sct'):
            self.sct.close()

    def handle_interrupt(self, signum: int, frame) -> None:
        """Handle interrupt signals gracefully."""
        self.logger.info(f"Received signal {signum}")
        self.stop()

def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='StuckMonitor - Monitor screen region for changes')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Scan interval in seconds (default: 1.0)')
    args = parser.parse_args()

    try:
        monitor = StuckMonitor(
            debug=args.debug,
            interval=args.interval
        )
        monitor.run()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        if 'monitor' in locals():
            monitor.stop()

if __name__ == '__main__':
    main() 