# HustleBot Clicker

An automated UI interaction tool with two implementations:
1. `main.py` - Full-featured bot with multi-monitor support and advanced error recovery
2. `basic_clicker.py` - Simplified single-monitor implementation with calibration

## Project Structure
```
.
├── main.py              # Primary implementation
├── basic_clicker.py     # Secondary implementation
├── src/                 # Core dependencies
│   ├── image_matcher.py     # OpenCV-based image matching
│   ├── error_recovery.py    # Error handling and recovery
│   └── logging_config.py    # Logging configuration
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Basic Clicker (basic_clicker.py)

A simplified implementation with built-in calibration.

### Features
- Interactive calibration process
- Multiple target support
- Consecutive match verification
- Returns cursor to original position after clicks
- Development mode with timeout

### Usage

1. **Calibration Mode**:
```bash
python basic_clicker.py --calibrate
```

During calibration:
1. For each target you want to click:
   - When prompted, hover (don't click) over the button when it's visible
   - Press Enter
   - Wait for the button to disappear completely
   - Press Enter again
2. Repeat for additional targets
3. Type 'y' when done adding targets

2. **Normal Operation**:
```bash
python basic_clicker.py
```

3. **Development Mode** (30-second timeout):
```bash
python basic_clicker.py --dev
```

### Configuration
- Minimum click interval: 5.0 seconds
- Required consecutive matches: 2
- Similarity threshold: 0.65
- Match verification weight: 70% pixel difference, 30% exact matches

## Main Bot (main.py)

The full-featured implementation with advanced capabilities.

### Features
- Multi-monitor support
- Automatic window detection
- Advanced error recovery
- Resource cleanup
- Configurable cache clearing

### Usage

1. **Debug Mode** (recommended for first run):
```bash
python main.py --debug
```

2. **Custom Configuration**:
```bash
python main.py --interval 2.0 --confidence 0.8
```

### Command Line Options
```bash
python main.py [options]
  --debug            Enable debug logging
  --interval FLOAT   Scan interval in seconds (default: 3.0)
  --confidence FLOAT Confidence threshold (default: 0.8)
```

## Configuration Tips

### Confidence Threshold
- Start with default (0.8)
- Increase if getting false positives
- Decrease if missing valid targets
- Recommended ranges:
  - High accuracy: 0.8-0.9
  - Normal use: 0.7-0.8
  - Lenient: 0.6-0.7

### Scan Interval
- Default: 3.0 seconds
- Decrease for faster response
- Increase to reduce CPU usage
- Recommended ranges:
  - Fast response: 1.0-2.0
  - Normal use: 2.0-4.0
  - Low CPU: 4.0+

## Troubleshooting

### Basic Clicker Issues
1. **Calibration Problems**
   - Ensure clear button visibility during "present" state
   - Ensure complete button absence during "absent" state
   - Check mean difference values (should be > 5)

2. **False Positives/Negatives**
   - Increase consecutive match requirement
   - Adjust similarity threshold
   - Recalibrate with more distinct states

### Main Bot Issues
1. **Window Detection**
   - Run with --debug flag
   - Check monitor configuration
   - Verify window visibility

2. **Click Accuracy**
   - Increase confidence threshold
   - Check for window movement
   - Verify target coordinates

## Best Practices

1. **Target Selection**
   - Choose distinct, stable UI elements
   - Avoid areas with dynamic content
   - Calibrate during normal operation conditions

2. **Performance**
   - Balance interval vs CPU usage
   - Monitor memory usage
   - Clean logs periodically

3. **Testing**
   - Always test in safe environments
   - Use development mode for initial setup
   - Monitor logs during operation

## License

MIT License - Feel free to modify and distribute 