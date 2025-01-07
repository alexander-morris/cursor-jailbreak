# Button Detection Calibration Algorithm

## Overview
This document describes the high-precision button detection algorithm used for calibrating and detecting accept buttons. The algorithm uses a multi-stage approach combining edge detection, template matching, and verification to achieve highly accurate results.

## Calibration Process

### 1. Button State Capture
- Captures both pre-click and post-click states of each button
- Captures a 70x20 pixel region centered on the mouse cursor
- Stores relative coordinates to monitor boundaries
- Saves calibration data in `assets/monitor_2/` directory

### 2. Monitor Configuration
- Targets monitor 2 (third monitor) specifically
- Stores monitor metadata:
  - Resolution
  - Position (left, top coordinates)
  - Monitor boundaries
  - Monitor name

## Detection Algorithm

### 1. Initial Search Parameters
- Vertical search margin: ±80 pixels from calibration point
- Horizontal search margin: ±40 pixels from calibration point
- Template size: 70x20 pixels
- Maximum allowed horizontal deviation: 5 pixels
- Minimum match quality threshold: 0.5

### 2. Image Preprocessing
```python
Edge Detection Parameters:
- Canny edge detection thresholds: (50, 150)
- Edge dilation kernel: 2x2 matrix
- Dilation iterations: 1
```

### 3. Multi-Scale Template Matching
Scales tested: [1.0, 0.995, 1.005]

### 4. Match Scoring System
Match quality is calculated using a weighted combination:
- Direct template matching (50%): Using TM_CCOEFF_NORMED
- Edge overlap ratio (30%): Binary edge mask intersection
- Edge confidence (20%): Edge template matching score

### 5. Match Verification
Uses three methods with weighted scoring:
- Template correlation (60%): Using TM_CCORR_NORMED
- Mean squared error (30%): Normalized to 0-1 range
- Structural similarity (10%): Using scikit-image SSIM

### 6. Precision Requirements
- Horizontal precision: ±5 pixels
- Vertical tolerance: ±80 pixels
- Minimum verification threshold: 0.75
- Required edge match confidence: ≥0.3
- Required final match quality: >0.5

## Search Algorithm Details

### 1. First Pass: Edge Detection
1. Convert images to grayscale
2. Apply Canny edge detection
3. Dilate edges for robustness
4. Perform initial template matching on edges
5. Filter matches above 0.3 confidence

### 2. Second Pass: Direct Matching
For each potential match:
1. Extract region of interest (ROI)
2. Perform grayscale template matching
3. Calculate edge overlap ratio
4. Compute combined match quality
5. Track best match based on:
   - Horizontal distance to calibration point
   - Match quality score

### 3. Final Verification
1. Move to match position
2. Capture current state
3. Compare with template using:
   - Template correlation
   - Mean squared error
   - Structural similarity
4. Save debug images for visual verification

## File Structure

### Calibration Data
```
assets/monitor_2/
├── button_1_pre.png
├── button_1_post.png
├── click_coords_1.txt
├── button_2_pre.png
├── button_2_post.png
├── click_coords_2.txt
├── button_3_pre.png
├── button_3_post.png
└── click_coords_3.txt
```

### Debug Output
```
debug/
├── button_1_template.png
├── button_1_current.png
├── button_2_template.png
├── button_2_current.png
├── button_3_template.png
└── button_3_current.png
```

## Performance Characteristics

### Match Quality Thresholds
- Excellent match: >0.95
- Good match: 0.75-0.95
- Marginal match: 0.5-0.75
- Failed match: <0.5

### Timing Considerations
- 0.5 second delay for mouse movement
- Additional 0.5 second delay for state stabilization

## Error Handling

### Boundary Conditions
- Validates coordinates against monitor bounds
- Ensures search regions don't exceed screen boundaries
- Handles template size mismatches

### Match Validation
- Requires matches within horizontal precision
- Verifies match quality meets minimum threshold
- Performs multi-method verification
- Saves debug images for failed matches

## Implementation Notes

### Critical Dependencies
- OpenCV (cv2)
- NumPy
- MSS (screen capture)
- PyAutoGUI (mouse control)
- scikit-image (optional, for SSIM) 