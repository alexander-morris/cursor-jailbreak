import pyautogui
import time
import logging
import sys
import argparse
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta
import mss
import numpy as np
import cv2
from PIL import Image
from pynput import keyboard
import tkinter as tk
from threading import Thread, Event
from queue import Queue
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_bot.log'),
        logging.StreamHandler()
    ]
)

class MainWindow:
    def __init__(self, toggle_callback, calibrate_callback):
        self.root = tk.Tk()
        self.root.title("ClickBot")
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Set window size and position
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - window_width - 20
        y = 40  # Position near top of screen
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window semi-transparent and stay on top
        self.root.attributes("-alpha", 0.9, "-topmost", True)
        
        # Create main frame with blue background
        self.frame = tk.Frame(self.root, bg='#0066cc')
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create control frame at top
        self.control_frame = tk.Frame(self.frame, bg='#0066cc')
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add play/pause button
        self.is_playing = False
        self.toggle_button = tk.Button(
            self.control_frame,
            text="▶",  # Play symbol
            command=self.toggle,
            bg='#004999',
            fg='white',
            font=('Arial', 14),
            width=2
        )
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        
        # Add calibrate button
        self.calibrate_button = tk.Button(
            self.control_frame,
            text="⚙",  # Gear symbol
            command=self.calibrate,
            bg='#004999',
            fg='white',
            font=('Arial', 14),
            width=2
        )
        self.calibrate_button.pack(side=tk.LEFT, padx=5)
        
        # Add submit calibration button (hidden by default)
        self.submit_button = tk.Button(
            self.control_frame,
            text="✓",  # Checkmark symbol
            command=self.submit_calibration,
            bg='#004999',
            fg='white',
            font=('Arial', 14),
            width=2
        )
        
        # Add status label
        self.status_label = tk.Label(
            self.control_frame,
            text="Ready",
            bg='#0066cc',
            fg='white',
            font=('Arial', 12)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Create text widget for logs
        self.log_text = tk.Text(
            self.frame,
            height=15,
            bg='#0066cc',
            fg='white',
            font=('Courier', 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Store callbacks
        self.toggle_callback = toggle_callback
        self.calibrate_callback = calibrate_callback
        
        # Add drag functionality
        self.control_frame.bind('<Button-1>', self.start_drag)
        self.control_frame.bind('<B1-Motion>', self.on_drag)
        
        # Calibration state
        self.calibrating = False
        self.button_states = []
        self.capturing = False
        
    def start_drag(self, event):
        """Start window drag"""
        self.x = event.x
        self.y = event.y
        
    def on_drag(self, event):
        """Handle window drag"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def add_log(self, message):
        """Add a log message"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        # Keep only last 50 lines
        if float(self.log_text.index('end-1c').split('.')[0]) > 50:
            self.log_text.delete('1.0', '2.0')
        self.root.update()
        
    def clear_log(self):
        """Clear all log text"""
        self.log_text.delete('1.0', tk.END)
        self.root.update()
        
    def start_capture(self, sct):
        """Start capturing a button"""
        if self.capturing:
            return
            
        # Clear any pending after callbacks
        for after_id in self.root.tk.call('after', 'info'):
            self.root.after_cancel(after_id)
            
        self.capturing = True
        try:
            # Clear previous text
            self.clear_log()
            
            # Start hover capture countdown
            self.add_log("=== Capturing Accept Button ===")
            self.add_log("1. Move your cursor over the center of the button")
            self.add_log("2. Keep the cursor still")
            self.add_log("3. Wait for hover state capture")
            self.add_log("4. Click when prompted")
            self.add_log("5. Keep cursor still after clicking")
            self.add_log("\nStarting in 5 seconds...")
            
            def countdown_hover(count):
                if count > 0:
                    self.add_log(f"Capturing hover state in {count}...")
                    self.root.after(1000, lambda: countdown_hover(count - 1))
                else:
                    capture_hover()
            
            def capture_hover():
                # Capture hover state
                hover_x, hover_y = pyautogui.position()
                hover_region = {"top": hover_y-20, "left": hover_x-40, "width": 80, "height": 40}
                
                # Take multiple samples to ensure quality
                samples = []
                for i in range(3):
                    hover_screenshot = sct.grab(hover_region)
                    hover_img = Image.frombytes("RGB", hover_screenshot.size, hover_screenshot.rgb)
                    hover_np = np.array(hover_img)
                    hover_bgr = cv2.cvtColor(hover_np, cv2.COLOR_RGB2BGR)
                    
                    if hover_bgr.shape[0] != 40 or hover_bgr.shape[1] != 80:
                        hover_bgr = cv2.rotate(hover_bgr, cv2.ROTATE_90_CLOCKWISE)
                    
                    samples.append(hover_bgr)
                    time.sleep(0.1)
                
                # Use the middle sample to avoid any transition frames
                hover_bgr = samples[1]
                
                self.add_log("\nHover state captured!")
                self.add_log("Click the button now...")
                
                # Start click capture after a longer delay
                self.root.after(3000, lambda: countdown_click(3))
                
                return hover_x, hover_y, hover_bgr, hover_region
            
            def countdown_click(count):
                if count > 0:
                    self.add_log(f"Capturing after-click state in {count}...")
                    self.root.after(1000, lambda: countdown_click(count - 1))
                else:
                    capture_click()
            
            def capture_click():
                try:
                    # Store hover state
                    hover_x, hover_y, hover_bgr, hover_region = capture_hover()
                    
                    # Click the button
                    pyautogui.click()
                    time.sleep(0.5)  # Wait for button to disappear
                    
                    # Take multiple samples of after state
                    samples = []
                    for i in range(3):
                        after_screenshot = sct.grab(hover_region)
                        after_img = Image.frombytes("RGB", after_screenshot.size, after_screenshot.rgb)
                        after_np = np.array(after_img)
                        after_bgr = cv2.cvtColor(after_np, cv2.COLOR_RGB2BGR)
                        
                        if after_bgr.shape[0] != 40 or after_bgr.shape[1] != 80:
                            after_bgr = cv2.rotate(after_bgr, cv2.ROTATE_90_CLOCKWISE)
                        
                        samples.append(after_bgr)
                        time.sleep(0.1)
                    
                    # Use the last sample to ensure button has disappeared
                    after_bgr = samples[-1]
                    
                    # Verify the samples are consistent
                    diffs = []
                    for i in range(len(samples)-1):
                        diff = np.sum(np.abs(samples[i] - samples[i+1]))
                        diffs.append(diff)
                    
                    if max(diffs) > 1000:
                        self.add_log("\nWarning: Unstable after-click state")
                        self.add_log("Please try calibration again")
                        self.capturing = False
                        return
                    
                    # Store button state
                    self.button_states = [{
                        'hover_img': hover_bgr,
                        'hover_x': hover_x,
                        'hover_y': hover_y,
                        'after_img': after_bgr,
                        'click_x': hover_x,
                        'click_y': hover_y
                    }]
                    
                    self.add_log("\nButton captured successfully!")
                    self.add_log("\nPress checkmark to save and start the bot.")
                    
                    # Done capturing
                    self.capturing = False
                    
                except Exception as e:
                    self.add_log(f"\nError during click capture: {str(e)}")
                    self.capturing = False
            
            # Start the hover countdown
            countdown_hover(5)
            
        except Exception as e:
            self.add_log(f"\nError during capture: {str(e)}")
            self.capturing = False
            
    def finish_calibration(self, assets_dir):
        """Save calibration data"""
        if not self.button_states:
            self.add_log("\nNo button captured! Please capture the button first.")
            return False
        
        try:
            # First clean up any existing calibration files
            monitor_assets = assets_dir / "monitor_0"
            monitor_assets.mkdir(exist_ok=True)
            for file in monitor_assets.glob("*"):
                file.unlink()
            
            # Save button states
            hover_file = monitor_assets / 'accept_button.png'
            after_file = monitor_assets / 'accept_after.png'
            coords_file = monitor_assets / 'click_coords.txt'
            
            state = self.button_states[0]
            cv2.imwrite(str(hover_file), state['hover_img'])
            cv2.imwrite(str(after_file), state['after_img'])
            
            # Save coordinates
            with open(coords_file, 'w') as f:
                f.write(f"{state['hover_x']},{state['hover_y']}")
            
            self.add_log("\nCalibration complete! Bot will start running.")
            self.status_label.config(text="Ready")
            
            # Reset calibration state
            self.calibrating = False
            self.button_states = []
            self.capturing = False
            
            return True
            
        except Exception as e:
            self.add_log(f"\nError saving calibration: {str(e)}")
            return False
        
    def toggle(self):
        """Toggle play/pause state"""
        if self.calibrating and not self.capturing:
            return  # Ignore play button during calibration
            
        # Normal play/pause toggle
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.toggle_button.config(text="⏸")  # Pause symbol
            self.status_label.config(text="Running")
            # Clear any pending after callbacks
            for after_id in self.root.tk.call('after', 'info'):
                self.root.after_cancel(after_id)
        else:
            self.toggle_button.config(text="▶")  # Play symbol
            self.status_label.config(text="Stopped")
        self.toggle_callback()
        
    def calibrate(self):
        """Start calibration"""
        if self.capturing:
            return
            
        if not self.calibrating:
            # Starting new calibration
            self.calibrating = True
            self.button_states = []
            self.is_playing = False
            self.toggle_button.config(text="▶")
            self.status_label.config(text="Calibrating...")
            
            # Show submit button
            self.submit_button.pack(side=tk.LEFT, padx=5)
            
            # Show initial instructions
            self.clear_log()
            self.add_log("=== Cursor Auto Accept Calibration ===\n")
            self.add_log("We will calibrate by capturing multiple buttons.")
            self.add_log("For each button:")
            self.add_log("1. Move your cursor over the button")
            self.add_log("2. Wait for hover state capture (5 seconds)")
            self.add_log("3. When prompted, click the button")
            self.add_log("4. Wait for click state capture (3 seconds)")
            self.add_log("\nPress gear button to start capturing a button.")
            self.add_log("Press checkmark when done to save calibration.")
            
        else:
            # Already calibrating, start next capture
            self.calibrate_callback()
            
    def submit_calibration(self):
        """Submit calibration and start the bot"""
        if not self.calibrating or self.capturing:
            return
            
        # Hide submit button
        self.submit_button.pack_forget()
        
        # Save calibration and start bot
        assets_dir = self.toggle_callback()
        if assets_dir and self.finish_calibration(assets_dir):
            # Calibration saved successfully, now start the bot
            self.is_playing = True
            self.toggle_button.config(text="⏸")  # Pause symbol
            self.status_label.config(text="Running")
            # Clear any pending after callbacks
            for after_id in self.root.tk.call('after', 'info'):
                self.root.after_cancel(after_id)
            # Start the bot without calling toggle_callback again
            self.toggle_callback()
            
    def show(self):
        """Show the window"""
        self.root.mainloop()
        
    def close(self):
        """Close the window"""
        self.root.destroy()

    def start_calibrate_hold(self, event):
        """Start timing the calibrate button hold"""
        self.hold_start_time = time.time()
        # Schedule the hold check
        self.hold_after_id = self.root.after(1000, self.check_calibrate_hold)
        
    def stop_calibrate_hold(self, event):
        """Handle calibrate button release"""
        if self.hold_after_id:
            self.root.after_cancel(self.hold_after_id)
            self.hold_after_id = None
        
        # If released before 1 second, treat as normal click
        if self.hold_start_time and time.time() - self.hold_start_time < 1.0:
            if self.calibrating and not self.capturing:
                # Start next capture
                self.calibrate_callback()
            else:
                # Start calibration
                self.calibrate()
                
        self.hold_start_time = None
        
    def check_calibrate_hold(self):
        """Check if calibrate button has been held long enough"""
        if self.hold_start_time and time.time() - self.hold_start_time >= 1.0:
            if self.calibrating and not self.capturing:
                # Stop calibration
                self.calibrating = False
                self.status_label.config(text="Ready")
                self.add_log("\nCalibration stopped.")
                self.button_states = []
            self.hold_start_time = None

class StatusWindow:
    def __init__(self, message, duration=2.0):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Set window size and position
        window_width = 300
        window_height = 100
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window semi-transparent
        self.root.attributes("-alpha", 1.0)
        
        # Add message label
        self.label = tk.Label(
            self.root, 
            text=message,
            font=("Arial", 14),
            pady=20
        )
        self.label.pack(expand=True)
        
        self.duration = duration
        self.start_time = time.time()
        
        # Start fade out animation
        self.fade_out()
        
    def fade_out(self):
        elapsed = time.time() - self.start_time
        if elapsed < self.duration:
            # Calculate opacity (1.0 to 0.0)
            opacity = 1.0 - (elapsed / self.duration)
            self.root.attributes("-alpha", opacity)
            self.root.after(50, self.fade_out)
        else:
            self.root.destroy()
            
    def show(self):
        self.root.mainloop()

class CalibrationWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ClickBot Calibration")
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Set window size and position
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window transparent and blue
        self.root.attributes("-alpha", 0.9, "-topmost", True)  # Keep on top
        
        # Create main frame with blue background
        self.frame = tk.Frame(self.root, bg='#0066cc')
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget for instructions and logs
        self.text = tk.Text(
            self.frame,
            height=15,
            bg='#0066cc',
            fg='white',
            font=('Arial', 12),
            wrap=tk.WORD
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add close button
        self.close_button = tk.Button(
            self.frame,
            text="Close",
            command=self.close,
            bg='#004999',
            fg='white',
            font=('Arial', 12)
        )
        self.close_button.pack(pady=10)
        
        # Flag to track if window is closing
        self.is_closing = False
        
    def add_text(self, message):
        """Add text to the window"""
        if not self.is_closing:
            self.text.insert(tk.END, message + '\n')
            self.text.see(tk.END)  # Auto-scroll to bottom
            self.root.update()  # Force update UI
            
    def clear_text(self):
        """Clear all text"""
        if not self.is_closing:
            self.text.delete('1.0', tk.END)
            self.root.update()
        
    def close(self):
        """Close the window"""
        if not self.is_closing:
            self.is_closing = True
            self.root.quit()
            self.root.destroy()
        
    def show(self):
        """Show the window"""
        if not self.is_closing:
            self.root.mainloop()

    def update(self):
        """Force update the window"""
        if not self.is_closing:
            self.root.update()

    def after(self, ms, func):
        """Schedule a function to run after ms milliseconds"""
        if not self.is_closing:
            self.root.after(ms, func)

class CursorAutoAccept:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sct = mss.mss()
        
        # Rate limiting: max 8 clicks per minute
        self.click_history = deque(maxlen=8)
        self.MAX_CLICKS_PER_MINUTE = 8
        
        # Ensure assets directory exists
        self.assets_dir = Path('assets')
        self.assets_dir.mkdir(exist_ok=True)
        
        # Initialize monitor info
        self.monitors = self.get_monitors()
        self.logger.info(f"Found {len(self.monitors)} monitors")
        for i, m in enumerate(self.monitors):
            self.logger.info(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
            
        # Control flags
        self.running = False
        self.stop_event = Event()
        self.calibrating = False
        
        # Initialize windows
        self.main_window = None
        self.calibration_window = None
        
    def create_main_window(self):
        """Create the main window in the main thread"""
        self.main_window = MainWindow(self.toggle_bot, self.start_calibration)
        self.main_window.show()
            
    def start_calibration(self):
        """Start the calibration process"""
        # Stop the bot if it's running
        if self.running:
            self.stop_event.set()
            self.running = False
            self.logger.info("Bot stopped for calibration")
            
        # Start capture in main window
        self.main_window.start_capture(self.sct)
            
    def toggle_bot(self):
        """Toggle bot on/off"""
        if self.main_window.calibrating and not self.main_window.capturing:
            # Return assets directory for saving calibration
            return self.assets_dir
            
        if self.running:
            self.stop_event.set()
            self.running = False
            self.logger.info("Bot stopped via control window")
            if self.main_window:
                self.main_window.add_log("Bot stopped")
        else:
            # Check if calibration exists
            monitor_assets = self.assets_dir / "monitor_0"
            hover_file = monitor_assets / 'accept_button.png'
            after_file = monitor_assets / 'accept_after.png'
            coords_file = monitor_assets / 'click_coords.txt'
            
            if not all(f.exists() for f in [hover_file, after_file, coords_file]):
                # Reset play button since we're going to calibrate
                if self.main_window:
                    self.main_window.is_playing = False
                    self.main_window.toggle_button.config(text="▶")
                    self.main_window.status_label.config(text="Calibrating...")
                    self.main_window.calibrating = True
                    self.main_window.calibrate()  # Show initial instructions
                return
                
            # Start the bot
            self.stop_event.clear()
            self.running = True
            self.logger.info("Bot started via control window")
            if self.main_window:
                self.main_window.add_log("Bot started")
                self.main_window.calibrating = False  # Ensure calibration state is cleared
            # Start bot in new thread
            Thread(target=self.run_bot, daemon=True).start()
            
    def run_bot(self):
        """Main bot loop"""
        self.logger.info("Starting Cursor Auto Accept Bot")
        if self.main_window:
            self.main_window.add_log("Starting Cursor Auto Accept Bot")
        
        last_not_found_log = 0
        
        while not self.stop_event.is_set():
            if self.find_and_click_accept():
                time.sleep(0.5)
            else:
                current_time = time.time()
                if current_time - last_not_found_log >= 5:
                    message = "Still searching for accept button..."
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    last_not_found_log = current_time
                time.sleep(0.2)
                
    def run(self):
        """Initialize and start the bot"""
        self.logger.info("Bot initialized. Use control window to start/stop")
        # Create and show main window in main thread
        self.create_main_window()

    def get_monitors(self):
        """Get list of all monitors"""
        monitors = []
        for m in self.sct.monitors[1:]:  # Skip the "all monitors" monitor
            # Adjust monitor coordinates to be relative to primary monitor
            monitors.append({
                "left": m["left"],
                "top": m["top"],
                "width": m["width"],
                "height": m["height"]
            })
            self.logger.info(f"Monitor found: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
        # Only use the first monitor
        return [monitors[0]]

    def _ensure_monitor_calibration(self, monitor_index):
        """Ensure calibration file exists for a monitor"""
        monitor_assets = self.assets_dir / f"monitor_{monitor_index}"
        monitor_assets.mkdir(exist_ok=True)
        return monitor_assets / 'accept_button.png'

    def capture_accept_button(self, specific_monitor=None):
        """Capture the accept button image for one or all monitors"""
        monitor_index = specific_monitor if specific_monitor is not None else 0

        print(f"\n=== Cursor Auto Accept Calibration for Monitor {monitor_index} ===")
        print(f"Monitor at position: ({self.monitors[monitor_index]['left']}, {self.monitors[monitor_index]['top']})")
        print("1. Move Cursor to this monitor")
        print("2. Trigger an AI prompt")
        print("3. Move your mouse over the center of the accept button")
        print("4. Keep it there for 5 seconds")
        print("5. Don't move until capture is complete")
        print("\nStarting capture in 5 seconds...")
        time.sleep(5)
        
        # Get mouse position - this will be our click point
        click_x, click_y = pyautogui.position()
        
        # Capture region around mouse with original working size
        region = {"top": click_y-20, "left": click_x-40, "width": 80, "height": 40}
        screenshot = self.sct.grab(region)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        
        # Convert to OpenCV format
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # Ensure template is in correct orientation (80x40)
        if img_bgr.shape[0] != 40 or img_bgr.shape[1] != 80:
            self.logger.warning(f"Template has wrong dimensions: {img_bgr.shape}, rotating...")
            img_bgr = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
            self.logger.info(f"New template dimensions: {img_bgr.shape}")
        
        # Save template
        monitor_assets = self.assets_dir / f"monitor_{monitor_index}"
        monitor_assets.mkdir(exist_ok=True)
        calibration_file = monitor_assets / 'accept_button.png'
        coords_file = monitor_assets / 'click_coords.txt'
        
        cv2.imwrite(str(calibration_file), img_bgr)  # Save in BGR format
        # Save click offset from template top-left
        with open(coords_file, 'w') as f:
            f.write(f"40,20")  # Center of 80x40 region
            
        print(f"\nCalibration complete for monitor {monitor_index}!")
        print(f"Saved accept button image to {calibration_file}")

    def can_click(self):
        """Check if we haven't exceeded rate limit"""
        now = datetime.now()
        # Remove clicks older than 1 minute
        while self.click_history and (now - self.click_history[0]) > timedelta(minutes=1):
            self.click_history.popleft()
        
        return len(self.click_history) < self.MAX_CLICKS_PER_MINUTE

    def monitor_click_area(self, x, y, monitor, timeout=20):
        """Monitor the area around a click for changes"""
        # Define the button region (same size as calibration)
        button_region = {"top": y-20, "left": x-40, "width": 80, "height": 40}
        
        # Get initial screenshot of button area
        initial = np.array(self.sct.grab(button_region))
        time.sleep(0.2)  # Small delay to let UI start changing
        
        start_time = time.time()
        last_change_time = start_time
        
        message = "Monitoring for button disappearance..."
        self.logger.info(message)
        if self.main_window:
            self.main_window.add_log(message)
        
        # Load the hover template to check if button is still there
        monitor_assets = self.assets_dir / "monitor_0"
        hover_file = monitor_assets / 'accept_button.png'
        
        if hover_file.exists():
            hover_template = cv2.imread(str(hover_file))
            if hover_template is not None:
                # Ensure template is in correct orientation
                if hover_template.shape[0] != 40 or hover_template.shape[1] != 80:
                    hover_template = cv2.rotate(hover_template, cv2.ROTATE_90_CLOCKWISE)
                
                while time.time() - start_time < timeout:
                    # Capture current state of button area
                    current = np.array(self.sct.grab(button_region))
                    current_bgr = cv2.cvtColor(current, cv2.COLOR_BGRA2BGR)
                    
                    # Check if button is still visible
                    result = cv2.matchTemplate(current_bgr, hover_template, cv2.TM_CCOEFF_NORMED)
                    confidence = result.max()
                    
                    message = f"Button visibility confidence: {confidence:.3f}"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    if confidence < 0.6:  # Button is no longer visible
                        message = "Button appears gone (low confidence)"
                        self.logger.info(message)
                        if self.main_window:
                            self.main_window.add_log(message)
                        return True
                    
                    elif time.time() - last_change_time > 1.0:  # No changes for 1 second
                        message = "Button still visible, clicking again..."
                        self.logger.info(message)
                        if self.main_window:
                            self.main_window.add_log(message)
                        pyautogui.click(x, y)
                        time.sleep(0.1)
                        pyautogui.click(x, y)
                        last_change_time = time.time()
                    
                    time.sleep(0.1)
        
        message = "Monitoring timed out"
        self.logger.warning(message)
        if self.main_window:
            self.main_window.add_log(message)
        return False

    def find_and_click_accept(self):
        if not self.can_click():
            message = "Rate limit reached (8 clicks/minute). Waiting..."
            self.logger.info(message)
            if self.main_window:
                self.main_window.add_log(message)
            return False
            
        try:
            # Store current mouse position
            original_x, original_y = pyautogui.position()
            
            # Only check monitor 0
            monitor = self.monitors[0]
            monitor_assets = self.assets_dir / "monitor_0"
            
            # Log monitor info for debugging
            self.logger.info(f"Using monitor: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Check for calibration files
            hover_file = monitor_assets / 'accept_button.png'
            after_file = monitor_assets / 'accept_after.png'
            coords_file = monitor_assets / 'click_coords.txt'
            
            if not all(f.exists() for f in [hover_file, after_file, coords_file]):
                message = "Missing calibration files. Please run calibration first."
                self.logger.warning(message)
                if self.main_window:
                    self.main_window.add_log(message)
                return False
            
            # Load template
            hover_template = cv2.imread(str(hover_file))
            if hover_template is None:
                message = "Failed to load template"
                self.logger.error(message)
                if self.main_window:
                    self.main_window.add_log(message)
                return False
            
            # Ensure template is in correct orientation (80x40)
            if hover_template.shape[0] != 40 or hover_template.shape[1] != 80:
                hover_template = cv2.rotate(hover_template, cv2.ROTATE_90_CLOCKWISE)
            
            try:
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Try different matching methods
                methods = [
                    (cv2.TM_CCOEFF_NORMED, 0.6),  # Method, threshold
                    (cv2.TM_CCORR_NORMED, 0.8),
                    (cv2.TM_SQDIFF_NORMED, 0.2)  # For SQDIFF, lower is better
                ]
                
                best_match = None
                best_confidence = -1
                
                for method, threshold in methods:
                    # Match against hover template
                    result = cv2.matchTemplate(img_bgr, hover_template, method)
                    
                    if method == cv2.TM_SQDIFF_NORMED:
                        # For SQDIFF, we want minimum value
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = 1.0 - min_val  # Convert to confidence
                        loc = min_loc
                    else:
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = max_val
                        loc = max_loc
                    
                    message = f"Method {method} confidence: {confidence:.3f}"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    # Check if this match is better
                    if method == cv2.TM_SQDIFF_NORMED:
                        if confidence > (1.0 - threshold) and confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'confidence': confidence,
                                'relative_x': loc[0],
                                'relative_y': loc[1]
                            }
                    else:
                        if confidence > threshold and confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'confidence': confidence,
                                'relative_x': loc[0],
                                'relative_y': loc[1]
                            }
                
                # Take best match
                if best_match:
                    message = f"\nBest match confidence: {best_match['confidence']:.3f}"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                        
                    # Calculate screen coordinates relative to monitor
                    click_x = monitor["left"] + best_match['relative_x'] + 40  # Center of template
                    click_y = monitor["top"] + best_match['relative_y'] + 20
                    
                    # Log coordinates for debugging
                    message = f"Match at ({best_match['relative_x']}, {best_match['relative_y']}) in monitor"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    message = f"Screen position: ({click_x}, {click_y})"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    # Ensure coordinates are within screen bounds
                    screen_width = monitor["width"] + monitor["left"]
                    screen_height = monitor["height"] + monitor["top"]
                    click_x = max(monitor["left"] + 10, min(click_x, screen_width - 10))
                    click_y = max(monitor["top"] + 10, min(click_y, screen_height - 10))
                    
                    # Move to position and click
                    message = "Moving to button position..."
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    pyautogui.moveTo(click_x, click_y)
                    time.sleep(0.1)  # Small delay
                    
                    message = "Performing click..."
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    pyautogui.click()
                    time.sleep(0.1)  # Small delay between clicks
                    pyautogui.click()  # Double click to ensure it registers
                    self.click_history.append(datetime.now())
                    
                    # Monitor the click area for changes
                    message = "Monitoring click area for changes..."
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    self.monitor_click_area(click_x, click_y, monitor)
                    
                    # Restore original cursor position
                    message = "Restoring cursor position..."
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    restore_x = max(monitor["left"] + 10, min(original_x, screen_width - 10))
                    restore_y = max(monitor["top"] + 10, min(original_y, screen_height - 10))
                    pyautogui.moveTo(restore_x, restore_y)
                    return True
                else:
                    message = "No matches found above confidence threshold"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    return False
                    
            except Exception as e:
                message = f"Error finding matches: {str(e)}"
                self.logger.error(message)
                if self.main_window:
                    self.main_window.add_log(message)
                return False
            
        except Exception as e:
            message = f"Unexpected error: {str(e)}"
            self.logger.error(message)
            if self.main_window:
                self.main_window.add_log(message)
            return False

def main():
    parser = argparse.ArgumentParser(description='Cursor Auto Accept Bot')
    parser.add_argument('--capture', action='store_true', help='Force recalibration by capturing new accept button images')
    parser.add_argument('--monitor', type=int, help='Calibrate a specific monitor (0-based index)')
    parser.add_argument('--test', action='store_true', help='Run in test mode with 10s timeout')
    args = parser.parse_args()

    bot = CursorAutoAccept()
    
    if args.capture:
        bot.capture_accept_button(args.monitor)
        return

    if args.test:
        print("Test mode: Will exit after 10 seconds")
        Thread(target=lambda: time.sleep(10) or sys.exit(0), daemon=True).start()
        
    bot.run()

if __name__ == "__main__":
    main() 