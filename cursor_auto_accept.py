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
        
    def toggle(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.toggle_button.config(text="⏸")  # Pause symbol
            self.status_label.config(text="Running")
        else:
            self.toggle_button.config(text="▶")  # Play symbol
            self.status_label.config(text="Stopped")
        self.toggle_callback()
        
    def add_log(self, message):
        """Add a log message"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        # Keep only last 50 lines
        if float(self.log_text.index('end-1c').split('.')[0]) > 50:
            self.log_text.delete('1.0', '2.0')
        
    def show(self):
        """Show the window"""
        self.root.mainloop()
        
    def close(self):
        """Close the window"""
        self.root.destroy()
        
    def calibrate(self):
        """Start calibration"""
        # Reset play button state
        self.is_playing = False
        self.toggle_button.config(text="▶")
        self.status_label.config(text="Calibrating...")
        self.calibrate_callback()

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
            
        self.calibrating = True
        self.calibration_window = CalibrationWindow()
        
        def run_calibration():
            self.calibration_window.add_text("=== Cursor Auto Accept Calibration ===\n")
            self.calibration_window.add_text("1. Move your cursor to the monitor you want to calibrate")
            self.calibration_window.add_text("2. Trigger an AI prompt")
            self.calibration_window.add_text("3. Move your mouse over the center of the accept button")
            self.calibration_window.add_text("4. Keep it there for 5 seconds")
            self.calibration_window.add_text("5. Don't move until capture is complete")
            self.calibration_window.add_text("\nStarting capture in 5 seconds...")
            
            self.calibration_window.root.update()  # Force update
            time.sleep(5)
            
            try:
                # Get mouse position
                click_x, click_y = pyautogui.position()
                
                # Capture region around mouse with larger area
                region = {"top": click_y-30, "left": click_x-75, "width": 150, "height": 60}
                screenshot = self.sct.grab(region)
                
                # Convert to PIL Image and save
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # Save calibration files
                monitor_assets = self.assets_dir / "monitor_0"
                monitor_assets.mkdir(exist_ok=True)
                calibration_file = monitor_assets / 'accept_button.png'
                coords_file = monitor_assets / 'click_coords.txt'
                
                img.save(calibration_file)
                with open(coords_file, 'w') as f:
                    f.write(f"{75},{30}")  # Center of capture region
                    
                self.calibration_window.add_text("\nCalibration complete!")
                self.calibration_window.add_text(f"Saved accept button image to {calibration_file}")
                self.calibration_window.add_text("\nWindow will close in 3 seconds...")
                
                # Update main window status
                if self.main_window:
                    self.main_window.status_label.config(text="Ready")
                
                # Schedule window close
                self.calibration_window.root.after(3000, self.calibration_window.close)
                
            except Exception as e:
                self.calibration_window.add_text(f"\nError during calibration: {str(e)}")
                self.calibration_window.add_text("Please try again.")
                # Update main window status
                if self.main_window:
                    self.main_window.status_label.config(text="Calibration Failed")
            
            self.calibrating = False
            
        # Start calibration in a non-daemon thread
        calibration_thread = Thread(target=run_calibration)
        calibration_thread.start()
        
        # Show calibration window in main thread
        self.calibration_window.show()
            
    def toggle_bot(self):
        """Toggle bot on/off"""
        if self.calibrating:
            return
            
        if self.running:
            self.stop_event.set()
            self.running = False
            self.logger.info("Bot stopped via control window")
            if self.main_window:
                self.main_window.add_log("Bot stopped")
        else:
            # Check if calibration exists
            monitor_assets = self.assets_dir / "monitor_0"
            calibration_file = monitor_assets / 'accept_button.png'
            coords_file = monitor_assets / 'click_coords.txt'
            
            if not calibration_file.exists() or not coords_file.exists():
                # Reset play button since we're going to calibrate
                if self.main_window:
                    self.main_window.is_playing = False
                    self.main_window.toggle_button.config(text="▶")
                    self.main_window.status_label.config(text="Calibrating...")
                self.start_calibration()
                return
                
            self.stop_event.clear()
            self.running = True
            self.logger.info("Bot started via control window")
            if self.main_window:
                self.main_window.add_log("Bot started")
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
        monitors = self.sct.monitors[1:]  # Skip the "all monitors" monitor
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
        
        # Capture region around mouse with larger area
        region = {"top": click_y-30, "left": click_x-75, "width": 150, "height": 60}
        screenshot = self.sct.grab(region)
        
        # Convert to PIL Image and save
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        
        # Save both the template and click coordinates
        monitor_assets = self.assets_dir / f"monitor_{monitor_index}"
        monitor_assets.mkdir(exist_ok=True)
        calibration_file = monitor_assets / 'accept_button.png'
        coords_file = monitor_assets / 'click_coords.txt'
        
        img.save(calibration_file)
        # Save relative click coordinates
        with open(coords_file, 'w') as f:
            f.write(f"{75},{30}")  # Center of the capture region
            
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
        region = {
            "left": max(0, x - 100),
            "top": max(0, y - 100),
            "width": 200,
            "height": 200
        }
        
        # Get initial screenshot
        initial = np.array(self.sct.grab(region))
        time.sleep(0.2)  # Small delay to let UI start changing
        
        start_time = time.time()
        last_change_time = start_time
        prev_frame = initial
        textarea_clicked = False
        
        while time.time() - start_time < timeout:
            current = np.array(self.sct.grab(region))
            # Calculate pixel differences
            diff = np.sum(np.abs(current - prev_frame))
            
            if diff > 1000:  # Threshold for significant change
                last_change_time = time.time()
                if textarea_clicked:
                    message = "Detected UI change after textarea click"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    return
            elif time.time() - last_change_time > 15.0 and not textarea_clicked:  # No changes for 15 seconds
                message = "Area stalled for 15s, attempting textarea click..."
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                # Click the textarea (200px left, 68px down from original click)
                textarea_x = x - 200
                textarea_y = y + 68
                pyautogui.moveTo(textarea_x, textarea_y)
                pyautogui.click()
                textarea_clicked = True
                last_change_time = time.time()  # Reset timer to check for UI response
            elif time.time() - last_change_time > 1.0 and not textarea_clicked:  # No changes for 1 second
                message = "Click area appears stalled, attempting unstick..."
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                # Move mouse slightly and click again
                pyautogui.moveTo(x + 5, y + 5)
                pyautogui.click()
                pyautogui.moveTo(x, y)
                pyautogui.click()
                last_change_time = time.time()  # Reset timer
                
            prev_frame = current
            time.sleep(0.1)
        
        if textarea_clicked:
            message = "No UI changes detected after textarea click"
            self.logger.warning(message)
            if self.main_window:
                self.main_window.add_log(message)
        message = "Area monitoring timed out"
        self.logger.warning(message)
        if self.main_window:
            self.main_window.add_log(message)

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
            calibration_file = monitor_assets / 'accept_button.png'
            coords_file = monitor_assets / 'click_coords.txt'
            
            # Log monitor info
            message = f"Searching monitor: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})"
            self.logger.info(message)
            if self.main_window:
                self.main_window.add_log(message)
            
            if not calibration_file.exists() or not coords_file.exists():
                message = "No calibration found. Please run with --capture flag first."
                self.logger.warning(message)
                if self.main_window:
                    self.main_window.add_log(message)
                return False

            try:
                # Load the template image and click coordinates
                template = cv2.imread(str(calibration_file))
                if template is None:
                    message = f"Failed to load template from {calibration_file}"
                    self.logger.error(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    return False
                
                # Log template info
                template_h, template_w = template.shape[:2]
                message = f"Template size: {template_w}x{template_h}"
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                    
                with open(coords_file, 'r') as f:
                    rel_x, rel_y = map(int, f.read().strip().split(','))
                message = f"Click offset: ({rel_x}, {rel_y})"
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                # Convert to CV2 format
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Log screenshot info
                img_h, img_w = img_bgr.shape[:2]
                message = f"Screenshot size: {img_w}x{img_h}"
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                
                # Template matching with lower confidence threshold
                result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # Debug log the confidence value and location
                message = f"Best match at ({max_loc[0]}, {max_loc[1]}) with confidence: {max_val:.3f}"
                self.logger.info(message)
                if self.main_window:
                    self.main_window.add_log(message)
                
                # Save debug images
                debug_dir = Path('debug')
                debug_dir.mkdir(exist_ok=True)
                
                # Save the template
                cv2.imwrite(str(debug_dir / 'template.png'), template)
                
                # Save the full screenshot
                cv2.imwrite(str(debug_dir / 'full_screen.png'), img_bgr)
                
                # Save the region where match was found
                h, w = template.shape[:2]
                x, y = max_loc
                if x >= 0 and y >= 0 and x + w <= img_w and y + h <= img_h:
                    match_region = img_bgr[y:y+h, x:x+w]
                    cv2.imwrite(str(debug_dir / 'match_region.png'), match_region)
                    message = f"Saved debug images to {debug_dir}"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                
                if max_val >= 0.7:  # Lower confidence threshold
                    # Calculate absolute screen coordinates using saved click point
                    screen_x = monitor["left"] + max_loc[0] + rel_x
                    screen_y = monitor["top"] + max_loc[1] + rel_y
                    
                    message = f"Clicking at absolute coordinates: ({screen_x}, {screen_y})"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    # Click and restore cursor
                    pyautogui.click(screen_x, screen_y)
                    pyautogui.click(screen_x, screen_y)  # Double click to ensure it registers
                    self.click_history.append(datetime.now())
                    message = f"Clicked accept button at ({screen_x}, {screen_y}) with confidence {max_val:.2f}"
                    self.logger.info(message)
                    if self.main_window:
                        self.main_window.add_log(message)
                    
                    # Monitor the click area for changes
                    self.monitor_click_area(screen_x, screen_y, monitor)
                    
                    # Restore original cursor position
                    pyautogui.moveTo(original_x, original_y)
                    return True
                    
            except Exception as e:
                message = f"Error processing monitor: {str(e)}"
                self.logger.error(message)
                if self.main_window:
                    self.main_window.add_log(message)
                return False
            
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