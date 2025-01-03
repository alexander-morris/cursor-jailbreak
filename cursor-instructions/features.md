# Features

## Multi-Monitor Support
- Uses `mss` library for efficient screen capture across multiple monitors
- Supports per-monitor calibration with separate accept button images
- Maintains calibration images in monitor-specific directories
- Handles coordinate translation between monitor and screen space
- Rate limits clicks to 8 per minute across all monitors
- Includes error recovery with note detection and automatic continuation
- Preserves cursor position after clicking

### Implementation Details
1. Monitor Detection
   - Automatically detects all connected monitors
   - Stores monitor-specific information (resolution, position)
   - Creates calibration directories for each monitor

2. Screen Capture
   - Uses `mss` for fast, low-latency screen capture
   - Captures each monitor independently
   - Processes images in BGR format for OpenCV compatibility

3. Image Recognition
   - Uses template matching with confidence threshold
   - Supports different accept button appearances per monitor
   - Handles scaling and resolution differences

4. Click Handling
   - Translates monitor coordinates to screen coordinates
   - Preserves original cursor position
   - Implements rate limiting across all monitors
   - Logs successful clicks with monitor information

5. Error Recovery
   - Detects note icons across all monitors
   - Automatically types "continue" when note detected
   - Handles error conditions gracefully
   - Logs recovery actions for debugging

### Security Considerations
1. Rate Limiting
   - Maximum 8 clicks per minute
   - Prevents accidental rapid clicking
   - Logs rate limit events

2. Error Handling
   - Validates all image operations
   - Handles screen capture failures
   - Protects against coordinate overflow
   - Logs all errors with context

3. Resource Management
   - Efficient memory usage with screen capture
   - Proper cleanup of resources
   - Handles monitor hot-plug events
