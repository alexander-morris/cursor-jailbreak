"""
Test script for verifying button detection implementation.
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

class ButtonDetectorTester:
    def __init__(self):
        """Initialize the tester."""
        self.detector = ButtonDetector()
        self.debug_dir = Path('debug/button_test')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def test_with_calibration_data(self):
        """Test detection using actual calibration data."""
        logger.info("Testing with calibration data...")
        
        # Load calibration data
        assets_dir = Path('assets/monitor_2')
        button_data = []
        
        # Load templates and coordinates
        for i in range(1, 4):  # Test buttons 1-3
            template_path = assets_dir / f'button_{i}_pre.png'
            coords_path = assets_dir / f'click_coords_{i}.txt'
            
            if not template_path.exists() or not coords_path.exists():
                continue
                
            template = cv2.imread(str(template_path))
            if template is None:
                continue
                
            with open(coords_path, 'r') as f:
                x, y = map(int, f.read().strip().split(','))
                
            button_data.append({
                'index': i,
                'template': template,
                'x': x,
                'y': y
            })
            
        if not button_data:
            logger.error("No calibration data found!")
            return
            
        # Create test monitor dict
        monitor = {
            "left": 0,
            "top": 0,
            "width": 1920,
            "height": 1080,
            "mon": 2
        }
        
        # Run detection
        matches = self.detector.find_matches(monitor, button_data)
        
        # Create visualization
        visualization = np.zeros((1080, 1920, 3), dtype=np.uint8)
        visualization.fill(240)  # Light gray background
        
        # Colors for different buttons (BGR format)
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # Red, Green, Blue
        
        # Draw calibration points and matches
        for button, color in zip(button_data, colors):
            cal_x, cal_y = button['x'], button['y']
            
            # Draw calibration point
            cv2.circle(visualization, (cal_x, cal_y), 5, color, -1)
            cv2.putText(visualization, f"Cal {button['index']}", 
                       (cal_x + 10, cal_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Find corresponding match
            match = next((m for m in matches if m['button_index'] == button['index']), None)
            if match:
                match_x, match_y = int(match['x']), int(match['y'])
                
                # Draw match point
                cv2.circle(visualization, (match_x, match_y), 5, color, -1)
                
                # Draw line between calibration and match
                cv2.line(visualization, (cal_x, cal_y), 
                        (match_x, match_y), color, 1)
                
                # Draw match info
                text = f"Match {button['index']} ({match['confidence']:.3f})"
                cv2.putText(visualization, text,
                           (match_x + 10, match_y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # Draw scale info
                scale_text = f"Scale: {match['scale']:.3f}"
                cv2.putText(visualization, scale_text,
                           (match_x + 10, match_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # Calculate and draw distances
                h_dist = abs(match_x - cal_x)
                v_dist = abs(match_y - cal_y)
                dist_text = f"H:{h_dist}px V:{v_dist}px"
                cv2.putText(visualization, dist_text,
                           (match_x + 10, match_y + 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                logger.info(f"\nResults for Button {button['index']}:")
                logger.info(f"  Calibration: ({cal_x}, {cal_y})")
                logger.info(f"  Match: ({match_x}, {match_y})")
                logger.info(f"  Scale: {match['scale']:.3f}")
                logger.info(f"  Confidence: {match['confidence']:.3f}")
                logger.info(f"  Horizontal distance: {h_dist}px")
                logger.info(f"  Vertical distance: {v_dist}px")
                
        # Save visualization
        cv2.imwrite(str(self.debug_dir / 'calibration_test_results.png'), visualization)
        logger.info(f"\nSaved visualization to: {self.debug_dir / 'calibration_test_results.png'}")

def main():
    """Run button detection tests."""
    tester = ButtonDetectorTester()
    
    # Test with actual calibration data
    logger.info("\nRunning calibration data tests...")
    tester.test_with_calibration_data()

if __name__ == "__main__":
    main() 