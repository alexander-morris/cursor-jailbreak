import os
import time
import pyautogui
from PIL import Image
import logging

class ErrorRecoveryHandler:
    def __init__(self, debug=False):
        self.debug = debug
        self.error_indicators = ['note-icon.png']
        self.error_threshold = 0.8  # Confidence threshold for error detection
        self.max_retries = 3  # Maximum number of retries for recovery
        
        # Set up logging
        log_dir = os.path.join(os.path.dirname(__file__), "temp", "logs")
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO if not debug else logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'error_recovery.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('error_recovery')
        
        # Load reference images
        self.images_dir = os.path.join(os.path.dirname(__file__), 'images')
        self.error_images = {}  # Initialize empty, load on demand

    def _load_error_images(self):
        """Load error indicator images."""
        images = {}
        for img_name in self.error_indicators:
            path = os.path.join(self.images_dir, img_name)
            if os.path.exists(path):
                images[img_name] = Image.open(path)
            else:
                self.logger.warning(f"Error indicator image not found: {img_name}")
        return images

    def _ensure_images_loaded(self):
        """Ensure all necessary images are loaded."""
        if not self.error_images:
            self.error_images = self._load_error_images()

    def perform_recovery(self):
        """Perform the recovery sequence by typing 'continue'."""
        self.logger.info("Starting error recovery sequence")
        
        try:
            # Type 'continue' and press Enter
            self.logger.info("Typing 'continue'")
            pyautogui.write('continue')
            time.sleep(0.2)  # Wait after typing
            
            self.logger.info("Pressing Enter")
            pyautogui.press('enter')
            
            self.logger.info("Recovery sequence completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during recovery sequence: {str(e)}")
            return False

    def check_for_note(self, screen):
        """Check if note icon is present on screen."""
        self._ensure_images_loaded()
        
        try:
            note_icon = self.error_images.get('note-icon.png')
            
            if not note_icon:
                self.logger.error("Note icon template not loaded")
                return False

            # Convert screen to PIL Image if it's not already
            if not isinstance(screen, Image.Image):
                screen = Image.fromarray(screen)

            # Use PyAutoGUI's locate function which returns None if not found
            location = pyautogui.locate(note_icon, screen, confidence=self.error_threshold)
            
            if location:
                self.logger.info(f"Found note icon at {location}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Error checking for note icon: {str(e)}")
            return False

    def handle_error_case(self, screen):
        """Main error handling flow."""
        if self.check_for_note(screen):
            self.logger.info("Detected note icon")
            return self.perform_recovery()
        return False 