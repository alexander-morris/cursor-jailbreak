"""
Test module for edge detection improvements.
"""

import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EdgeDetectionTester:
    def __init__(self):
        """Initialize the edge detection tester."""
        self.debug_dir = Path('debug/edge_detection')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def current_edge_detection(self, image):
        """Current edge detection implementation."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 50, 150)
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        return dilated
        
    def improved_edge_detection(self, image):
        """Improved edge detection with adaptive thresholding."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Normalize image contrast
        normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Edge detection with optimized parameters
        blurred = cv2.GaussianBlur(binary, (3, 3), 0)
        edges = cv2.Canny(blurred, 30, 120, L2gradient=True)
        
        # Morphological operations to connect edges
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        return dilated
        
    def compare_edge_detection(self, image_path):
        """Compare current and improved edge detection methods."""
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return False
            
        # Apply both methods
        current_edges = self.current_edge_detection(image)
        improved_edges = self.improved_edge_detection(image)
        
        # Create visualization
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'Edge Detection Comparison - {image_path.name}')
        
        # Original image
        axes[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        axes[0].set_title('Original Image')
        axes[0].axis('off')
        
        # Current edges
        axes[1].imshow(current_edges, cmap='gray')
        axes[1].set_title('Current Edge Detection')
        axes[1].axis('off')
        
        # Improved edges
        axes[2].imshow(improved_edges, cmap='gray')
        axes[2].set_title('Improved Edge Detection')
        axes[2].axis('off')
        
        # Save comparison
        plt.tight_layout()
        plt.savefig(str(self.debug_dir / f'edge_comparison_{image_path.name}'))
        plt.close()
        
        # Calculate edge density and continuity metrics
        current_density = np.sum(current_edges > 0) / current_edges.size
        improved_density = np.sum(improved_edges > 0) / improved_edges.size
        
        # Calculate edge continuity using connected components
        _, current_labels = cv2.connectedComponents(current_edges)
        _, improved_labels = cv2.connectedComponents(improved_edges)
        current_components = len(np.unique(current_labels)) - 1  # Subtract background
        improved_components = len(np.unique(improved_labels)) - 1
        
        logging.info(f"\nEdge detection metrics for {image_path.name}:")
        logging.info("Current method:")
        logging.info(f"  Edge density: {current_density:.3f}")
        logging.info(f"  Connected components: {current_components}")
        logging.info("\nImproved method:")
        logging.info(f"  Edge density: {improved_density:.3f}")
        logging.info(f"  Connected components: {improved_components}")
        
        return {
            'current_density': current_density,
            'improved_density': improved_density,
            'current_components': current_components,
            'improved_components': improved_components
        }

def main():
    """Run edge detection tests."""
    tester = EdgeDetectionTester()
    
    # Test with calibration button images
    assets_dir = Path('assets/monitor_2')
    all_metrics = []
    
    for i in range(1, 4):  # Buttons 1-3
        button_file = assets_dir / f'button_{i}_pre.png'
        if button_file.exists():
            logging.info(f"\nTesting edge detection on {button_file.name}")
            metrics = tester.compare_edge_detection(button_file)
            if metrics:
                all_metrics.append(metrics)
    
    if all_metrics:
        # Calculate average metrics
        avg_current_density = sum(m['current_density'] for m in all_metrics) / len(all_metrics)
        avg_improved_density = sum(m['improved_density'] for m in all_metrics) / len(all_metrics)
        avg_current_components = sum(m['current_components'] for m in all_metrics) / len(all_metrics)
        avg_improved_components = sum(m['improved_components'] for m in all_metrics) / len(all_metrics)
        
        logging.info("\nOverall metrics:")
        logging.info(f"Average current edge density: {avg_current_density:.3f}")
        logging.info(f"Average improved edge density: {avg_improved_density:.3f}")
        logging.info(f"Average current components: {avg_current_components:.1f}")
        logging.info(f"Average improved components: {avg_improved_components:.1f}")
    
    logging.info("\nEdge detection testing complete!")
    logging.info(f"Debug output saved to: {tester.debug_dir}")

if __name__ == "__main__":
    main() 