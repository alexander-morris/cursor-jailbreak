"""
HustleBot - Combined clicker and stuck monitor with unified calibration.

This module provides:
1. Button click automation with calibration
2. Stuck detection and recovery
3. Session statistics tracking
"""

import os
import sys
import time
import json
import signal
import argparse
import numpy as np
import mss
import pyautogui
from PIL import Image
from typing import Dict, List, Optional, Tuple
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
    """Click coordinates."""
    x: int
    y: int

@dataclass
class Target:
    """Target button configuration."""
    region: Region
    click_pos: ActionPoint
    present_pixels: np.ndarray
    absent_pixels: np.ndarray

@dataclass
class StuckAction:
    """Stuck recovery action configuration."""
    region: Region
    click_pos: ActionPoint
    command: str
    reference_state: np.ndarray

class ClickStats:
    """Track and report session statistics."""
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

class HustleBot:
    """Combined clicker and stuck monitor."""
    
    def __init__(self, debug: bool = False, interval: float = 1.0, development: bool = False):
        self.logger = setup_logging('hustlebot', debug)
        self.debug = debug
        self.interval = interval
        self.development = development
        self.running = False
        self.last_click_time = 0
        self.click_cooldown = 5.0  # Minimum time between clicks
        self.start_time = time.time()
        
        # Initialize screen capture
        self.sct = mss.mss()
        
        # Targets and actions
        self.targets: List[Target] = []
        self.stuck_action: Optional[StuckAction] = None
        self.consecutive_matches = {}
        
        # Statistics
        self.stats = ClickStats()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
        
        self.logger.info(f"HustleBot initialized - Debug: {debug}, Interval: {interval}s, Development: {development}")

    def calibrate(self) -> None:
        """Interactive calibration for both clicking and stuck detection."""
        print("\n=== Button Calibration ===")
        while True:
            print(f"\nCurrently have {len(self.targets)} targets.")
            print("\nCalibrating new target...")
            
            # Select button region
            print("1. Move your mouse to the top-left corner of the button region")
            input("Press Enter when ready...")
            time.sleep(0.5)
            start_x, start_y = pyautogui.position()
            
            print("\n2. Move your mouse to the bottom-right corner of the button region")
            input("Press Enter when ready...")
            time.sleep(0.5)
            end_x, end_y = pyautogui.position()
            
            region = Region(
                left=min(start_x, end_x),
                top=min(start_y, end_y),
                width=abs(end_x - start_x),
                height=abs(end_y - start_y)
            )
            
            # Get click position
            print("\n3. Move your mouse to the exact click position")
            input("Press Enter when ready...")
            time.sleep(0.5)
            click_x, click_y = pyautogui.position()
            click_pos = ActionPoint(x=click_x, y=click_y)
            
            # Capture present state
            print("\n=== Button Present Calibration ===")
            input("4. Make sure the button IS present/visible, then press Enter...")
            region_dict = {'left': region.left, 'top': region.top, 
                          'width': region.width, 'height': region.height}
            present_pixels = np.array(self.sct.grab(region_dict)).astype(np.float32)
            
            # Capture absent state
            print("\n=== Button Absent Calibration ===")
            input("5. Make sure the button is NOT present/visible, then press Enter...")
            absent_pixels = np.array(self.sct.grab(region_dict)).astype(np.float32)
            
            # Create target
            target = Target(region=region, click_pos=click_pos,
                          present_pixels=present_pixels, absent_pixels=absent_pixels)
            self.targets.append(target)
            
            print("\nTarget calibrated successfully!")
            print(f"Click position: ({click_pos.x}, {click_pos.y})")
            
            if input("\nAdd another target? (y/n): ").lower() != 'y':
                break
        
        print("\n=== Stuck Detection Calibration ===")
        print("\nNow let's set up stuck detection...")
        
        # Select stuck monitor region
        print("1. Move your mouse to the top-left corner of the region to monitor")
        input("Press Enter when ready...")
        time.sleep(0.5)
        start_x, start_y = pyautogui.position()
        
        print("\n2. Move your mouse to the bottom-right corner of the region")
        input("Press Enter when ready...")
        time.sleep(0.5)
        end_x, end_y = pyautogui.position()
        
        stuck_region = Region(
            left=min(start_x, end_x),
            top=min(start_y, end_y),
            width=abs(end_x - start_x),
            height=abs(end_y - start_y)
        )
        
        # Get stuck action click position
        print("\n3. Move your mouse to where to click when stuck")
        input("Press Enter when ready...")
        time.sleep(0.5)
        action_x, action_y = pyautogui.position()
        action_pos = ActionPoint(x=action_x, y=action_y)
        
        # Get stuck command
        print("\n4. Enter the command to type when stuck (e.g. /stuck):")
        stuck_command = input("> ").strip()
        
        # Capture reference state
        print("\nCapturing reference state...")
        region_dict = {'left': stuck_region.left, 'top': stuck_region.top, 
                      'width': stuck_region.width, 'height': stuck_region.height}
        reference_state = np.array(self.sct.grab(region_dict)).astype(np.float32)
        
        # Create stuck action
        self.stuck_action = StuckAction(
            region=stuck_region,
            click_pos=action_pos,
            command=stuck_command,
            reference_state=reference_state
        )
        
        print("\nCalibration complete!")
        print(f"Monitoring {len(self.targets)} targets")
        print(f"Stuck detection region: {stuck_region.width}x{stuck_region.height} "
              f"at ({stuck_region.left}, {stuck_region.top})")
        print(f"Stuck action: Click at ({action_pos.x}, {action_pos.y}), "
              f"type '{stuck_command}', press Cmd+Enter")

    def check_button_present(self, current: np.ndarray, target: Target) -> Tuple[bool, float]:
        """Check if button is present using calibrated states."""
        try:
            current = current.astype(np.float32)
            
            # Calculate similarity with more weight on exact matches
            diff_present = np.abs(current - target.present_pixels)
            similarity_to_present = 1 - np.mean(diff_present) / 255
            
            diff_absent = np.abs(current - target.absent_pixels)
            similarity_to_absent = 1 - np.mean(diff_absent) / 255
            
            # Button is present if it's significantly different from the absent state
            is_present = similarity_to_absent < 0.85
            
            if is_present and self.debug:
                self.logger.debug(f"Match detected! Present: {similarity_to_present:.3f}, "
                                f"Absent: {similarity_to_absent:.3f}")
            
            return is_present, similarity_to_present
            
        except Exception as e:
            self.logger.error(f"Error checking button presence: {str(e)}")
            return False, 0.0

    def check_for_change(self, current: np.ndarray, reference: np.ndarray) -> Tuple[bool, float]:
        """Check if current state is different from reference."""
        try:
            current = current.astype(np.float32)
            
            # Calculate difference
            diff = np.abs(current - reference)
            mean_diff = np.mean(diff)
            
            # State is different if mean difference is significant
            is_different = mean_diff > 5  # Threshold for significant change
            
            if is_different and self.debug:
                self.logger.debug(f"Change detected! Mean difference: {mean_diff:.2f}")
            
            return is_different, mean_diff
            
        except Exception as e:
            self.logger.error(f"Error checking for change: {str(e)}")
            return False, 0.0

    def verify_click(self, region: Region, pre_click_state: np.ndarray) -> bool:
        """Verify click was successful by comparing screen state before and after."""
        try:
            time.sleep(0.2)  # Wait for UI to update
            region_dict = {'left': region.left, 'top': region.top, 
                          'width': region.width, 'height': region.height}
            post_click_state = np.array(self.sct.grab(region_dict))
            
            # Calculate difference between states
            diff = np.abs(post_click_state.astype(float) - pre_click_state.astype(float))
            mean_diff = np.mean(diff)
            
            # If states are very similar, click probably didn't work
            success = mean_diff > 10  # Threshold for significant change
            
            if self.debug:
                self.logger.debug(f"Click verification - Mean difference: {mean_diff:.2f}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error verifying click: {str(e)}")
            return False

    def perform_stuck_action(self) -> bool:
        """Perform recovery action when screen is stuck."""
        try:
            if not self.stuck_action:
                self.logger.error("Stuck action not configured")
                return False
                
            # Store original position
            original_x, original_y = pyautogui.position()
            
            # Move and click to activate input
            pyautogui.moveTo(self.stuck_action.click_pos.x, 
                           self.stuck_action.click_pos.y, duration=0.1)
            pyautogui.click()
            time.sleep(0.2)  # Wait for input focus
            
            # Type the command
            pyautogui.write(self.stuck_action.command)
            time.sleep(0.1)  # Small delay before key combo
            
            # Press Command+Enter
            pyautogui.hotkey('command', 'return')
            
            # Return to original position
            pyautogui.moveTo(original_x, original_y, duration=0.1)
            
            self.logger.info(f"Performed stuck action: click at "
                           f"({self.stuck_action.click_pos.x}, {self.stuck_action.click_pos.y}), "
                           f"typed '{self.stuck_action.command}', pressed Cmd+Enter")
            return True
            
        except Exception as e:
            self.logger.error(f"Error performing stuck action: {str(e)}")
            return False

    def run(self) -> None:
        """Main bot loop combining clicking and stuck detection."""
        if not self.targets or not self.stuck_action:
            self.calibrate()
        
        self.running = True
        self.logger.info("Starting HustleBot")
        
        # Initialize tracking variables
        self.consecutive_matches = {i: 0 for i in range(len(self.targets))}
        consecutive_changes = 0
        last_change_time = time.time()
        stuck_action_cooldown = 5.0  # Minimum time between stuck actions
        last_action_time = 0
        last_stuck_state = self.stuck_action.reference_state
        
        try:
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Development mode: auto-terminate after 30 seconds
                    if self.development and (current_time - self.start_time > 30):
                        self.logger.info("Development mode: 30 second timeout reached")
                        self.stop()
                        break

                    # Only check for buttons if enough time has passed since last click
                    if current_time - self.last_click_time >= self.click_cooldown:
                        # Check each target
                        for i, target in enumerate(self.targets):
                            # Capture current state for this target
                            region_dict = {'left': target.region.left, 'top': target.region.top, 
                                         'width': target.region.width, 'height': target.region.height}
                            current = np.array(self.sct.grab(region_dict))
                            
                            # Check if button is present
                            is_present, similarity = self.check_button_present(current, target)
                            
                            if is_present:
                                self.consecutive_matches[i] += 1
                                # Only click if we've seen the button for a few frames
                                if self.consecutive_matches[i] >= 2:
                                    self.logger.info(f"Target {i+1} matched (similarity: {similarity:.3f})")
                                    
                                    # Store original position and screen state
                                    original_x, original_y = pyautogui.position()
                                    pre_click_state = current.copy()
                                    
                                    try:
                                        # Move and click
                                        pyautogui.moveTo(target.click_pos.x, target.click_pos.y, duration=0.1)
                                        pyautogui.click()
                                        
                                        # Verify click
                                        click_success = self.verify_click(target.region, pre_click_state)
                                        self.stats.record_click(click_success)
                                        
                                        if click_success:
                                            self.logger.info("Click verified successful!")
                                        else:
                                            self.logger.warning("Click verification failed - no UI change detected")
                                        
                                        # Return to original position
                                        pyautogui.moveTo(original_x, original_y, duration=0.1)
                                        
                                    except Exception as e:
                                        self.logger.error(f"Click failed: {str(e)}")
                                        continue
                                    
                                    # Update last click time
                                    self.last_click_time = current_time
                                    # Reset consecutive matches for all targets
                                    self.consecutive_matches = {i: 0 for i in range(len(self.targets))}
                                    
                                    # Print current stats every 10 clicks
                                    if self.stats.total_clicks % 10 == 0:
                                        self.stats.print_stats()
                                    break
                            else:
                                self.consecutive_matches[i] = 0  # Reset if no match
                    
                    # Check for stuck state
                    stuck_region_dict = {'left': self.stuck_action.region.left, 
                                       'top': self.stuck_action.region.top,
                                       'width': self.stuck_action.region.width, 
                                       'height': self.stuck_action.region.height}
                    current_stuck = np.array(self.sct.grab(stuck_region_dict))
                    
                    # Check for change in stuck monitor region
                    is_different, mean_diff = self.check_for_change(current_stuck, last_stuck_state)
                    
                    if is_different:
                        consecutive_changes += 1
                        if consecutive_changes >= 2:
                            self.logger.info(f"Change detected in stuck region (difference: {mean_diff:.3f})")
                            last_change_time = current_time
                            consecutive_changes = 0
                            last_stuck_state = current_stuck
                    else:
                        consecutive_changes = 0
                        # Check if stuck (no changes for 30 seconds)
                        if current_time - last_change_time > 30:
                            # Only perform action if cooldown has elapsed
                            if current_time - last_action_time >= stuck_action_cooldown:
                                self.logger.warning("No changes detected for 30 seconds - performing stuck action!")
                                if self.perform_stuck_action():
                                    last_action_time = current_time
                                    last_change_time = current_time
                    
                    # Status update every 30 seconds
                    if int(current_time) % 30 == 0:
                        self.logger.info("Bot running - monitoring targets and stuck state")
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {str(e)}")
                    time.sleep(self.interval)
                    
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            self.stop()
            sys.exit(1)

    def stop(self) -> None:
        """Clean shutdown of the bot."""
        self.logger.info("Stopping HustleBot")
        self.running = False
        if hasattr(self, 'sct'):
            self.sct.close()
        self.stats.print_stats()

    def handle_interrupt(self, signum: int, frame) -> None:
        """Handle interrupt signals gracefully."""
        self.logger.info(f"Received signal {signum}")
        self.stop()

def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='HustleBot - Combined clicker and stuck monitor')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--development', action='store_true', help='Development mode (30 second timeout)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Scan interval in seconds (default: 1.0)')
    args = parser.parse_args()

    try:
        bot = HustleBot(
            debug=args.debug,
            interval=args.interval,
            development=args.development
        )
        bot.run()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        if 'bot' in locals():
            bot.stop()

if __name__ == '__main__':
    main() 