"""
Test module for multi-scale template matching improvements.
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

class MultiScaleTester:
    def __init__(self):
        """Initialize the multi-scale tester."""
        self.debug_dir = Path('debug/multi_scale')
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def current_matching(self, image, template):
        """Current single-scale template matching."""
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image.copy()
            template_gray = template.copy()
            
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        return {
            'confidence': max_val,
            'location': max_loc,
            'scale': 1.0
        }
        
    def multi_scale_matching(self, image, template, scales=[0.98, 0.99, 0.995, 1.0, 1.005, 1.01, 1.02]):
        """Multi-scale template matching implementation."""
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image.copy()
            template_gray = template.copy()
            
        template_h, template_w = template.shape[:2]
        best_result = None
        best_scale = 1.0
        
        # Try different scales
        for scale in scales:
            if scale != 1.0:
                scaled_w = int(template_w * scale)
                scaled_h = int(template_h * scale)
                scaled_template = cv2.resize(template_gray, (scaled_w, scaled_h),
                                          interpolation=cv2.INTER_LINEAR)
            else:
                scaled_template = template_gray
                
            result = cv2.matchTemplate(image_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if best_result is None or max_val > best_result['confidence']:
                best_result = {
                    'confidence': max_val,
                    'location': max_loc,
                    'scale': scale
                }
                
        return best_result
        
    def test_with_synthetic_variations(self):
        """Test matching with synthetic scale variations."""
        # Create a simple synthetic button template
        template = np.zeros((20, 70), dtype=np.uint8)
        cv2.rectangle(template, (5, 5), (65, 15), 255, 2)
        cv2.putText(template, "Test", (15, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 255, 1)
        
        # Create test image with multiple scales
        image = np.zeros((200, 400), dtype=np.uint8)
        scales = [0.95, 1.0, 1.05]
        true_positions = []
        
        for i, scale in enumerate(scales):
            scaled_w = int(70 * scale)
            scaled_h = int(20 * scale)
            scaled = cv2.resize(template, (scaled_w, scaled_h))
            x = 50 + i * 100
            y = 50
            image[y:y+scaled_h, x:x+scaled_w] = scaled
            true_positions.append((x, y, scale))
            
        # Test both methods
        results = []
        for x, y, scale in true_positions:
            roi = image[y:y+30, x:x+100]  # Region around button
            
            # Current method
            current = self.current_matching(roi, template)
            current['true_scale'] = scale
            current['method'] = 'Current'
            results.append(current)
            
            # Multi-scale method
            multi = self.multi_scale_matching(roi, template)
            multi['true_scale'] = scale
            multi['method'] = 'Multi-scale'
            results.append(multi)
            
        # Visualize results
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('Synthetic Test Results')
        
        # Plot scale accuracy
        scales = [r['true_scale'] for r in results]
        detected = [r['scale'] for r in results]
        methods = [r['method'] for r in results]
        
        for ax, title in zip(axes, ['Scale Accuracy', 'Confidence']):
            for method in ['Current', 'Multi-scale']:
                mask = [m == method for m in methods]
                if title == 'Scale Accuracy':
                    ax.scatter(np.array(scales)[mask], np.array(detected)[mask],
                             label=method, alpha=0.7)
                    ax.plot([0.9, 1.1], [0.9, 1.1], 'k--', alpha=0.3)
                    ax.set_xlabel('True Scale')
                    ax.set_ylabel('Detected Scale')
                else:
                    ax.scatter(np.array(scales)[mask],
                             [r['confidence'] for r, m in zip(results, mask) if m],
                             label=method, alpha=0.7)
                    ax.set_xlabel('True Scale')
                    ax.set_ylabel('Match Confidence')
                    
            ax.grid(True, alpha=0.3)
            ax.legend()
            
        plt.tight_layout()
        plt.savefig(str(self.debug_dir / 'synthetic_test_results.png'))
        plt.close()
        
        return results
        
    def test_with_real_buttons(self):
        """Test matching with real button images."""
        assets_dir = Path('assets/monitor_2')
        results = []
        
        for i in range(1, 4):  # Buttons 1-3
            button_file = assets_dir / f'button_{i}_pre.png'
            if not button_file.exists():
                continue
                
            # Load button image
            button = cv2.imread(str(button_file))
            if button is None:
                continue
                
            # Create test image with multiple scales
            canvas = np.zeros((300, 800, 3), dtype=np.uint8)
            scales = [0.98, 1.0, 1.02]
            true_positions = []
            
            for j, scale in enumerate(scales):
                h, w = button.shape[:2]
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
                scaled = cv2.resize(button, (scaled_w, scaled_h))
                x = 50 + j * 200
                y = 50
                canvas[y:y+scaled_h, x:x+scaled_w] = scaled
                true_positions.append((x, y, scale))
                
            # Test both methods
            for x, y, scale in true_positions:
                roi_h, roi_w = int(button.shape[0] * 1.5), int(button.shape[1] * 1.5)
                roi = canvas[y:y+roi_h, x:x+roi_w]
                
                # Current method
                current = self.current_matching(roi, button)
                current.update({
                    'true_scale': scale,
                    'method': 'Current',
                    'button': i
                })
                results.append(current)
                
                # Multi-scale method
                multi = self.multi_scale_matching(roi, button)
                multi.update({
                    'true_scale': scale,
                    'method': 'Multi-scale',
                    'button': i
                })
                results.append(multi)
                
            # Visualize test image
            cv2.imwrite(str(self.debug_dir / f'button_{i}_test.png'), canvas)
            
        # Plot results
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('Real Button Test Results')
        
        scales = [r['true_scale'] for r in results]
        detected = [r['scale'] for r in results]
        methods = [r['method'] for r in results]
        buttons = [r['button'] for r in results]
        
        for ax, title in zip(axes, ['Scale Accuracy', 'Confidence']):
            for method in ['Current', 'Multi-scale']:
                for btn in range(1, 4):
                    mask = [m == method and b == btn for m, b in zip(methods, buttons)]
                    if sum(mask) == 0:
                        continue
                        
                    if title == 'Scale Accuracy':
                        ax.scatter(np.array(scales)[mask], np.array(detected)[mask],
                                 label=f'{method} (Button {btn})', alpha=0.7)
                        ax.plot([0.95, 1.05], [0.95, 1.05], 'k--', alpha=0.3)
                        ax.set_xlabel('True Scale')
                        ax.set_ylabel('Detected Scale')
                    else:
                        ax.scatter(np.array(scales)[mask],
                                 [r['confidence'] for r, m in zip(results, mask) if m],
                                 label=f'{method} (Button {btn})', alpha=0.7)
                        ax.set_xlabel('True Scale')
                        ax.set_ylabel('Match Confidence')
                        
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
        plt.tight_layout()
        plt.savefig(str(self.debug_dir / 'real_button_results.png'))
        plt.close()
        
        return results

def main():
    """Run multi-scale matching tests."""
    tester = MultiScaleTester()
    
    # Test with synthetic variations
    logging.info("Testing with synthetic variations...")
    synthetic_results = tester.test_with_synthetic_variations()
    
    # Analyze synthetic results
    current_scales = [r['scale'] for r in synthetic_results if r['method'] == 'Current']
    multi_scales = [r['scale'] for r in synthetic_results if r['method'] == 'Multi-scale']
    true_scales = [r['true_scale'] for r in synthetic_results if r['method'] == 'Current']
    
    current_error = np.mean(np.abs(np.array(current_scales) - np.array(true_scales)))
    multi_error = np.mean(np.abs(np.array(multi_scales) - np.array(true_scales)))
    
    logging.info("\nSynthetic Test Results:")
    logging.info(f"Current method average scale error: {current_error:.3f}")
    logging.info(f"Multi-scale method average scale error: {multi_error:.3f}")
    
    # Test with real buttons
    logging.info("\nTesting with real buttons...")
    real_results = tester.test_with_real_buttons()
    
    # Analyze real button results
    for method in ['Current', 'Multi-scale']:
        method_results = [r for r in real_results if r['method'] == method]
        scales = [r['scale'] for r in method_results]
        true_scales = [r['true_scale'] for r in method_results]
        confidences = [r['confidence'] for r in method_results]
        
        scale_error = np.mean(np.abs(np.array(scales) - np.array(true_scales)))
        avg_conf = np.mean(confidences)
        
        logging.info(f"\n{method} Results:")
        logging.info(f"Average scale error: {scale_error:.3f}")
        logging.info(f"Average confidence: {avg_conf:.3f}")
    
    logging.info("\nMulti-scale testing complete!")
    logging.info(f"Debug output saved to: {tester.debug_dir}")

if __name__ == "__main__":
    main() 