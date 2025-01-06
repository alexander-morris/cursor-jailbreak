import os
import unittest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

from main import ClickBot
from image_matcher import ImageMatcher
from logging_config import setup_logging

class TestClickBot(unittest.TestCase):
    def setUp(self):
        self.logger = setup_logging('test_clickbot', debug=True)
        self.bot = ClickBot(debug=True, interval=0.1)
        
        # Create test images directory
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'test_images')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # Create a test image
        self.test_image = Image.new('RGB', (100, 100), color='white')
        self.test_image_path = os.path.join(self.test_images_dir, 'test.png')
        self.test_image.save(self.test_image_path)

    def tearDown(self):
        # Clean up test files
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        if os.path.exists(self.test_images_dir):
            os.rmdir(self.test_images_dir)

    @patch('main.ImageMatcher')
    def test_monitor_detection(self, mock_matcher):
        # Mock monitor detection
        mock_monitor = {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}
        mock_matcher.return_value.get_monitors.return_value = [mock_monitor]
        mock_matcher.return_value.find_template.return_value = {'confidence': 0.9}
        
        # Test monitor detection
        monitor = self.bot.find_cursor_monitor()
        self.assertIsNotNone(monitor)
        self.assertEqual(monitor['width'], 1920)

    @patch('main.ImageMatcher')
    def test_match_processing(self, mock_matcher):
        # Mock matches
        matches = [
            {'confidence': 0.9, 'x': 100, 'y': 100},
            {'confidence': 0.7, 'x': 200, 'y': 200}
        ]
        
        # Test match processing
        with patch('pyautogui.click') as mock_click:
            self.bot.process_matches(matches, self.test_image)
            mock_click.assert_called_once_with(100, 100)

    def test_error_handling(self):
        # Test invalid monitor
        with patch('main.ImageMatcher') as mock_matcher:
            mock_matcher.return_value.get_monitors.return_value = []
            monitor = self.bot.find_cursor_monitor()
            self.assertIsNone(monitor)

    @patch('main.ImageMatcher')
    def test_debug_mode(self, mock_matcher):
        # Create bot in debug mode
        debug_bot = ClickBot(debug=True, interval=0.1)
        
        # Mock matches
        matches = [{'confidence': 0.9, 'x': 100, 'y': 100}]
        
        # Test debug output
        with patch('pyautogui.click') as mock_click:
            debug_bot.process_matches(matches, self.test_image)
            mock_click.assert_not_called()  # Should not click in debug mode

class TestImageMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = ImageMatcher(debug=True)
        
        # Create test images
        self.screen = Image.new('RGB', (200, 200), color='white')
        self.template = Image.new('RGB', (50, 50), color='white')
        
        # Draw something unique in template
        self.template.putpixel((25, 25), (255, 0, 0))

    def test_template_loading(self):
        # Save test template
        template_path = 'test_template.png'
        self.template.save(template_path)
        
        # Test template loading
        loaded_template = self.matcher.load_template(template_path)
        self.assertIsNotNone(loaded_template)
        
        # Clean up
        os.remove(template_path)

    def test_template_matching(self):
        # Create screen with template in it
        self.screen.paste(self.template, (75, 75))
        
        # Test matching
        match = self.matcher.find_template(self.screen, self.template)
        self.assertIsNotNone(match)
        self.assertGreater(match['confidence'], 0.8)

    def test_error_handling(self):
        # Test invalid template
        match = self.matcher.find_template(self.screen, None)
        self.assertIsNone(match)
        
        # Test invalid screen
        match = self.matcher.find_template(None, self.template)
        self.assertIsNone(match)

if __name__ == '__main__':
    unittest.main() 