import cv2
import numpy as np
import mss
import time
from pathlib import Path
import pyautogui

def analyze_template_match(template_path, threshold_range=(0.6, 0.9, 0.05)):
    # Initialize screen capture
    sct = mss.mss()
    monitor = sct.monitors[1]  # First actual monitor
    
    # Load and verify template
    template = cv2.imread(str(template_path))
    if template is None:
        print(f"Failed to load template: {template_path}")
        return
        
    # Ensure template is in correct orientation (80x40)
    if template.shape[0] != 40 or template.shape[1] != 80:
        template = cv2.rotate(template, cv2.ROTATE_90_CLOCKWISE)
    
    print(f"\nAnalyzing template matching for: {template_path}")
    print(f"Template size: {template.shape}")
    
    # Capture and analyze screen
    screenshot = np.array(sct.grab(monitor))
    img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    # Try different threshold values
    start_thresh, end_thresh, step = threshold_range
    thresholds = np.arange(start_thresh, end_thresh, step)
    
    print("\nTesting different confidence thresholds:")
    print("Threshold | Matches | Max Confidence | Best Match Location")
    print("-" * 70)
    
    # Perform template matching
    result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
    max_val = result.max()
    max_loc = np.unravel_index(result.argmax(), result.shape)
    
    best_match_x = monitor["left"] + max_loc[1] + 40
    best_match_y = monitor["top"] + max_loc[0] + 20
    
    for threshold in thresholds:
        # Find matches above threshold
        locations = np.where(result >= threshold)
        matches = list(zip(*locations[::-1]))  # Convert to list of (x,y) points
        
        # Group nearby matches
        used = set()
        distinct_matches = []
        for x, y in matches:
            if (x, y) in used:
                continue
            
            # Mark nearby points as used
            for dx in range(-10, 11):
                for dy in range(-10, 11):
                    used.add((x + dx, y + dy))
            
            distinct_matches.append((x, y))
        
        print(f"{threshold:.2f}    | {len(distinct_matches):7d} | {max_val:.3f}      | ({best_match_x}, {best_match_y})")
    
    print("\nAnalysis Results:")
    print(f"- Template: {template_path.name}")
    print(f"- Max confidence: {max_val:.3f}")
    print(f"- Best match location: ({best_match_x}, {best_match_y})")
    
    # Move cursor to best match location
    print("\nMoving cursor to best match location for 2 seconds...")
    original_x, original_y = pyautogui.position()
    pyautogui.moveTo(best_match_x, best_match_y)
    time.sleep(2)
    pyautogui.moveTo(original_x, original_y)
    
    # Analyze match quality
    if max_val >= 0.8:
        print("Match Quality: EXCELLENT")
        print("Recommendation: Use threshold of 0.75")
    elif max_val >= 0.7:
        print("Match Quality: GOOD")
        print("Recommendation: Use threshold of 0.65")
    elif max_val >= 0.6:
        print("Match Quality: FAIR")
        print("Recommendation: Use threshold of 0.55 but verify matches")
    else:
        print("Match Quality: POOR")
        print("Recommendation: Recalibrate template")
    
    return max_val, best_match_x, best_match_y

def main():
    # Check for template files
    assets_dir = Path('assets/monitor_0')
    hover_file = assets_dir / 'accept_button.png'
    after_file = assets_dir / 'accept_after.png'
    
    if not hover_file.exists() or not after_file.exists():
        print("Template files not found. Please run calibration first.")
        return
    
    print("Template Analysis Tool")
    print("=====================")
    print("This tool will analyze the current templates and recommend settings.")
    print("Make sure an accept button is visible on screen.")
    input("Press Enter to start analysis...")
    
    # Analyze hover template
    print("\nAnalyzing hover template...")
    hover_conf, hover_x, hover_y = analyze_template_match(hover_file)
    
    # Analyze after template
    print("\nAnalyzing after-click template...")
    after_conf, after_x, after_y = analyze_template_match(after_file)
    
    print("\nOverall Analysis:")
    print(f"Hover template max confidence: {hover_conf:.3f}")
    print(f"After template max confidence: {after_conf:.3f}")
    
    if hover_conf < 0.6 or after_conf < 0.6:
        print("\nRecommendation: Recalibrate both templates")
    elif abs(hover_x - after_x) > 10 or abs(hover_y - after_y) > 10:
        print("\nWarning: Best match locations differ significantly")
        print("Recommendation: Recalibrate to ensure consistent positioning")
    else:
        print("\nTemplates appear to be working correctly")
        print(f"Recommended threshold: {min(0.75, hover_conf - 0.1):.2f}")

if __name__ == "__main__":
    main() 