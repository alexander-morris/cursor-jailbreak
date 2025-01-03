import os
import mss
import mss.tools
import numpy as np
import cv2
from PIL import Image, ImageDraw
from logging_config import setup_logging, log_error_with_context, save_debug_image

class ImageMatcher:
    def __init__(self, debug=False):
        self.logger = setup_logging('image_matcher', debug)
        self.debug = debug
        self.screen = mss.mss()
        self.template_cache = {}
        self.logger.info("ImageMatcher initialized")

    def get_monitors(self):
        """Get list of available monitors with error handling."""
        try:
            monitors = self.screen.monitors[1:]  # Skip first monitor (represents "all monitors")
            self.logger.debug(f"Found {len(monitors)} monitors")
            return monitors
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to get monitors")
            return []

    def capture_screen(self, region):
        """Capture screen region with error handling and debug output."""
        try:
            screenshot = self.screen.grab(region)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            if self.debug:
                path = save_debug_image(img, 'screen_capture', 'debug_output')
                self.logger.debug(f"Saved screen capture: {path}")
            
            return img
        except Exception as e:
            log_error_with_context(self.logger, e, f"Screen capture failed for region: {region}")
            return None

    def load_template(self, template_path):
        """Load and cache template images with error handling."""
        try:
            if template_path not in self.template_cache:
                if not os.path.exists(template_path):
                    raise FileNotFoundError(f"Template not found: {template_path}")
                
                template = Image.open(template_path)
                self.template_cache[template_path] = template
                self.logger.debug(f"Loaded template: {template_path}")
            
            return self.template_cache[template_path]
        except Exception as e:
            log_error_with_context(self.logger, e, f"Failed to load template: {template_path}")
            return None

    def find_template(self, screen_img, template_img, threshold=0.8):
        """Find template in screen image with error handling and debug output."""
        try:
            if screen_img is None or template_img is None:
                return None

            # Convert images to numpy arrays
            screen_np = np.array(screen_img)
            template_np = np.array(template_img)

            # Convert to grayscale
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            template_gray = cv2.cvtColor(template_np, cv2.COLOR_RGB2GRAY)

            # Perform template matching
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                match = {
                    'confidence': max_val,
                    'x': max_loc[0] + template_gray.shape[1] // 2,
                    'y': max_loc[1] + template_gray.shape[0] // 2,
                    'width': template_gray.shape[1],
                    'height': template_gray.shape[0]
                }
                
                if self.debug:
                    self.logger.debug(f"Match found - Confidence: {max_val:.4f} at ({match['x']}, {match['y']})")
                
                return match
            
            return None

        except Exception as e:
            log_error_with_context(self.logger, e, "Template matching failed")
            return None

    def find_all_matches(self, screen_img, threshold=0.8):
        """Find all template matches in screen image."""
        try:
            matches = []
            template_dir = os.path.join(os.path.dirname(__file__), 'images')
            
            if not os.path.exists(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")

            for template_file in os.listdir(template_dir):
                if template_file.endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(template_dir, template_file)
                    template_img = self.load_template(template_path)
                    
                    if template_img:
                        match = self.find_template(screen_img, template_img, threshold)
                        if match:
                            matches.append(match)

            if self.debug:
                self.logger.debug(f"Found {len(matches)} matches above threshold {threshold}")

            return matches

        except Exception as e:
            log_error_with_context(self.logger, e, "Finding all matches failed")
            return []

    def draw_match(self, image, match, color='red', text_color='white'):
        """Draw match visualization on image with error handling."""
        try:
            draw = ImageDraw.Draw(image)
            
            # Draw rectangle around match
            x = match['x'] - match['width'] // 2
            y = match['y'] - match['height'] // 2
            draw.rectangle(
                [x, y, x + match['width'], y + match['height']],
                outline=color,
                width=2
            )
            
            # Draw confidence score
            text = f"{match['confidence']:.4f}"
            draw.text((x, y - 20), text, fill=text_color)
            
            # Draw center point
            draw.ellipse(
                [match['x'] - 2, match['y'] - 2, match['x'] + 2, match['y'] + 2],
                fill=color
            )
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Drawing match visualization failed") 