"""
Main window for the Cursor Auto Accept application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import mss
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageTk
import time
import traceback
import pyautogui
from src.core.calibrator import Calibrator
from src.core.button_detector import ButtonDetector
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger
from src.utils.settings import Settings

logger = get_logger(__name__)

class MainWindow:
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Cursor Auto Accept")
        self.root.geometry("800x600")
        
        # Initialize components
        self.calibrator = Calibrator()
        self.detector = ButtonDetector()
        self.settings = Settings()
        self.is_clicking = False  # Track clicking state
        
        # Configure pyautogui
        pyautogui.PAUSE = 0.1  # Add small delay between actions
        pyautogui.FAILSAFE = True  # Enable failsafe
        
        # Get list of monitors
        try:
            with mss.mss() as sct:
                self.monitors = sct.monitors[1:]  # Skip primary monitor
                
            # Log monitor info
            for i, m in enumerate(self.monitors):
                logger.info(f"Found monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
                
            # Create UI elements
            self._create_widgets()
            
            # Load last monitor selection
            last_monitor = self.settings.get_last_monitor()
            if last_monitor is not None and last_monitor < len(self.monitors):
                self.monitor_var.set(last_monitor)
                
            # Update calibration status
            self._update_calibration_status()
                
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to initialize application: {e}")
            raise
            
    def _create_widgets(self):
        """Create the UI widgets."""
        # Monitor selection
        monitor_frame = ttk.LabelFrame(self.root, text="Monitor Selection", padding=10)
        monitor_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.monitor_var = tk.IntVar(value=0)
        for i, m in enumerate(self.monitors):
            ttk.Radiobutton(
                monitor_frame,
                text=f"Monitor {i} ({m['width']}x{m['height']})",
                variable=self.monitor_var,
                value=i,
                command=self._on_monitor_selected
            ).pack(side=tk.LEFT, padx=5)
            
        # Button count selection
        button_count_frame = ttk.LabelFrame(self.root, text="Number of Buttons", padding=10)
        button_count_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.button_count_var = tk.IntVar(value=3)  # Default to 3 buttons
        ttk.Label(button_count_frame, text="Select number of buttons to calibrate:").pack(side=tk.LEFT, padx=5)
        button_count_spinbox = ttk.Spinbox(
            button_count_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.button_count_var
        )
        button_count_spinbox.pack(side=tk.LEFT, padx=5)
            
        # Calibration frame
        calibration_frame = ttk.LabelFrame(self.root, text="Calibration", padding=10)
        calibration_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.calibration_status = ttk.Label(calibration_frame, text="Not calibrated")
        self.calibration_status.pack(side=tk.TOP, pady=5)
        
        # Instructions label
        self.instructions_label = ttk.Label(
            calibration_frame,
            text="Click 'Start Calibration' to begin",
            wraplength=600,
            justify=tk.LEFT
        )
        self.instructions_label.pack(side=tk.TOP, pady=5)
        
        button_frame = ttk.Frame(calibration_frame)
        button_frame.pack(side=tk.TOP, pady=5)
        
        ttk.Button(
            button_frame,
            text="Start Calibration",
            command=self._start_calibration
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Test Calibration",
            command=self._test_calibration
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-clicking frame
        clicking_frame = ttk.LabelFrame(self.root, text="Auto Clicking", padding=10)
        clicking_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.clicking_button = ttk.Button(
            clicking_frame,
            text="Start Clicking",
            command=self._toggle_clicking
        )
        self.clicking_button.pack(side=tk.LEFT, padx=5)
        
        self.clicking_status = ttk.Label(
            clicking_frame,
            text="Status: Stopped",
            foreground="red"
        )
        self.clicking_status.pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
    def _update_calibration_status(self):
        """Update the calibration status label."""
        try:
            monitor_index = self.monitor_var.get()
            monitor = self.monitors[monitor_index]
            
            if self.calibrator.check_calibration_data(monitor):
                self.calibration_status.config(text="Calibrated")
                self.instructions_label.config(text="Click 'Test Calibration' to verify the calibration")
            else:
                self.calibration_status.config(text="Not calibrated")
                self.instructions_label.config(text="Click 'Start Calibration' to begin")
                
        except Exception as e:
            logger.error(f"Failed to update calibration status: {e}")
            logger.error(traceback.format_exc())
            self.calibration_status.config(text="Error checking calibration")
        
    def _on_monitor_selected(self):
        """Handle monitor selection."""
        try:
            monitor_index = self.monitor_var.get()
            logger.info(f"Selected monitor {monitor_index}")
            self.settings.save_last_monitor(monitor_index)
            self._update_calibration_status()
            
        except Exception as e:
            logger.error(f"Failed to handle monitor selection: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to select monitor: {e}")
        
    def _start_calibration(self):
        """Start the calibration process."""
        try:
            monitor_index = self.monitor_var.get()
            monitor = self.monitors[monitor_index]
            logger.info(f"Starting calibration for monitor {monitor_index}")
            
            # Add monitor index for mss
            monitor['mon'] = monitor_index + 1  # mss uses 1-based indices
            
            # Get number of buttons to calibrate
            num_buttons = self.button_count_var.get()
            
            # Calibrate each button
            button_data = []
            for i in range(1, num_buttons + 1):
                logger.info(f"Calibrating button {i}...")
                self.instructions_label.config(
                    text=f"Calibrating button {i} of {num_buttons}...\nHover over the button and wait for countdown"
                )
                self.root.update()
                
                x, y, pre_click, post_click = self.calibrator.capture_button_state(i, monitor)
                button_data.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'template': pre_click
                })
                
                logger.info(f"Captured button {i} at ({x}, {y})")
                
            # Update calibration status
            self._update_calibration_status()
            
            # Show success message in instructions
            self.instructions_label.config(text=f"Calibration completed successfully for {num_buttons} buttons!")
            
        except Exception as e:
            logger.error(f"Failed to calibrate: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to calibrate: {e}")
            self.instructions_label.config(text="Calibration failed. Please try again.")
            
    def _test_calibration(self):
        """Test the calibration by finding matches."""
        try:
            monitor_index = self.monitor_var.get()
            monitor = self.monitors[monitor_index]
            
            # Add monitor index for mss
            monitor['mon'] = monitor_index + 1  # mss uses 1-based indices
            
            # Update instructions
            self.instructions_label.config(text="Testing calibration...")
            self.root.update()
            
            # Load calibration data
            button_data = self.calibrator.load_calibration_data(monitor)
            if not button_data:
                self.instructions_label.config(text="No calibration data found. Please calibrate first.")
                return
                
            # Find matches
            matches = self.detector.find_matches(monitor, button_data)
            
            if not matches:
                self.instructions_label.config(text="No matches found in current screen.")
                return
                
            # Create visualization
            vis_path = self.detector.create_visualization(monitor, matches)
            
            # Show visualization in new window
            self._show_visualization(vis_path)
            
            # Update instructions
            self.instructions_label.config(text=f"Found {len(matches)} matches. Check the visualization window.")
            
        except Exception as e:
            logger.error(f"Failed to test calibration: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to test calibration: {e}")
            self.instructions_label.config(text="Testing failed. Please try again.")
        
    def _show_visualization(self, image_path):
        """Show the visualization in a new window."""
        try:
            vis_window = tk.Toplevel(self.root)
            vis_window.title("Calibration Test Results")
            
            # Load and resize image if needed
            image = Image.open(image_path)
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate scaling factor to fit screen
            scale_width = screen_width / image.width
            scale_height = screen_height / image.height
            scale = min(scale_width, scale_height, 1.0)  # Don't upscale
            
            if scale < 1.0:
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Create canvas to display image
            canvas = tk.Canvas(
                vis_window,
                width=image.width,
                height=image.height
            )
            canvas.pack()
            
            # Display image
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo  # Keep reference
            
            # Add close button
            ttk.Button(
                vis_window,
                text="Close",
                command=vis_window.destroy
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Failed to show visualization: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to show visualization: {e}")
        
    def _toggle_clicking(self):
        """Toggle the auto-clicking state."""
        try:
            if not self.is_clicking:
                # Check calibration
                monitor_index = self.monitor_var.get()
                monitor = self.monitors[monitor_index]
                
                if not self.calibrator.check_calibration_data(monitor):
                    messagebox.showerror("Error", "Please calibrate the buttons first.")
                    return
                
                # Start clicking
                self.is_clicking = True
                self.clicking_button.config(text="Stop Clicking")
                self.clicking_status.config(text="Status: Running", foreground="green")
                
                # Add monitor index for mss
                monitor['mon'] = monitor_index + 1  # mss uses 1-based indices
                
                # Load calibration data
                self.button_data = self.calibrator.load_calibration_data(monitor)
                
                # Start checking for buttons
                self.root.after(100, self._check_and_click)
                logger.info("Auto-clicking started")
                
            else:
                # Stop clicking
                self.is_clicking = False
                self.clicking_button.config(text="Start Clicking")
                self.clicking_status.config(text="Status: Stopped", foreground="red")
                logger.info("Auto-clicking stopped")
                
        except Exception as e:
            logger.error(f"Failed to toggle clicking: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to toggle clicking: {e}")
            self.is_clicking = False
            self.clicking_button.config(text="Start Clicking")
            self.clicking_status.config(text="Status: Error", foreground="red")
            
    def _check_and_click(self):
        """Check for buttons and click them if found."""
        try:
            if not self.is_clicking:
                return
                
            monitor_index = self.monitor_var.get()
            monitor = self.monitors[monitor_index]
            monitor['mon'] = monitor_index + 1
            
            # Find matches
            matches = self.detector.find_matches(monitor, self.button_data)
            
            if matches:
                logger.info(f"Found {len(matches)} buttons to click")
                for match in matches:
                    # Get button coordinates
                    x, y = int(match['x']), int(match['y'])
                    logger.info(f"Clicking button {match['button_index']} at ({x}, {y})")
                    
                    # Convert monitor-relative coordinates to screen coordinates
                    screen_x = monitor['left'] + x
                    screen_y = monitor['top'] + y
                    
                    # Move mouse and click
                    try:
                        # Move mouse smoothly to button
                        pyautogui.moveTo(screen_x, screen_y, duration=0.2)
                        # Click and wait briefly
                        pyautogui.click(screen_x, screen_y)
                        time.sleep(0.1)  # Wait for click to register
                    except pyautogui.FailSafeException:
                        logger.warning("Failsafe triggered - mouse moved to corner")
                        self.is_clicking = False
                        self.clicking_button.config(text="Start Clicking")
                        self.clicking_status.config(text="Status: Stopped (Failsafe)", foreground="red")
                        return
            
            # Schedule next check
            self.root.after(100, self._check_and_click)
            
        except Exception as e:
            logger.error(f"Error in check and click: {e}")
            logger.error(traceback.format_exc())
            self.is_clicking = False
            self.clicking_button.config(text="Start Clicking")
            self.clicking_status.config(text="Status: Error", foreground="red")
        
    def run(self):
        """Start the application."""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application crashed: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Application crashed: {e}") 