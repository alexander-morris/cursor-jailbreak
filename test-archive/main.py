import os
import sys
import time
import signal
import argparse
from datetime import datetime
import pyautogui
import numpy as np
from PIL import Image

from image_matcher import ImageMatcher
from error_recovery import ErrorRecoveryHandler
from logging_config import setup_logging, log_error_with_context, log_match_result, save_debug_image

class ClickBot:
    def __init__(self, debug=False, interval=3.0, confidence_threshold=0.8):
        # Initialize logging
        self.logger = setup_logging('clickbot', debug)
        self.debug = debug
        self.interval = interval
        self.confidence_threshold = confidence_threshold
        self.running = False
        self.last_click_time = 0
        self.click_cooldown = 1.0  # Minimum time between clicks
        
        # Initialize components
        self.matcher = ImageMatcher(debug)
        self.error_handler = ErrorRecoveryHandler(debug)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
        
        self.logger.info(f"ClickBot initialized - Debug: {debug}, Interval: {interval}s, "
                        f"Confidence Threshold: {confidence_threshold}")

    def find_cursor_monitor(self):
        """Find the monitor containing the Cursor application."""
        try:
            ref_image_path = os.path.join(os.path.dirname(__file__), 'images', 'cursor-screen-head.png')
            if not os.path.exists(ref_image_path):
                raise FileNotFoundError(f"Reference image not found: {ref_image_path}")

            ref_image = Image.open(ref_image_path)
            monitors = self.matcher.get_monitors()
            
            best_match = None
            best_confidence = 0
            
            for i, monitor in enumerate(monitors):
                # Only capture top 50 pixels of each monitor
                top_region = {
                    'left': monitor['left'],
                    'top': monitor['top'],
                    'width': monitor['width'],
                    'height': 50
                }
                
                screen = self.matcher.capture_screen(top_region)
                match = self.matcher.find_template(screen, ref_image)
                
                if match and match['confidence'] > best_confidence:
                    best_confidence = match['confidence']
                    best_match = {**monitor, 'match': match}
                
                if self.debug:
                    self.logger.debug(f"Monitor {i} scan - Confidence: {match['confidence'] if match else 0:.4f}")
            
            if best_match and best_confidence > 0.7:
                self.logger.info(f"Found Cursor monitor - Confidence: {best_confidence:.4f}")
                return best_match
            
            raise RuntimeError("Could not find Cursor application window")
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Monitor detection failed")
            return None

    def process_matches(self, matches, screen):
        """Process and validate matches, handling clicks if appropriate."""
        try:
            if not matches:
                return

            current_time = time.time()
            for match in matches:
                if match['confidence'] < self.confidence_threshold:
                    if self.debug:
                        log_match_result(self.logger, match, match['confidence'])
                    continue

                if current_time - self.last_click_time < self.click_cooldown:
                    self.logger.debug("Click cooldown active")
                    continue

                self.logger.info(f"High confidence match found: {match['confidence']:.4f} "
                               f"at ({match['x']}, {match['y']})")

                if self.debug:
                    # Save annotated image
                    annotated = screen.copy()
                    self.matcher.draw_match(annotated, match)
                    save_debug_image(annotated, 'match', 'annotated_matches')
                else:
                    # Perform click
                    pyautogui.click(match['x'], match['y'])
                    self.last_click_time = current_time
                    self.logger.info(f"Clicked at ({match['x']}, {match['y']})")

        except Exception as e:
            log_error_with_context(self.logger, e, "Match processing failed")

    def handle_error_state(self, screen):
        """Handle potential error states and perform recovery if needed."""
        try:
            if self.error_handler.handle_error_case(screen):
                self.logger.info("Error state handled successfully")
                return True
            else:
                self.logger.error("Failed to handle error state")
                return False
        except Exception as e:
            log_error_with_context(self.logger, e, "Error handling failed")
            return False

    def run(self):
        """Main bot loop with proper error handling and monitoring."""
        self.running = True
        self.logger.info("Starting ClickBot")
        
        try:
            monitor = self.find_cursor_monitor()
            if not monitor:
                raise RuntimeError("Failed to find Cursor monitor")

            last_monitor_check = time.time()
            monitor_check_interval = 300  # Check monitor every 5 minutes
            
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Periodically recheck monitor
                    if current_time - last_monitor_check > monitor_check_interval:
                        monitor = self.find_cursor_monitor()
                        if not monitor:
                            raise RuntimeError("Lost Cursor monitor")
                        last_monitor_check = current_time
                    
                    # Capture screen and check for errors first
                    screen = self.matcher.capture_screen(monitor)
                    
                    # Handle any error states before proceeding
                    if not self.handle_error_state(screen):
                        self.logger.warning("Error state detected but recovery failed")
                        time.sleep(self.interval)
                        continue
                    
                    # Proceed with normal operation
                    matches = self.matcher.find_all_matches(screen)
                    self.process_matches(matches, screen)
                    
                    # Status update every 30 seconds
                    if int(current_time) % 30 == 0:
                        self.logger.info("Bot running - monitoring for matches")
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    log_error_with_context(self.logger, e, "Error in main loop")
                    time.sleep(self.interval)  # Continue with next iteration
                    
        except Exception as e:
            log_error_with_context(self.logger, e, "Fatal error")
            self.stop()
            sys.exit(1)

    def stop(self):
        """Clean shutdown of the bot."""
        self.logger.info("Stopping ClickBot")
        self.running = False

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signals gracefully."""
        self.logger.info(f"Received signal {signum}")
        self.stop()

def main():
    parser = argparse.ArgumentParser(description='ClickBot - Automated UI interaction')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--interval', type=float, default=3.0,
                       help='Scan interval in seconds (default: 3.0)')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Minimum confidence threshold (default: 0.8)')
    args = parser.parse_args()

    bot = ClickBot(
        debug=args.debug,
        interval=args.interval,
        confidence_threshold=args.confidence
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.logger.info("Keyboard interrupt received")
    finally:
        bot.stop()

if __name__ == '__main__':
    main() 