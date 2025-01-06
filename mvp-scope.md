# Cursor Auto Accept - MVP Integration Scope

## Overview
Integration plan for the improved calibration and button detection system into the main clickbot application.

## Core Components

### 1. UI Components
- **Calibration Section**
  - Calibrate button
  - Debug Matches button (runs analyze_hover_results.py)
  - Last calibration timestamp
  - Status indicators per button type

- **Monitoring Section**
  - Start/Stop button
  - Live status display
  - Match confidence display
  - Current click rate
  - Active monitor indicator

- **Debug Section**
  - View Latest Matches button
  - Match history log
  - Error rate tracking
  - Button match statistics

### 2. Core Features
- **Button Group Detection**
  - X-axis position grouping (±20px)
  - Confidence + Y-axis position prioritization
  - Match history tracking

- **Enhanced Calibration**
  - Pre/post click image capture
  - Calibration coordinate storage
  - Match validation against calibration data

- **Debug Visualization**
  - Real-time match visualization
  - Color-coded button states (Green/Yellow/Red)
  - Confidence score overlay

### 3. File Structure
```
cursor-auto-accept/
├── src/
│   ├── ui/
│   │   ├── main_window.py      # Main UI
│   │   ├── calibration_tab.py  # Calibration UI
│   │   └── debug_tab.py        # Debug UI
│   ├── core/
│   │   ├── button_detector.py  # New detection logic
│   │   ├── calibrator.py       # New calibration logic
│   │   └── visualizer.py       # Debug visualization
│   └── utils/
│       ├── config.py           # Configuration
│       └── logging.py          # Enhanced logging
├── assets/
│   └── monitor_0/             # Calibration data
├── debug/                     # Debug output
└── logs/                     # Application logs
```

### 4. Configuration System
```python
class ClickBotConfig:
    # Detection Settings
    MATCH_CONFIDENCE_THRESHOLD = 0.9
    X_AXIS_GROUP_THRESHOLD = 20
    MIN_Y_POSITION_DELTA = 5

    # Visualization Settings
    BUTTON_COLORS = {
        'accept': (0, 255, 0),    # Green
        'suggest': (0, 255, 255), # Yellow
        'cancel': (0, 0, 255)     # Red
    }

    # Debug Settings
    SAVE_DEBUG_IMAGES = True
    MAX_DEBUG_HISTORY = 100
    VISUALIZATION_UPDATE_RATE = 1.0  # seconds
```

## Implementation Phases

### Phase 1: Core Integration
1. Port improved button detection algorithm
2. Implement match grouping logic
3. Add match validation system
4. Set up configuration system

### Phase 2: UI Development
1. Create new calibration workflow
2. Add debug visualization panel
3. Implement match statistics display
4. Add real-time status updates

### Phase 3: Testing & Validation
1. Unit tests for new components
2. Integration tests for full workflow
3. Visualization system tests
4. Performance benchmarking

### Phase 4: Documentation & Deployment
1. Update README with new features
2. Add debug visualization guide
3. Document configuration options
4. Create user guide for new features

## Success Criteria
- Successful button detection rate > 95%
- False positive rate < 1%
- Match confidence threshold ≥ 0.9
- Response time < 200ms
- Stable operation across multiple monitors

## Timeline
- Phase 1: 1 week
- Phase 2: 1 week
- Phase 3: 3 days
- Phase 4: 2 days

Total estimated time: 2.5 weeks 