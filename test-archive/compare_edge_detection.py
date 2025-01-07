"""
Compare gold standard edge detection with current implementation.
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

class EdgeDetectionComparator:
    def __init__(self):
        """Initialize the edge detection comparator."""
        self.debug_dir = Path('debug/edge_comparison')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def gold_standard_edge_detection(self, image):
        """Gold standard edge detection implementation."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Detect edges with gold standard parameters
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges with gold standard kernel
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        return dilated
        
    def current_edge_detection(self, image):
        """Current edge detection implementation."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Detect edges with current parameters
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges with current kernel
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        return dilated
        
    def compare_edge_detection(self, image_path):
        """Compare edge detection methods and analyze differences."""
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return False
            
        # Get edges from both methods
        gold_edges = self.gold_standard_edge_detection(image)
        current_edges = self.current_edge_detection(image)
        
        # Calculate difference metrics
        intersection = cv2.bitwise_and(gold_edges, current_edges)
        union = cv2.bitwise_or(gold_edges, current_edges)
        
        # Calculate IoU (Intersection over Union)
        iou = np.sum(intersection) / np.sum(union) if np.sum(union) > 0 else 0
        
        # Calculate edge point counts
        gold_points = np.sum(gold_edges > 0)
        current_points = np.sum(current_edges > 0)
        
        # Calculate edge continuity
        gold_contours, _ = cv2.findContours(gold_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        current_contours, _ = cv2.findContours(current_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        gold_avg_points = sum(len(c) for c in gold_contours) / len(gold_contours) if gold_contours else 0
        current_avg_points = sum(len(c) for c in current_contours) / len(current_contours) if current_contours else 0
        
        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'Edge Detection Comparison - {image_path.name}')
        
        # Original image
        axes[0, 0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title('Original')
        axes[0, 0].axis('off')
        
        # Gold standard edges
        axes[0, 1].imshow(gold_edges, cmap='gray')
        axes[0, 1].set_title('Gold Standard')
        axes[0, 1].axis('off')
        
        # Current edges
        axes[1, 0].imshow(current_edges, cmap='gray')
        axes[1, 0].set_title('Current')
        axes[1, 0].axis('off')
        
        # Difference visualization
        diff = cv2.absdiff(gold_edges, current_edges)
        axes[1, 1].imshow(diff, cmap='hot')
        axes[1, 1].set_title('Difference')
        axes[1, 1].axis('off')
        
        # Save comparison
        plt.tight_layout()
        plt.savefig(str(self.debug_dir / f'comparison_{image_path.name}'))
        plt.close()
        
        # Log metrics
        logging.info(f"\nComparison metrics for {image_path.name}:")
        logging.info(f"IoU (Intersection over Union): {iou:.4f}")
        logging.info(f"Edge points - Gold: {gold_points}, Current: {current_points}")
        logging.info(f"Points per contour - Gold: {gold_avg_points:.2f}, Current: {current_avg_points:.2f}")
        logging.info(f"Contours - Gold: {len(gold_contours)}, Current: {len(current_contours)}")
        
        return {
            'iou': iou,
            'gold_points': gold_points,
            'current_points': current_points,
            'gold_avg_points': gold_avg_points,
            'current_avg_points': current_avg_points,
            'gold_contours': len(gold_contours),
            'current_contours': len(current_contours)
        }

def main():
    """Run edge detection comparison tests."""
    comparator = EdgeDetectionComparator()
    
    # Test with sample buttons from assets
    assets_dir = Path('assets/monitor_2')
    if not assets_dir.exists():
        logging.error("No calibration data found!")
        return
        
    button_files = sorted(assets_dir.glob('button_*_pre.png'))
    if not button_files:
        logging.error("No button images found!")
        return
        
    logging.info("Starting edge detection comparison...")
    
    all_metrics = []
    for button_file in button_files:
        metrics = comparator.compare_edge_detection(button_file)
        if metrics:
            all_metrics.append(metrics)
    
    if all_metrics:
        # Calculate average metrics
        avg_iou = sum(m['iou'] for m in all_metrics) / len(all_metrics)
        avg_gold_points = sum(m['gold_points'] for m in all_metrics) / len(all_metrics)
        avg_current_points = sum(m['current_points'] for m in all_metrics) / len(all_metrics)
        
        logging.info("\nOverall metrics:")
        logging.info(f"Average IoU: {avg_iou:.4f}")
        logging.info(f"Average edge points - Gold: {avg_gold_points:.1f}, Current: {avg_current_points:.1f}")
        logging.info(f"Point ratio (Current/Gold): {(avg_current_points/avg_gold_points):.2f}")
    
    logging.info("\nEdge detection comparison complete!")
    logging.info(f"Debug output saved to: {comparator.debug_dir}")

if __name__ == "__main__":
    main() 