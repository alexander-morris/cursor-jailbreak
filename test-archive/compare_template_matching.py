"""
Compare gold standard multi-scale template matching with current implementation.
"""

import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import logging
import mss  # Add mss import for screen capture

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TemplateMatchingComparator:
    def __init__(self):
        """Initialize the template matching comparator."""
        self.debug_dir = Path('debug/template_comparison')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.sct = mss.mss()  # Initialize screen capture
        
    def capture_screen(self, monitor_num=3):
        """Capture the screen for the given monitor."""
        monitor = self.sct.monitors[monitor_num]
        screenshot = self.sct.grab(monitor)
        return np.array(screenshot)
        
    def preprocess_with_edges(self, image):
        """Edge detection preprocessing."""
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
        
    def extract_template_region(self, image, cal_x, cal_y):
        """Extract 70x20 region centered on calibration point."""
        template_h, template_w = 20, 70  # Gold standard template size
        template_y = cal_y - template_h // 2
        template_x = cal_x - template_w // 2
        
        # Ensure template region is within image bounds
        if (template_y < 0 or template_y + template_h > image.shape[0] or
            template_x < 0 or template_x + template_w > image.shape[1]):
            return None
            
        return image[template_y:template_y+template_h, template_x:template_x+template_w].copy()
        
    def gold_standard_matching(self, image, template, cal_x, cal_y):
        """Gold standard multi-scale template matching implementation."""
        if template is None or image is None:
            return None
            
        # Convert images to grayscale
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image.copy()
            template_gray = template.copy()
            
        # Get edge images
        image_edges = self.preprocess_with_edges(image)
        template_edges = self.preprocess_with_edges(template)
        
        template_h, template_w = template.shape[:2]
        
        # Define search region with larger margins
        vertical_margin = 100  # Increased margin
        horizontal_margin = 50  # Increased margin
        
        search_top = max(0, cal_y - vertical_margin)
        search_bottom = min(image.shape[0], cal_y + vertical_margin)
        search_left = max(0, cal_x - horizontal_margin)
        search_right = min(image.shape[1], cal_x + horizontal_margin)
        
        # Get search regions
        search_region_edges = image_edges[search_top:search_bottom, search_left:search_right]
        search_region_gray = image_gray[search_top:search_bottom, search_left:search_right]
        
        # Save edge detection debug images
        debug_edges = np.zeros((search_bottom - search_top, search_right - search_left, 3), dtype=np.uint8)
        debug_edges[..., 0] = search_region_edges  # Blue channel
        debug_edges[..., 1] = search_region_edges  # Green channel
        debug_edges[..., 2] = search_region_edges  # Red channel
        cv2.imwrite(str(self.debug_dir / 'search_region_edges.png'), debug_edges)
        
        debug_template = np.zeros((template_edges.shape[0], template_edges.shape[1], 3), dtype=np.uint8)
        debug_template[..., 0] = template_edges
        debug_template[..., 1] = template_edges
        debug_template[..., 2] = template_edges
        cv2.imwrite(str(self.debug_dir / 'template_edges.png'), debug_template)
        
        # Try different scales
        scales = [0.98, 0.99, 0.995, 1.0, 1.005, 1.01, 1.02]  # More scales
        best_match = None
        best_quality = 0
        
        for scale in scales:
            if scale != 1.0:
                scaled_template_edges = cv2.resize(template_edges, 
                    (int(template_w * scale), int(template_h * scale)),
                    interpolation=cv2.INTER_NEAREST)
                scaled_template_gray = cv2.resize(template_gray,
                    (int(template_w * scale), int(template_h * scale)),
                    interpolation=cv2.INTER_LINEAR)
            else:
                scaled_template_edges = template_edges
                scaled_template_gray = template_gray
                
            scaled_h, scaled_w = scaled_template_edges.shape[:2]
            
            if search_region_edges.shape[0] < scaled_h or search_region_edges.shape[1] < scaled_w:
                continue
                
            # First pass: Match edges with further reduced threshold
            edge_result = cv2.matchTemplate(search_region_edges, scaled_template_edges, cv2.TM_CCOEFF_NORMED)
            edge_matches = np.where(edge_result >= 0.2)  # Even lower threshold
            
            for pt_y, pt_x in zip(*edge_matches):
                # Calculate absolute position
                abs_x = search_left + pt_x
                abs_y = search_top + pt_y
                
                # Get ROI for both edge and direct matching
                roi_edges = search_region_edges[pt_y:pt_y+scaled_h, pt_x:pt_x+scaled_w]
                roi_gray = search_region_gray[pt_y:pt_y+scaled_h, pt_x:pt_x+scaled_w]
                
                if roi_edges.shape != scaled_template_edges.shape or roi_gray.shape != scaled_template_gray.shape:
                    continue
                    
                # Calculate match quality components with refined weights
                direct_conf = cv2.matchTemplate(roi_gray, scaled_template_gray, cv2.TM_CCOEFF_NORMED)[0][0]
                edge_conf = edge_result[pt_y, pt_x]
                edge_overlap = np.sum(roi_edges & scaled_template_edges) / np.sum(scaled_template_edges)
                
                # Combined score with refined weights
                match_quality = (direct_conf * 0.65 + edge_overlap * 0.2 + edge_conf * 0.15)
                
                # Further reduced quality threshold
                if match_quality > 0.4:
                    if match_quality > best_quality:
                        best_quality = match_quality
                        best_match = {
                            'x': abs_x + scaled_w // 2,
                            'y': abs_y + scaled_h // 2,
                            'scale': scale,
                            'quality': match_quality,
                            'direct_conf': direct_conf,
                            'edge_conf': edge_conf,
                            'edge_overlap': edge_overlap
                        }
                        
                        # Save best match debug image
                        debug_match = debug_edges.copy()
                        cv2.rectangle(debug_match,
                                    (pt_x, pt_y),
                                    (pt_x + scaled_w, pt_y + scaled_h),
                                    (0, 255, 0), 1)
                        cv2.imwrite(str(self.debug_dir / 'best_match_edges.png'), debug_match)
        
        return best_match
        
    def current_matching(self, image, template, cal_x, cal_y):
        """Current single-scale template matching implementation."""
        if template is None or image is None:
            return None
            
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image.copy()
            template_gray = template.copy()
            
        template_h, template_w = template.shape[:2]
            
        # Define search region (use same margins for fair comparison)
        vertical_margin = 80
        horizontal_margin = 40
        
        search_top = max(0, cal_y - vertical_margin)
        search_bottom = min(image.shape[0], cal_y + vertical_margin)
        search_left = max(0, cal_x - horizontal_margin)
        search_right = min(image.shape[1], cal_x + horizontal_margin)
        
        # Get search region
        search_region = image_gray[search_top:search_bottom, search_left:search_right]
        
        if search_region.shape[0] < template_h or search_region.shape[1] < template_w:
            return None
            
        # Single scale direct template matching
        result = cv2.matchTemplate(search_region, template_gray, cv2.TM_CCORR_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= 0.75:  # Current threshold
            match_x = search_left + max_loc[0] + template_w // 2
            match_y = search_top + max_loc[1] + template_h // 2
            
            return {
                'x': match_x,
                'y': match_y,
                'scale': 1.0,
                'quality': max_val,
                'direct_conf': max_val,
                'edge_conf': 0,  # Not used in current implementation
                'edge_overlap': 0  # Not used in current implementation
            }
            
        return None
        
    def compare_matching(self, template_path, cal_x, cal_y):
        """Compare matching methods and analyze differences."""
        # Load template image
        template = cv2.imread(str(template_path))
        if template is None:
            logging.error(f"Failed to load template: {template_path}")
            return False
            
        # Capture full screen image
        screen = self.capture_screen()
        if screen is None:
            logging.error("Failed to capture screen")
            return False
            
        # Convert screen from BGRA to BGR
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
            
        # Create copies for visualization
        gold_vis = screen.copy()
        current_vis = screen.copy()
        
        # Draw template region
        template_h, template_w = template.shape[:2]
        template_y = cal_y - template_h // 2
        template_x = cal_x - template_w // 2
        cv2.rectangle(gold_vis,
                     (template_x, template_y),
                     (template_x + template_w, template_y + template_h),
                     (0, 255, 255), 1)
        cv2.rectangle(current_vis,
                     (template_x, template_y),
                     (template_x + template_w, template_y + template_h),
                     (0, 255, 255), 1)
        
        # Run both matching methods
        gold_match = self.gold_standard_matching(screen, template, cal_x, cal_y)
        current_match = self.current_matching(screen, template, cal_x, cal_y)
        
        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle(f'Template Matching Comparison - {template_path.name}')
        
        # Draw matches
        if gold_match:
            cv2.circle(gold_vis, (gold_match['x'], gold_match['y']), 5, (0, 255, 0), -1)
            cv2.putText(gold_vis, f"Q: {gold_match['quality']:.3f}", 
                       (gold_match['x'] - 50, gold_match['y'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                       
        if current_match:
            cv2.circle(current_vis, (current_match['x'], current_match['y']), 5, (0, 255, 0), -1)
            cv2.putText(current_vis, f"Q: {current_match['quality']:.3f}",
                       (current_match['x'] - 50, current_match['y'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                       
        # Draw calibration point
        cv2.circle(gold_vis, (cal_x, cal_y), 3, (0, 0, 255), -1)
        cv2.circle(current_vis, (cal_x, cal_y), 3, (0, 0, 255), -1)
        
        # Draw search region
        vertical_margin = 80
        horizontal_margin = 40
        cv2.rectangle(gold_vis,
                     (cal_x - horizontal_margin, cal_y - vertical_margin),
                     (cal_x + horizontal_margin, cal_y + vertical_margin),
                     (255, 0, 0), 1)
        cv2.rectangle(current_vis,
                     (cal_x - horizontal_margin, cal_y - vertical_margin),
                     (cal_x + horizontal_margin, cal_y + vertical_margin),
                     (255, 0, 0), 1)
        
        # Show results
        axes[0].imshow(cv2.cvtColor(gold_vis, cv2.COLOR_BGR2RGB))
        axes[0].set_title('Gold Standard Match')
        axes[0].axis('off')
        
        axes[1].imshow(cv2.cvtColor(current_vis, cv2.COLOR_BGR2RGB))
        axes[1].set_title('Current Match')
        axes[1].axis('off')
        
        # Save comparison
        plt.tight_layout()
        plt.savefig(str(self.debug_dir / f'comparison_{template_path.name}'))
        plt.close()
        
        # Log results
        logging.info(f"\nMatching results for {template_path.name}:")
        if gold_match:
            logging.info("Gold Standard Match:")
            logging.info(f"  Position: ({gold_match['x']}, {gold_match['y']})")
            logging.info(f"  Scale: {gold_match['scale']:.3f}")
            logging.info(f"  Quality: {gold_match['quality']:.3f}")
            logging.info(f"  Components: Direct={gold_match['direct_conf']:.3f}, "
                       f"Edge={gold_match['edge_conf']:.3f}, "
                       f"Overlap={gold_match['edge_overlap']:.3f}")
        else:
            logging.info("Gold Standard: No match found")
            
        if current_match:
            logging.info("\nCurrent Match:")
            logging.info(f"  Position: ({current_match['x']}, {current_match['y']})")
            logging.info(f"  Scale: {current_match['scale']:.3f}")
            logging.info(f"  Quality: {current_match['quality']:.3f}")
        else:
            logging.info("Current: No match found")
            
        if gold_match and current_match:
            # Calculate differences
            pos_diff = np.sqrt((gold_match['x'] - current_match['x'])**2 + 
                             (gold_match['y'] - current_match['y'])**2)
            quality_diff = abs(gold_match['quality'] - current_match['quality'])
            
            logging.info(f"\nDifferences:")
            logging.info(f"  Position difference: {pos_diff:.1f}px")
            logging.info(f"  Quality difference: {quality_diff:.3f}")
            
            return {
                'gold_match': gold_match,
                'current_match': current_match,
                'pos_diff': pos_diff,
                'quality_diff': quality_diff
            }
        
        return None

def main():
    """Run template matching comparison tests."""
    comparator = TemplateMatchingComparator()
    
    # Test with sample buttons from assets
    assets_dir = Path('assets/monitor_2')
    if not assets_dir.exists():
        logging.error("No calibration data found!")
        return
        
    # Get button files and their calibration coordinates
    button_files = []
    for i in range(1, 4):  # Buttons 1-3
        pre_file = assets_dir / f'button_{i}_pre.png'
        coords_file = assets_dir / f'click_coords_{i}.txt'
        
        if pre_file.exists() and coords_file.exists():
            with open(coords_file, 'r') as f:
                coords = f.read().strip().split(',')
                cal_x, cal_y = int(coords[0]), int(coords[1])
                button_files.append((pre_file, cal_x, cal_y))
        
    if not button_files:
        logging.error("No button files found!")
        return
        
    logging.info("Starting template matching comparison...")
    
    all_metrics = []
    for button_file, cal_x, cal_y in button_files:
        metrics = comparator.compare_matching(button_file, cal_x, cal_y)
        if metrics:
            all_metrics.append(metrics)
    
    if all_metrics:
        # Calculate average metrics
        avg_pos_diff = sum(m['pos_diff'] for m in all_metrics) / len(all_metrics)
        avg_quality_diff = sum(m['quality_diff'] for m in all_metrics) / len(all_metrics)
        
        logging.info("\nOverall metrics:")
        logging.info(f"Average position difference: {avg_pos_diff:.1f}px")
        logging.info(f"Average quality difference: {avg_quality_diff:.3f}")
    
    logging.info("\nTemplate matching comparison complete!")
    logging.info(f"Debug output saved to: {comparator.debug_dir}")

if __name__ == "__main__":
    main() 