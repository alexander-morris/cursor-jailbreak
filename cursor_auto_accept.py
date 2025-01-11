import cv2
import numpy as np
import pyautogui
import time
import logging
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import mss

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_bot.log'),
        logging.StreamHandler()
    ]
)

class NoteDetector:
    def __init__(self, dev_mode=False, calibrate=False):
        self.logger = logging.getLogger(__name__)
        self.sct = mss.mss()
        self.dev_mode = dev_mode
        self.calibrate = calibrate
        self.running = False  # Add flag to control running state
        
        # Load images
        self.images_dir = Path('images')
        if not self.calibrate:
            # Load target image
            target_path = self.images_dir / 'target.png'
            if not target_path.exists():
                raise ValueError("target.png not found in images directory")
            self.target_button = cv2.imread(str(target_path))
            if self.target_button is None:
                raise ValueError("Failed to load target.png")
            
            self.note_icon = cv2.imread(str(self.images_dir / 'note-with-icon.png'))
            self.note_text = cv2.imread(str(self.images_dir / 'note-text.png'))
            self.composer_title = cv2.imread(str(self.images_dir / 'composer-title.png'))
            
            if self.note_icon is None or self.note_text is None or self.composer_title is None:
                raise ValueError("Failed to load auxiliary images")
        
        # Initialize monitor info
        self.monitors = self.get_monitors()
        self.logger.info(f"Found {len(self.monitors)} monitors")
        for i, m in enumerate(self.monitors):
            self.logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        
        # Add cooldown tracking
        self.last_action_time = None
        self.action_cooldown = 2.0  # seconds between actions
        
        # Add composer view tracking
        self.last_composer_change = time.time()
        self.last_composer_content = None
        self.composer_windows = []  # List of (x, y, monitor, last_change) tuples
        self.last_composer_check = 0
        self.composer_check_interval = 1.0  # Check composer position every second
        self.last_stuck_handled = None  # Initialize stuck handler timestamp
        
        # Set timeouts based on mode
        if dev_mode:
            self.logger.info("Running in development mode with shortened timeouts")
            self.stuck_timeout = 30.0  # 30 seconds in dev mode (increased from 10)
            self.stuck_handler_cooldown = 60.0  # 1 minute between stuck handlers in dev mode
        else:
            self.stuck_timeout = 70.0  # 70 seconds in production
            self.stuck_handler_cooldown = 300.0  # 5 minutes between stuck handlers

    def get_monitors(self):
        """Get list of all monitors"""
        return self.sct.monitors[1:]  # Skip the "all monitors" monitor

    def type_in_prompt(self, message, x_position):
        """Type a message into the prompt field and submit it
        Args:
            message: The text to type
            x_position: The x coordinate to align with (prompt will be 5px to the right)
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store original mouse position
            original_x, original_y = pyautogui.position()

            # Calculate prompt position:
            # - Black banner is 20px tall at bottom
            # - Prompt field is 30-70px above the banner
            monitor = self.monitors[2]  # Using monitor 2 where note was found
            screen_bottom = monitor["top"] + monitor["height"]
            prompt_y = screen_bottom - (20 + np.random.randint(35, 45))  # 35-45px above bottom banner
            prompt_x = x_position + 5 + np.random.randint(-2, 3)

            # Move to and click prompt field
            self.logger.info(f"Moving to prompt at ({prompt_x}, {prompt_y})")
            pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
            
            # Try clicking up to 2 times to get focus
            click_success = False
            for attempt in range(2):
                # Capture before-click image
                before_click = self.sct.grab({"top": prompt_y - 20, "left": prompt_x - 20, 
                                            "width": 100, "height": 60})
                before_click = np.array(before_click)
                
                # Click and wait
                pyautogui.click()
                time.sleep(1.5)  # Long delay after click
                
                # Capture after-click image
                after_click = self.sct.grab({"top": prompt_y - 20, "left": prompt_x - 20, 
                                           "width": 100, "height": 60})
                after_click = np.array(after_click)
                
                # Verify click caused a visual change
                diff = cv2.absdiff(before_click, after_click)
                if np.mean(diff) > 2:  # Visual change threshold
                    self.logger.info(f"Click successful on attempt {attempt + 1}")
                    click_success = True
                    break
                
                if attempt == 0:
                    self.logger.warning("Click may not have registered - trying again with offset...")
                    # Try clicking again with slight offset
                    prompt_y = screen_bottom - (20 + np.random.randint(35, 45))
                    prompt_x += np.random.randint(-5, 6)
                    pyautogui.moveTo(prompt_x, prompt_y, duration=0.2)
                    time.sleep(0.3)  # Small delay before retry
            
            if not click_success:
                self.logger.warning("Failed to get prompt focus after 2 attempts")
                pyautogui.moveTo(original_x, original_y, duration=0.2)
                return False
            
            # Additional delay after successful click
            time.sleep(1.0)

            # Capture response area before typing
            response_area = {
                "left": x_position - 100,
                "top": prompt_y - 300,  # Area above prompt
                "width": 200,
                "height": 200
            }
            before_type = np.array(self.sct.grab(response_area))

            # Type the message with delay between characters
            self.logger.info(f"Typing message: '{message}'")
            for char in message:
                pyautogui.write(char)
                time.sleep(0.1)  # Add small delay between characters
            time.sleep(0.5)

            # Press Command + Enter
            self.logger.info("Submitting prompt")
            pyautogui.hotkey('command', 'return')
            time.sleep(1.0)  # Wait for submission

            # Check if message appeared in response area
            max_attempts = 3
            for attempt in range(max_attempts):
                # Capture response area after submission
                after_type = np.array(self.sct.grab(response_area))
                diff = cv2.absdiff(before_type, after_type)
                if np.mean(diff) > 2:  # Response area changed
                    self.logger.info("Message submission verified - response area changed")
                    # Restore original mouse position
                    pyautogui.moveTo(original_x, original_y, duration=0.2)
                    return True
                
                if attempt < max_attempts - 1:  # Don't wait on last attempt
                    self.logger.warning(f"Message might not have sent (attempt {attempt + 1}/{max_attempts}), retrying submission...")
                    pyautogui.hotkey('command', 'return')
                    time.sleep(1.5)  # Longer wait between retries

            # Restore original mouse position
            pyautogui.moveTo(original_x, original_y, duration=0.2)
            self.logger.error("Message submission could not be verified")
            return False

        except Exception as e:
            self.logger.error(f"Error typing in prompt: {str(e)}")
            # Attempt to restore mouse position even if there was an error
            try:
                pyautogui.moveTo(original_x, original_y, duration=0.2)
            except:
                pass
            return False

    def handle_note_prompt(self, note_coords):
        """Handle clicking prompt and typing continue"""
        try:
            # Check cooldown
            if self.last_action_time and time.time() - self.last_action_time < self.action_cooldown:
                return False

            x, y = note_coords
            success = self.type_in_prompt("continue", x)
            
            if success:
                self.last_action_time = time.time()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error handling prompt: {str(e)}")
            return False

    def find_note(self):
        """Find note icon or text on any monitor"""
        try:
            # Check each monitor
            for monitor_index, monitor in enumerate(self.monitors):
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                # Convert to CV2 format
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Convert to YUV color space (better for display matching)
                img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
                note_icon_yuv = cv2.cvtColor(self.note_icon, cv2.COLOR_BGR2YUV)
                note_text_yuv = cv2.cvtColor(self.note_text, cv2.COLOR_BGR2YUV)
                
                # Try matching note icon
                result = cv2.matchTemplate(img_yuv, note_icon_yuv, cv2.TM_SQDIFF_NORMED)
                result = 1 - result  # Invert so higher values are better matches
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.8:  # Confidence threshold
                    # Calculate absolute screen coordinates
                    screen_x = monitor["left"] + max_loc[0] + self.note_icon.shape[1]//2
                    screen_y = monitor["top"] + max_loc[1] + self.note_icon.shape[0]//2
                    self.logger.info(f"Found note icon at ({screen_x}, {screen_y}) on monitor {monitor_index}")
                    return True, (screen_x, screen_y)
                
                # Try matching note text
                result = cv2.matchTemplate(img_yuv, note_text_yuv, cv2.TM_SQDIFF_NORMED)
                result = 1 - result  # Invert so higher values are better matches
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.8:  # Confidence threshold
                    # Calculate absolute screen coordinates
                    screen_x = monitor["left"] + max_loc[0] + self.note_text.shape[1]//2
                    screen_y = monitor["top"] + max_loc[1] + self.note_text.shape[0]//2
                    self.logger.info(f"Found note text at ({screen_x}, {screen_y}) on monitor {monitor_index}")
                    return True, (screen_x, screen_y)
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error finding note: {str(e)}")
            return False, None

    def find_composer(self):
        """Find all composer titles on any monitor, tracking each instance"""
        try:
            found_composers = []  # List to store all found composers
            
            # Check each monitor
            for monitor_index, monitor in enumerate(self.monitors):
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                # Convert to CV2 format
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Convert to YUV color space
                img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
                composer_yuv = cv2.cvtColor(self.composer_title, cv2.COLOR_BGR2YUV)
                
                # Find all matches above threshold
                result = cv2.matchTemplate(img_yuv, composer_yuv, cv2.TM_SQDIFF_NORMED)
                result = 1 - result  # Invert so higher values are better matches
                locations = np.where(result >= 0.7)  # Lower threshold to 0.7 to catch more matches
                
                # Group nearby matches
                grouped_matches = []
                for pt in zip(*locations[::-1]):  # Check each match
                    # Calculate absolute screen coordinates
                    screen_x = monitor["left"] + pt[0] + self.composer_title.shape[1]//2
                    screen_y = monitor["top"] + pt[1] + self.composer_title.shape[0]//2
                    
                    # Check if this match is close to an existing group
                    found_group = False
                    for group in grouped_matches:
                        if abs(screen_x - group[0]) < 3 and abs(screen_y - group[1]) < 3:
                            # Average the positions
                            group[0] = (group[0] + screen_x) / 2
                            group[1] = (group[1] + screen_y) / 2
                            group[2] += 1  # Increment match count
                            found_group = True
                            break
                    
                    if not found_group:
                        # Start new group with count of 1
                        grouped_matches.append([screen_x, screen_y, 1, monitor])
                
                # Add the strongest match from each group
                for group in grouped_matches:
                    x, y, count, mon = group
                    # Only add groups with strong confidence (multiple matches)
                    if count >= 2:
                        found_composers.append((int(x), int(y), mon))
                        self.logger.info(f"Found composer window at ({int(x)}, {int(y)}) on monitor {monitor_index}")
            
            if found_composers:
                # Sort by y coordinate (lowest/bottom-most first)
                found_composers.sort(key=lambda x: x[1], reverse=True)
                self.logger.info(f"Total unique composer windows found: {len(found_composers)}")
                return True, found_composers
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error finding composer: {str(e)}")
            return False, None

    def update_composer_position(self):
        """Update all composer positions and track their changes"""
        current_time = time.time()
        if current_time - self.last_composer_check >= self.composer_check_interval:
            found, composers = self.find_composer()
            self.last_composer_check = current_time
            
            if found:
                # Update existing composers or add new ones
                new_composers = []
                for x, y, monitor in composers:
                    # Check if this composer exists in our list (within 10px)
                    existing = None
                    for old_x, old_y, old_monitor, last_change in self.composer_windows:
                        if abs(x - old_x) < 10 and abs(y - old_y) < 10:
                            existing = (old_x, old_y, old_monitor, last_change)
                            break
                    
                    if existing:
                        # Update position if changed significantly
                        if abs(x - existing[0]) > 5 or abs(y - existing[1]) > 5:
                            self.logger.info(f"Composer window moved: ({existing[0]}, {existing[1]}) -> ({x}, {y})")
                            new_composers.append((x, y, monitor, existing[3]))  # Keep last_change time
                        else:
                            new_composers.append(existing)  # Keep existing data
                    else:
                        # New composer window found
                        self.logger.info(f"New composer window found at ({x}, {y})")
                        new_composers.append((x, y, monitor, current_time))
                
                # Update the list of tracked composers
                self.composer_windows = new_composers
                return True
            else:
                if self.composer_windows:  # Lost track of all composers
                    self.logger.warning("Lost track of all composer windows")
                self.composer_windows = []
                return False
        return bool(self.composer_windows)

    def check_composer_stuck(self):
        """Check if any composer view is stuck (unchanged for too long)"""
        try:
            # Update composer positions regularly
            if not self.update_composer_position() or not self.composer_windows:
                return False

            current_time = time.time()
            stuck_composers = []

            # Check each composer window
            for x, y, monitor, last_change in self.composer_windows:
                # Calculate response area coordinates (200px wide, 150px above prompt)
                screen_bottom = monitor["top"] + monitor["height"]
                response_area = {
                    "left": x - 100,  # Center around composer
                    "top": screen_bottom - 170,     # 150px above prompt + 20px banner
                    "width": 200,
                    "height": 150
                }

                # Capture response area
                current_content = np.array(self.sct.grab(response_area))

                # Compare with previous content if exists
                if self.last_composer_content is not None:
                    diff = cv2.absdiff(current_content, self.last_composer_content)
                    if np.mean(diff) > 2:  # Content changed
                        # Update the last change time for this composer
                        idx = self.composer_windows.index((x, y, monitor, last_change))
                        self.composer_windows[idx] = (x, y, monitor, current_time)
                        continue

                # Check if stuck timeout reached
                time_since_change = current_time - last_change
                if time_since_change >= self.stuck_timeout:
                    self.logger.info(f"Composer view at ({x}, {y}) stuck for {time_since_change:.1f} seconds")
                    stuck_composers.append((x, y, monitor))

            # Return True if any composer is stuck, along with the most recently active stuck composer
            if stuck_composers:
                # Sort by last_change time (most recent first)
                stuck_composers.sort(key=lambda c: next(w[3] for w in self.composer_windows if w[0] == c[0] and w[1] == c[1]), reverse=True)
                self.composer_x, self.composer_y = stuck_composers[0][:2]  # Use most recent for handling
                self.current_monitor = stuck_composers[0][2]
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking composer stuck: {str(e)}")
            return False

    def handle_stuck_composer(self):
        """Handle stuck composer by sending continuation message"""
        try:
            if self.composer_x is None:
                return False

            # Check if we're still in cooldown (only in production mode)
            if not self.dev_mode and self.last_stuck_handled and time.time() - self.last_stuck_handled < self.stuck_handler_cooldown:
                self.logger.info("Skipping stuck handler (in cooldown)")
                return False

            message = "It looks like you stopped - please continue by reviewing the cursor-instructions/ folder. Don't forget to commit your work to a new branch before you start a new topic"
            success = self.type_in_prompt(message, self.composer_x)
            if success:
                self.last_composer_change = time.time()  # Reset stuck timer
                self.last_stuck_handled = time.time()    # Update last handled time
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error handling stuck composer: {str(e)}")
            return False

    def find_target(self):
        """Find all target buttons on monitor 0"""
        try:
            found_targets = []  # List to store all found targets
            
            # Only check monitor 0
            monitor = self.monitors[0]
            monitor_index = 0
            
            # Capture monitor
            screenshot = self.sct.grab(monitor)
            # Convert to CV2 format
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Convert to YUV color space (better for display matching)
            img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
            target_yuv = cv2.cvtColor(self.target_button, cv2.COLOR_BGR2YUV)
            
            # Try both normal and inverted target image
            target_yuv_inv = cv2.bitwise_not(target_yuv)
            target_h, target_w = target_yuv.shape[:2]
            
            # Create debug image if in dev mode
            if self.dev_mode:
                debug_img = img_bgr.copy()
            
            # Find matches for both normal and inverted target
            results = []
            for target_img in [target_yuv, target_yuv_inv]:
                result = cv2.matchTemplate(img_yuv, target_img, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= 0.70)  # Lower threshold for monitor 0
                for pt in zip(*locations[::-1]):
                    results.append((pt, result[pt[1], pt[0]]))
            
            # Group nearby matches
            grouped_matches = []
            for pt, conf in results:
                # Calculate absolute screen coordinates
                screen_x = monitor["left"] + pt[0] + target_w//2
                screen_y = monitor["top"] + pt[1] + target_h//2
                
                # Additional verification - check if target dimensions match exactly
                if pt[1]+target_h > img_yuv.shape[0] or pt[0]+target_w > img_yuv.shape[1]:
                    continue
                    
                target_region = img_yuv[pt[1]:pt[1]+target_h, pt[0]:pt[0]+target_w]
                if target_region.shape != target_yuv.shape:  # Require exact size match
                    continue
                
                # Draw match on debug image if in dev mode
                if self.dev_mode:
                    cv2.rectangle(debug_img, 
                                (pt[0], pt[1]), 
                                (pt[0] + target_w, pt[1] + target_h), 
                                (0, 255, 0), 2)
                    cv2.putText(debug_img, 
                              f"{conf:.2f}", 
                              (pt[0], pt[1] - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Check if this match is close to an existing group
                found_group = False
                for group in grouped_matches:
                    # Only group matches that are close together
                    local_x = pt[0] + target_w//2  # Local coordinates within monitor
                    local_y = pt[1] + target_h//2
                    group_local_x = group[0] - monitor["left"]  # Convert group coords to local
                    group_local_y = group[1] - monitor["top"]
                    
                    if abs(local_x - group_local_x) < 5 and abs(local_y - group_local_y) < 5:  # Slightly relaxed grouping
                        # Average the positions (in screen coordinates)
                        group[0] = (group[0] * group[2] + screen_x) / (group[2] + 1)
                        group[1] = (group[1] * group[2] + screen_y) / (group[2] + 1)
                        group[2] += 1  # Increment match count
                        group[3] = max(group[3], conf)  # Keep highest confidence
                        found_group = True
                        break
                
                if not found_group:
                    # Start new group with count of 1 (using screen coordinates)
                    grouped_matches.append([screen_x, screen_y, 1, conf])
            
            # Add matches that meet minimum confidence
            for group in grouped_matches:
                x, y, count, confidence = group
                # Only add groups with reasonable confidence
                if count >= 1 and confidence >= 0.70:  # Lower threshold for monitor 0
                    found_targets.append((int(x), int(y)))
                    self.logger.info(f"Found target button at ({int(x)}, {int(y)}) on monitor {monitor_index} with confidence {confidence:.3f}")
                    
                    # Draw final match on debug image if in dev mode
                    if self.dev_mode:
                        local_x = int(x - monitor["left"])
                        local_y = int(y - monitor["top"])
                        cv2.circle(debug_img, (local_x, local_y), 10, (0, 0, 255), 2)
            
            # Save debug image if in dev mode
            if self.dev_mode:
                debug_dir = Path('temp/debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                cv2.imwrite(str(debug_dir / f'target_search_monitor{monitor_index}_{timestamp}.png'), debug_img)
            
            if found_targets:
                # Sort by y coordinate (top-most first)
                found_targets.sort(key=lambda x: x[1])
                self.logger.info(f"Total unique target buttons found: {len(found_targets)}")
                return True, found_targets  # Return all targets
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error finding target: {str(e)}")
            return False, None

    def handle_target_click(self, target_coords):
        """Click the target button"""
        try:
            # Check cooldown
            if self.last_action_time and time.time() - self.last_action_time < self.action_cooldown:
                return False

            # Store original mouse position
            original_x, original_y = pyautogui.position()
            
            x, y = target_coords
            
            # Move to target
            self.logger.info(f"Moving to target at ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.2)
            
            success = False
            # Try clicking up to 2 times
            for attempt in range(2):
                # Capture before-click image
                before_click = self.sct.grab({"top": y - 10, "left": x - 10, 
                                            "width": 20, "height": 20})
                before_click = np.array(before_click)
                
                # Click and wait
                pyautogui.click()
                time.sleep(0.5)
                
                # Capture after-click image
                after_click = self.sct.grab({"top": y - 10, "left": x - 10, 
                                           "width": 20, "height": 20})
                after_click = np.array(after_click)
                
                # Verify click caused a visual change
                diff = cv2.absdiff(before_click, after_click)
                if np.mean(diff) > 2:  # Visual change threshold
                    self.logger.info(f"Target click successful on attempt {attempt + 1} - visual change detected")
                    self.last_action_time = time.time()
                    success = True
                    break
                
                if attempt == 0:
                    self.logger.warning("No visual change detected, trying second click...")
                    time.sleep(0.3)  # Additional delay before retry
            
            if not success:
                self.logger.warning("Target click unsuccessful after 2 attempts - no visual change detected")

            # Restore original mouse position
            pyautogui.moveTo(original_x, original_y, duration=0.2)
            return success

        except Exception as e:
            self.logger.error(f"Error clicking target: {str(e)}")
            return False

    def calibrate_target(self):
        """Calibrate by capturing new target button image"""
        self.logger.info("Starting target button calibration...")
        self.logger.info("Please calibrate for each monitor that has a target button.")
        
        # Create images directory if it doesn't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        for monitor_index, monitor in enumerate(self.monitors):
            while True:
                response = input(f"\nCalibrate monitor {monitor_index} ({monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']}))? [y/N/q]: ").lower()
                if response == 'q':
                    return True
                if response != 'y':
                    continue
                    
                self.logger.info(f"Please position your cursor at the CENTER of the target button on monitor {monitor_index} and press Enter")
                input()
                
                # Get cursor position
                x, y = pyautogui.position()
                self.logger.info(f"Cursor position: ({x}, {y})")
                
                # Verify cursor is on the correct monitor
                if not (monitor["left"] <= x < monitor["left"] + monitor["width"] and 
                       monitor["top"] <= y < monitor["top"] + monitor["height"]):
                    self.logger.warning(f"Cursor position ({x}, {y}) is not on monitor {monitor_index}! Please try again.")
                    continue
                
                # Capture region centered around cursor - using smaller region
                region = {
                    'left': x - 15,  # Smaller region, centered
                    'top': y - 15,   # Smaller region, centered
                    'width': 30,     # Total width 30px
                    'height': 30     # Total height 30px
                }
                
                # Capture screenshot
                screenshot = self.sct.grab(region)
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Save target image with monitor index
                target_path = self.images_dir / f'target_{monitor_index}.png'
                cv2.imwrite(str(target_path), img_bgr)
                self.logger.info(f"Saved target button image to {target_path}")
                
                # Verify image was saved
                if not target_path.exists():
                    raise RuntimeError(f"Failed to save target button image for monitor {monitor_index}")
                
                break  # Successfully calibrated this monitor
        
        self.logger.info("Target button calibration complete")
        return True

    def cleanup(self):
        """Clean up resources"""
        try:
            self.running = False
            if hasattr(self, 'sct'):
                self.sct.close()
            self.logger.info("Resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def run(self):
        """Run continuous monitoring with correct priorities"""
        self.logger.info("Starting Monitoring")
        self.logger.info("Press Ctrl+C to stop")
        
        self.running = True
        try:
            while self.running:
                # PRIORITY 1: Always check for target button first
                target_found, targets = self.find_target()
                if target_found:
                    # Handle all found targets
                    for target_coords in targets:
                        self.logger.info(f"Found target button at coordinates: {target_coords}")
                        if self.handle_target_click(target_coords):
                            self.logger.info("Successfully clicked target button")
                            time.sleep(0.5)  # Small delay between clicks
                        else:
                            self.logger.info("Target click failed or skipped (cooldown)")
                    continue  # Immediately start next cycle to check for more targets
                
                # Get current state of auxiliary features
                composer_found = self.update_composer_position()
                note_found, note_coords = self.find_note()
                is_stuck = False
                
                # Only check for stuck if we have a composer and no target was found
                if composer_found and not target_found:
                    is_stuck = self.check_composer_stuck()
                
                # Handle auxiliary features if no target was found
                if not target_found:
                    # Priority 2: Handle notes
                    if note_found:
                        self.logger.info(f"Found note at coordinates: {note_coords}")
                        if self.handle_note_prompt(note_coords):
                            self.logger.info("Successfully handled note prompt")
                    
                    # Priority 3: Handle stuck composer
                    if is_stuck:
                        self.logger.info(f"Composer stuck for {time.time() - self.last_composer_change:.1f} seconds")
                        if self.handle_stuck_composer():
                            self.logger.info("Successfully handled stuck composer")
                
                # Very short delay to prevent CPU overload but ensure we catch targets
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
        finally:
            self.cleanup()

    def run_target_test(self):
        """Run target detection test mode"""
        self.logger.info("Starting target detection test mode")
        self.logger.info("Press Ctrl+C to stop")
        
        self.running = True
        try:
            while self.running:
                target_found, targets = self.find_target()
                if target_found:
                    # Handle all found targets
                    for target_coords in targets:
                        self.logger.info(f"Found target button at coordinates: {target_coords}")
                        if self.handle_target_click(target_coords):
                            self.logger.info("Successfully clicked target button")
                            time.sleep(0.5)  # Small delay between clicks
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.logger.info("Target test stopped by user")
        finally:
            self.cleanup()

    def run_note_test(self):
        """Run note detection test mode"""
        self.logger.info("Starting note detection test mode")
        self.logger.info("Press Ctrl+C to stop")
        
        self.running = True
        try:
            while self.running:
                note_found, note_coords = self.find_note()
                if note_found:
                    self.logger.info(f"Found note at coordinates: {note_coords}")
                    if self.handle_note_prompt(note_coords):
                        self.logger.info("Successfully handled note prompt")
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.logger.info("Note test stopped by user")
        finally:
            self.cleanup()

    def run_stuck_test(self):
        """Run stuck detection test mode"""
        self.logger.info("Starting stuck detection test mode")
        self.logger.info("Press Ctrl+C to stop")
        
        self.running = True
        try:
            while self.running:
                composer_found = self.update_composer_position()
                if composer_found:
                    is_stuck = self.check_composer_stuck()
                    if is_stuck:
                        self.logger.info(f"Composer stuck for {time.time() - self.last_composer_change:.1f} seconds")
                        if self.handle_stuck_composer():
                            self.logger.info("Successfully handled stuck composer")
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.logger.info("Stuck test stopped by user")
        finally:
            self.cleanup()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev', action='store_true', help='Run in development mode with shorter timeouts')
    parser.add_argument('--calibrate', action='store_true', help='Run calibration mode')
    parser.add_argument('--test-target', action='store_true', help='Test target button detection only')
    parser.add_argument('--test-note', action='store_true', help='Test note detection only')
    parser.add_argument('--test-stuck', action='store_true', help='Test stuck detection only')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    detector = None
    try:
        detector = NoteDetector(dev_mode=args.dev, calibrate=args.calibrate)
        
        if args.calibrate:
            detector.calibrate_target()
            return
            
        if args.test_target:
            detector.run_target_test()
            return
            
        if args.test_note:
            detector.run_note_test()
            return
            
        if args.test_stuck:
            detector.run_stuck_test()
            return
        
        detector.run()
        
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise
    finally:
        if detector:
            detector.cleanup()

if __name__ == "__main__":
    main() 