import os
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
from error_recovery import ErrorRecoveryHandler

class TestErrorRecoveryHandler(unittest.TestCase):
    def setUp(self):
        self.handler = ErrorRecoveryHandler(debug=True)
        
        # Create test images directory
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'test_images')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # Create test images
        self.screen = Image.new('RGB', (800, 600), color='white')
        self.error_icon = Image.new('RGB', (32, 32), color='red')
        self.note_text = Image.new('RGB', (100, 20), color='yellow')
        self.footer = Image.new('RGB', (200, 50), color='blue')
        
        # Save test images
        self.error_icon_path = os.path.join(self.test_images_dir, 'error-icon.png')
        self.note_text_path = os.path.join(self.test_images_dir, 'note-text.png')
        self.footer_path = os.path.join(self.test_images_dir, 'agent-buttons-footer.png')
        
        self.error_icon.save(self.error_icon_path)
        self.note_text.save(self.note_text_path)
        self.footer.save(self.footer_path)

    def tearDown(self):
        # Clean up test files
        for path in [self.error_icon_path, self.note_text_path, self.footer_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_images_dir):
            os.rmdir(self.test_images_dir)

    @patch('error_recovery.ImageMatcher')
    def test_multiple_error_detection(self, mock_matcher):
        # Mock multiple error icon detections
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 100,
            'y': 100
        }
        
        # Mock find_all_error_matches
        self.handler.find_all_error_matches = MagicMock(return_value=[
            {'confidence': 0.9, 'x': 100, 'y': 100},
            {'confidence': 0.85, 'x': 300, 'y': 200}
        ])
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertTrue(has_error)
        self.assertEqual(error_type, 'multiple_error_icons')

    @patch('error_recovery.ImageMatcher')
    def test_single_error_no_trigger(self, mock_matcher):
        # Mock single error icon detection (should not trigger recovery)
        self.handler.find_all_error_matches = MagicMock(return_value=[
            {'confidence': 0.9, 'x': 100, 'y': 100}
        ])
        mock_matcher.return_value.find_template.return_value = None  # No note text
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertFalse(has_error)
        self.assertIsNone(error_type)

    @patch('error_recovery.ImageMatcher')
    def test_note_text_trigger(self, mock_matcher):
        # Mock note text detection with single error icon
        self.handler.find_all_error_matches = MagicMock(return_value=[
            {'confidence': 0.9, 'x': 100, 'y': 100}
        ])
        
        # Replace the ImageMatcher instance with our mock
        self.handler.matcher = mock_matcher.return_value
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 200,
            'y': 200
        }
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertTrue(has_error)
        self.assertEqual(error_type, 'note_text')

    @patch('error_recovery.ImageMatcher')
    def test_low_confidence_matches(self, mock_matcher):
        # Mock multiple error icons but with low confidence
        self.handler.find_all_error_matches = MagicMock(return_value=[
            {'confidence': 0.7, 'x': 100, 'y': 100},
            {'confidence': 0.6, 'x': 300, 'y': 200}
        ])
        mock_matcher.return_value.find_template.return_value = None
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertFalse(has_error)
        self.assertIsNone(error_type)

    @patch('error_recovery.ImageMatcher')
    def test_overlapping_matches_filtering(self, mock_matcher):
        # Test that overlapping matches are filtered out
        screen = Image.new('RGB', (800, 600))
        error_icon = Image.new('RGB', (32, 32))
        
        # Create two matches that overlap
        matches = [
            {'confidence': 0.9, 'x': 100, 'y': 100},
            {'confidence': 0.85, 'x': 110, 'y': 105}  # Overlapping with first match
        ]
        
        def mock_find_template(*args, **kwargs):
            return matches[0]  # Return first match
        
        mock_matcher.return_value.find_template = mock_find_template
        
        result = self.handler.find_all_error_matches(screen, error_icon)
        self.assertEqual(len(result), 1)  # Should only keep one of the overlapping matches

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_recovery_sequence(self, mock_press, mock_write, mock_click, mock_matcher):
        # Mock footer detection
        mock_matcher.return_value.find_template = MagicMock(return_value={
            'confidence': 0.9,
            'x': 400,
            'y': 500
        })
        
        # Replace the ImageMatcher instance with our mock
        self.handler.matcher = mock_matcher.return_value
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        success = self.handler.perform_recovery(self.screen)
        
        self.assertTrue(success)
        mock_click.assert_called_once_with(400, 470)  # y - 30
        mock_write.assert_called_once_with('continue')
        mock_press.assert_called_once_with('enter')

    @patch('error_recovery.ImageMatcher')
    def test_recovery_target_not_found(self, mock_matcher):
        # Mock footer not found
        mock_matcher.return_value.find_template.return_value = None
        
        success = self.handler.perform_recovery(self.screen)
        self.assertFalse(success)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    def test_recovery_click_failure(self, mock_click, mock_matcher):
        # Mock footer detection but click failure
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 400,
            'y': 500
        }
        mock_click.side_effect = Exception("Click failed")
        
        success = self.handler.perform_recovery(self.screen)
        self.assertFalse(success)

    def test_error_image_loading(self):
        # Test with missing images
        handler = ErrorRecoveryHandler(debug=True)
        self.assertEqual(len(handler.error_images), 0)
        self.assertIsNone(handler.recovery_image)

    @patch('error_recovery.ImageMatcher')
    def test_full_error_handling_flow(self, mock_matcher):
        # Mock multiple error icons and recovery
        self.handler.find_all_error_matches = MagicMock(return_value=[
            {'confidence': 0.9, 'x': 100, 'y': 100},
            {'confidence': 0.85, 'x': 300, 'y': 200}
        ])
        
        mock_matcher.return_value.find_template = MagicMock(return_value={
            'confidence': 0.9,
            'x': 400,
            'y': 500
        })
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        with patch('pyautogui.click'), patch('pyautogui.write'), patch('pyautogui.press'):
            success = self.handler.handle_error_case(self.screen)
            self.assertTrue(success)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_direct_recovery_sequence(self, mock_press, mock_write, mock_click, mock_matcher):
        """Test the recovery sequence directly without requiring error triggers."""
        # Mock finding the agent-buttons-footer.png
        mock_matcher.return_value.find_template = MagicMock(return_value={
            'confidence': 0.9,
            'x': 400,
            'y': 500
        })
        
        # Replace the ImageMatcher instance with our mock
        self.handler.matcher = mock_matcher.return_value
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        # Call perform_recovery directly
        success = self.handler.perform_recovery(self.screen)
        
        # Verify the sequence of actions
        self.assertTrue(success)
        mock_click.assert_called_once_with(400, 470)  # Verify click 30 pixels above target
        mock_write.assert_called_once_with('continue')  # Verify typing 'continue'
        mock_press.assert_called_once_with('enter')  # Verify pressing enter
        
        # Verify the target was found with find_template
        mock_matcher.return_value.find_template.assert_called_once()
        args, kwargs = mock_matcher.return_value.find_template.call_args
        self.assertEqual(kwargs.get('threshold', None), self.handler.error_threshold)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_recovery_sequence_with_delay(self, mock_press, mock_write, mock_click, mock_matcher):
        """Test recovery sequence with simulated delay between actions."""
        mock_matcher.return_value.find_template = MagicMock(return_value={
            'confidence': 0.95,
            'x': 500,
            'y': 600
        })
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        handler = ErrorRecoveryHandler(debug=True)
        with patch('time.sleep') as mock_sleep:
            success = handler.perform_recovery(self.screen)
            
            self.assertTrue(success)
            mock_click.assert_called_once_with(500, 570)
            mock_write.assert_called_once_with('continue')
            mock_press.assert_called_once_with('enter')
            mock_sleep.assert_called()

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_recovery_sequence_with_retry(self, mock_press, mock_write, mock_click, mock_matcher):
        """Test recovery sequence with initial failure and retry."""
        mock_matcher.return_value.find_template.side_effect = [
            None,  # First attempt fails
            {'confidence': 0.9, 'x': 300, 'y': 400}  # Second attempt succeeds
        ]
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        handler = ErrorRecoveryHandler(debug=True)
        success = handler.perform_recovery(self.screen)
        
        self.assertTrue(success)
        mock_click.assert_called_once_with(300, 370)
        mock_write.assert_called_once_with('continue')
        mock_press.assert_called_once_with('enter')
        self.assertEqual(mock_matcher.return_value.find_template.call_count, 2)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_recovery_sequence_edge_positions(self, mock_press, mock_write, mock_click, mock_matcher):
        """Test recovery sequence with target near screen edges."""
        test_positions = [
            {'x': 0, 'y': 30},      # Left edge
            {'x': 799, 'y': 30},    # Right edge
            {'x': 400, 'y': 0},     # Top edge
            {'x': 400, 'y': 599}    # Bottom edge
        ]
        
        # Mock image loading
        self.handler.recovery_image = self.footer
        
        handler = ErrorRecoveryHandler(debug=True)
        for pos in test_positions:
            mock_matcher.return_value.find_template = MagicMock(return_value={
                'confidence': 0.9,
                **pos
            })
            
            success = handler.perform_recovery(self.screen)
            self.assertTrue(success)
            expected_y = max(0, pos['y'] - 30)  # Ensure y doesn't go negative
            mock_click.assert_called_with(pos['x'], expected_y)
            mock_write.assert_called_with('continue')
            mock_press.assert_called_with('enter')

if __name__ == '__main__':
    unittest.main() 