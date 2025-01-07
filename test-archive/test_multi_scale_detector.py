"""
Test script for verifying multi-scale button detection implementation.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import cv2
import numpy as np
import matplotlib.pyplot as plt
from src.core.button_detector import ButtonDetector
from src.utils.logging import get_logger

logger = get_logger(__name__)

class MultiScaleDetectorTester:
    def __init__(self):
        """Initialize the tester."""
        self.detector = ButtonDetector()
        self.debug_dir = Path('debug/multi_scale_test')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def create_synthetic_test(self):
        """Create synthetic test images with buttons at different scales."""
        # Create base button template (70x20 with text)
        template = np.zeros((20, 70), dtype=np.uint8)
        cv2.rectangle(template, (5, 5), (65, 15), 255, 2)
        cv2.putText(template, "Test", (15, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 255, 1)
        
        # Create test image with buttons at different scales
        image = np.zeros((300, 800, 3), dtype=np.uint8)
        image.fill(240)  # Light gray background
        
        # Add some noise and gradient for realism
        noise = np.random.normal(0, 5, image.shape).astype(np.uint8)
        image = cv2.add(image, noise)
        
        # Create buttons at different scales
        scales = [0.98, 1.0, 1.02]
        true_positions = []
        
        for i, scale in enumerate(scales):
            # Scale template
            scaled_w = int(70 * scale)
            scaled_h = int(20 * scale)
            scaled = cv2.resize(template, (scaled_w, scaled_h))
            
            # Convert to BGR
            scaled_bgr = cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
            
            # Position in image
            x = 200 + i * 200
            y = 150
            
            # Calculate insertion coordinates
            y1 = y - scaled_h//2
            y2 = y1 + scaled_h
            x1 = x - scaled_w//2
            x2 = x1 + scaled_w
            
            # Insert into image
            image[y1:y2, x1:x2] = scaled_bgr
            
            true_positions.append({
                'x': x,
                'y': y,
                'scale': scale
            })
            
        return image, template, true_positions
        
    def test_synthetic_detection(self):
        """Test detection with synthetic images."""
        logger.info("Testing synthetic button detection...")
        
        # Create test image and data
        image, template, true_positions = self.create_synthetic_test()
        
        # Save test image
        cv2.imwrite(str(self.debug_dir / 'synthetic_test.png'), image)
        cv2.imwrite(str(self.debug_dir / 'synthetic_template.png'), template)
        
        # Create test buttons
        buttons = []
        for i, pos in enumerate(true_positions):
            buttons.append({
                'index': i + 1,
                'template': cv2.cvtColor(template, cv2.COLOR_GRAY2BGR),
                'x': pos['x'],
                'y': pos['y']
            })
        
        # Run detection
        matches = self.detector.find_matches(None, buttons, confidence_threshold=0.7, test_image=image)
        
        # Analyze results
        results = []
        for match, true_pos in zip(matches, true_positions):
            pos_error = np.sqrt((match['x'] - true_pos['x'])**2 + 
                              (match['y'] - true_pos['y'])**2)
            scale_error = abs(match['scale'] - true_pos['scale'])
            
            results.append({
                'position_error': pos_error,
                'scale_error': scale_error,
                'confidence': match['confidence'],
                'detected_scale': match['scale'],
                'true_scale': true_pos['scale']
            })
            
            logger.info(f"\nResults for button {match['button_index']}:")
            logger.info(f"  Position error: {pos_error:.1f}px")
            logger.info(f"  Scale error: {scale_error:.3f}")
            logger.info(f"  True scale: {true_pos['scale']:.3f}")
            logger.info(f"  Detected scale: {match['scale']:.3f}")
            logger.info(f"  Confidence: {match['confidence']:.3f}")
        
        # Create visualization
        self.detector.create_visualization({"left": 0, "top": 0, "width": 800, "height": 300}, matches)
        
        return results
        
    def test_real_detection(self):
        """Test detection with real button images."""
        logger.info("Testing real button detection...")
        
        # Load real button images
        assets_dir = Path('assets/monitor_2')
        results = []
        
        for i in range(1, 4):  # Test buttons 1-3
            template_path = assets_dir / f'button_{i}_pre.png'
            if not template_path.exists():
                continue
                
            template = cv2.imread(str(template_path))
            if template is None:
                continue
                
            # Create test image with scaled versions
            image = np.zeros((300, 800, 3), dtype=np.uint8)
            image.fill(240)  # Light gray background
            
            scales = [0.98, 1.0, 1.02]
            true_positions = []
            
            for j, scale in enumerate(scales):
                h, w = template.shape[:2]
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
                scaled = cv2.resize(template, (scaled_w, scaled_h))
                
                x = 200 + j * 200
                y = 150
                
                # Calculate insertion coordinates
                y1 = y - scaled_h//2
                y2 = y1 + scaled_h
                x1 = x - scaled_w//2
                x2 = x1 + scaled_w
                
                # Insert scaled button
                image[y1:y2, x1:x2] = scaled
                true_positions.append({
                    'x': x,
                    'y': y,
                    'scale': scale
                })
            
            # Save test image
            cv2.imwrite(str(self.debug_dir / f'real_test_{i}.png'), image)
            
            # Create test buttons
            buttons = []
            for j, pos in enumerate(true_positions):
                buttons.append({
                    'index': j + 1,
                    'template': template,
                    'x': pos['x'],
                    'y': pos['y']
                })
            
            # Run detection
            matches = self.detector.find_matches(None, buttons, confidence_threshold=0.7, test_image=image)
            
            # Analyze results
            for match, true_pos in zip(matches, true_positions):
                pos_error = np.sqrt((match['x'] - true_pos['x'])**2 + 
                                  (match['y'] - true_pos['y'])**2)
                scale_error = abs(match['scale'] - true_pos['scale'])
                
                results.append({
                    'button': i,
                    'position_error': pos_error,
                    'scale_error': scale_error,
                    'confidence': match['confidence'],
                    'detected_scale': match['scale'],
                    'true_scale': true_pos['scale']
                })
                
                logger.info(f"\nResults for real button {i} at scale {true_pos['scale']:.3f}:")
                logger.info(f"  Position error: {pos_error:.1f}px")
                logger.info(f"  Scale error: {scale_error:.3f}")
                logger.info(f"  Confidence: {match['confidence']:.3f}")
            
            # Create visualization
            self.detector.create_visualization({"left": 0, "top": 0, "width": 800, "height": 300}, matches)
        
        return results

def main():
    """Run multi-scale detection tests."""
    tester = MultiScaleDetectorTester()
    
    # Test with synthetic images
    logger.info("\nRunning synthetic image tests...")
    synthetic_results = tester.test_synthetic_detection()
    
    # Test with real images
    logger.info("\nRunning real image tests...")
    real_results = tester.test_real_detection()
    
    # Print summary statistics
    logger.info("\nSynthetic Test Summary:")
    pos_errors = [r['position_error'] for r in synthetic_results]
    scale_errors = [r['scale_error'] for r in synthetic_results]
    confidences = [r['confidence'] for r in synthetic_results]
    
    logger.info(f"Position Error - Mean: {np.mean(pos_errors):.1f}px, Max: {np.max(pos_errors):.1f}px")
    logger.info(f"Scale Error - Mean: {np.mean(scale_errors):.3f}, Max: {np.max(scale_errors):.3f}")
    logger.info(f"Confidence - Mean: {np.mean(confidences):.3f}, Min: {np.min(confidences):.3f}")
    
    logger.info("\nReal Button Test Summary:")
    pos_errors = [r['position_error'] for r in real_results]
    scale_errors = [r['scale_error'] for r in real_results]
    confidences = [r['confidence'] for r in real_results]
    
    logger.info(f"Position Error - Mean: {np.mean(pos_errors):.1f}px, Max: {np.max(pos_errors):.1f}px")
    logger.info(f"Scale Error - Mean: {np.mean(scale_errors):.3f}, Max: {np.max(scale_errors):.3f}")
    logger.info(f"Confidence - Mean: {np.mean(confidences):.3f}, Min: {np.min(confidences):.3f}")

if __name__ == "__main__":
    main() 