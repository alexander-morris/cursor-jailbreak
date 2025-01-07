"""
Visualize button detection matches from both methods.
"""

import cv2
import numpy as np
from pathlib import Path
import mss
from compare_template_matching import TemplateMatchingComparator

def main():
    # Initialize screen capture and comparator
    comparator = TemplateMatchingComparator()
    sct = mss.mss()
    monitor = sct.monitors[3]  # Monitor 3: (-1435, -1080, 1920x1080)
    screenshot = np.array(sct.grab(monitor))
    screen = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    # Load calibration coordinates and templates
    assets_dir = Path('assets/monitor_2')
    button_data = []
    for i in range(1, 4):  # Buttons 1-3
        coords_file = assets_dir / f'click_coords_{i}.txt'
        template_file = assets_dir / f'button_{i}_pre.png'
        if coords_file.exists() and template_file.exists():
            with open(coords_file, 'r') as f:
                coords = f.read().strip().split(',')
                cal_x, cal_y = int(coords[0]), int(coords[1])
                button_data.append((template_file, cal_x, cal_y))
    
    # Create visualization
    vis = screen.copy()
    
    # Draw matches for each button
    for i, (template_file, cal_x, cal_y) in enumerate(button_data, 1):
        # Get matches from both methods
        template = cv2.imread(str(template_file))
        gold_match = comparator.gold_standard_matching(screen, template, cal_x, cal_y)
        current_match = comparator.current_matching(screen, template, cal_x, cal_y)
        
        # Draw calibration point
        cv2.circle(vis, (cal_x, cal_y), 5, (0, 0, 255), -1)  # Red dot
        cv2.putText(vis, f"Button {i}", 
                   (cal_x + 10, cal_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw template region
        template_h, template_w = template.shape[:2]
        template_y = cal_y - template_h // 2
        template_x = cal_x - template_w // 2
        cv2.rectangle(vis,
                     (template_x, template_y),
                     (template_x + template_w, template_y + template_h),
                     (255, 255, 0), 2)  # Yellow rectangle
        
        # Draw search region
        vertical_margin = 80
        horizontal_margin = 40
        cv2.rectangle(vis,
                     (cal_x - horizontal_margin, cal_y - vertical_margin),
                     (cal_x + horizontal_margin, cal_y + vertical_margin),
                     (255, 0, 0), 1)  # Blue rectangle
        
        # Draw gold standard match
        if gold_match:
            cv2.circle(vis, (gold_match['x'], gold_match['y']), 5, (0, 255, 0), -1)  # Green dot
            cv2.putText(vis, f"Gold {i}: {gold_match['quality']:.2f}", 
                       (gold_match['x'] + 10, gold_match['y'] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw current match
        if current_match:
            cv2.circle(vis, (current_match['x'], current_match['y']), 5, (255, 165, 0), -1)  # Orange dot
            cv2.putText(vis, f"Current {i}: {current_match['quality']:.2f}",
                       (current_match['x'] + 10, current_match['y'] + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
    
    # Add legend
    legend_y = 30
    cv2.putText(vis, "Legend:", (10, legend_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    # Calibration point
    cv2.circle(vis, (150, legend_y-5), 5, (0, 0, 255), -1)
    cv2.putText(vis, "Calibration Point", (170, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    # Template region
    cv2.rectangle(vis, (350, legend_y-10), (380, legend_y+10), (255, 255, 0), 2)
    cv2.putText(vis, "Template Region", (400, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    # Search region
    cv2.rectangle(vis, (580, legend_y-15), (620, legend_y+15), (255, 0, 0), 1)
    cv2.putText(vis, "Search Region", (640, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    # Gold standard match
    cv2.circle(vis, (800, legend_y-5), 5, (0, 255, 0), -1)
    cv2.putText(vis, "Gold Standard Match", (820, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    # Current match
    cv2.circle(vis, (1000, legend_y-5), 5, (255, 165, 0), -1)
    cv2.putText(vis, "Current Match", (1020, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Save visualization
    debug_dir = Path('debug/template_comparison')
    debug_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(debug_dir / 'button_matches.png'), vis)

if __name__ == "__main__":
    main() 