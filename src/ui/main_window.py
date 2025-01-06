"""
Main window UI for the Cursor Auto Accept application.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import threading
from datetime import datetime
from src.utils.config import ClickBotConfig
from src.utils.logging import get_logger, QueueHandler
from src.core.calibrator import Calibrator
from src.core.button_detector import ButtonDetector

logger = get_logger(__name__)

class MainWindow:
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Cursor Auto Accept")
        self.root.geometry("800x600")
        
        # Components
        self.calibrator = Calibrator()
        self.detector = ButtonDetector()
        
        # State
        self.is_running = False
        self.log_queue = queue.Queue()
        self.current_monitor = None
        
        self._init_ui()
        self._setup_logging()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Monitor selection
        monitor_frame = ttk.LabelFrame(main_frame, text="Monitor", padding="5")
        monitor_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(monitor_frame, text="Select Monitor:").grid(row=0, column=0, padx=5)
        self.monitor_var = tk.StringVar(value="0")
        monitor_combo = ttk.Combobox(monitor_frame, textvariable=self.monitor_var)
        monitor_combo['values'] = [str(i) for i in range(len(self.detector.monitors))]
        monitor_combo.grid(row=0, column=1, padx=5)
        monitor_combo.bind('<<ComboboxSelected>>', self._on_monitor_selected)
        
        # Calibration section
        cal_frame = ttk.LabelFrame(main_frame, text="Calibration", padding="5")
        cal_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        ttk.Button(cal_frame, text="Start Calibration", 
                  command=self._start_calibration).grid(row=0, column=0, pady=5)
        ttk.Button(cal_frame, text="Test Detection", 
                  command=self._test_detection).grid(row=1, column=0, pady=5)
        
        self.cal_status = ttk.Label(cal_frame, text="Not calibrated")
        self.cal_status.grid(row=2, column=0, pady=5)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Control", padding="5")
        control_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start", 
                                  command=self._toggle_running)
        self.start_btn.grid(row=0, column=0, pady=5)
        
        self.status_label = ttk.Label(control_frame, text="Stopped")
        self.status_label.grid(row=1, column=0, pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
    def _setup_logging(self):
        """Set up logging to UI."""
        self.log_handler = _QueueHandler(self.log_queue)
        logger.addHandler(self.log_handler)
        self.root.after(100, self._poll_log_queue)
        
    def _poll_log_queue(self):
        """Check for new log records."""
        while True:
            try:
                record = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, record + '\n')
                self.log_text.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self._poll_log_queue)
        
    def _on_monitor_selected(self, event):
        """Handle monitor selection."""
        monitor_index = int(self.monitor_var.get())
        self.current_monitor = self.detector.monitors[monitor_index]
        logger.info(f"Selected monitor {monitor_index}")
        
        # Update calibration status
        if self.calibrator.check_calibration_data(self.current_monitor["name"]):
            self.cal_status.config(text="Calibrated")
        else:
            self.cal_status.config(text="Not calibrated")
            
    def _start_calibration(self):
        """Start the calibration process."""
        if not self.current_monitor:
            logger.error("No monitor selected!")
            return
            
        def calibrate():
            logger.info("Starting calibration...")
            for i in range(1, 4):
                logger.info(f"Calibrating button {i}...")
                logger.info("Move mouse over button and wait...")
                self.calibrator.capture_button_state(i, self.current_monitor)
            logger.info("Calibration complete!")
            self.cal_status.config(text="Calibrated")
            
        thread = threading.Thread(target=calibrate)
        thread.daemon = True
        thread.start()
        
    def _test_detection(self):
        """Test button detection."""
        if not self.current_monitor:
            logger.error("No monitor selected!")
            return
            
        def test():
            logger.info("Testing button detection...")
            buttons = self.calibrator.load_calibration_data(self.current_monitor["name"])
            if not buttons:
                logger.error("No calibration data found!")
                return
                
            for button in buttons:
                matches = self.detector.find_matches(
                    button["template"],
                    self.current_monitor,
                    button["x"],
                    button["y"]
                )
                logger.info(f"Found {len(matches)} matches for button {button['index']}")
                for i, match in enumerate(matches, 1):
                    logger.info(f"Match {i}: pos=({match['x']}, {match['y']}), conf={match['confidence']:.3f}")
                    
        thread = threading.Thread(target=test)
        thread.daemon = True
        thread.start()
        
    def _toggle_running(self):
        """Toggle the running state."""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.config(text="Stop")
            self.status_label.config(text="Running")
            logger.info("Started monitoring")
        else:
            self.start_btn.config(text="Start")
            self.status_label.config(text="Stopped")
            logger.info("Stopped monitoring")
            
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()


class _QueueHandler:
    def __init__(self, queue):
        self.queue = queue
        
    def emit(self, record):
        """Add formatted log message to queue."""
        msg = f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} - {record.levelname} - {record.getMessage()}"
        self.queue.put(msg) 