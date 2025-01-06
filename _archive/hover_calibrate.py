import mss
import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path
from PIL import Image
import tkinter as tk
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HoverCalibrationWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hover Calibration")
        self.root.overrideredirect(True)
        
        # Set window size and position
        window_width = 400
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - window_width - 20
        y = 40
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window semi-transparent and stay on top
        self.root.attributes("-alpha", 0.9, "-topmost", True)
        
        # Create main frame
        self.frame = tk.Frame(self.root, bg='#0066cc')
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create control frame
        self.control_frame = tk.Frame(self.frame, bg='#0066cc')
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add capture button
        self.capture_button = tk.Button(
            self.control_frame,
            text="Capture",
            command=self.start_capture,
            bg='#004999',
            fg='white',
            font=('Arial', 12)
        )
        self.capture_button.pack(side=tk.LEFT, padx=5)
        
        # Add done button
        self.done_button = tk.Button(
            self.control_frame,
            text="Done",
            command=self.finish_calibration,
            bg='#004999',
            fg='white',
            font=('Arial', 12)
        )
        self.done_button.pack(side=tk.LEFT, padx=5)
        
        # Add status label
        self.status_label = tk.Label(
            self.control_frame,
            text="Ready",
            bg='#0066cc',
            fg='white',
            font=('Arial', 12)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Create text widget for instructions
        self.text = tk.Text(
            self.frame,
            height=6,
            bg='#0066cc',
            fg='white',
            font=('Arial', 12),
            wrap=tk.WORD
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Initialize screen capture
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # First actual monitor
        
        # Initialize state
        self.capturing = False
        self.button_count = 0
        self.assets_dir = Path('assets/monitor_0')
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Add drag functionality
        self.control_frame.bind('<Button-1>', self.start_drag)
        self.control_frame.bind('<B1-Motion>', self.on_drag)
        
        # Show initial instructions
        self.show_instructions()
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def show_instructions(self):
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, 
            "1. Move your cursor over an accept button\n"
            "2. Keep the cursor still\n"
            "3. Click 'Capture' to save the button image\n"
            "4. Repeat for different button variations\n"
            "5. Click 'Done' when finished\n"
        )
        
    def add_message(self, message):
        self.text.insert(tk.END, f"\n{message}")
        self.text.see(tk.END)
        self.root.update()
        
    def start_capture(self):
        if self.capturing:
            return
            
        self.capturing = True
        self.capture_button.config(state=tk.DISABLED)
        self.status_label.config(text="Capturing...")
        
        # Start countdown
        self.countdown(3)
        
    def countdown(self, count):
        if count > 0:
            self.add_message(f"Capturing in {count}...")
            self.root.after(1000, lambda: self.countdown(count - 1))
        else:
            self.capture_button_state()
            
    def capture_button_state(self):
        try:
            # Get mouse position
            x, y = pyautogui.position()
            
            # Define capture region (80x40 centered on cursor)
            region = {"top": y-20, "left": x-40, "width": 80, "height": 40}
            
            # Capture multiple samples
            samples = []
            for i in range(3):
                screenshot = self.sct.grab(region)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_np = np.array(img)
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                
                if img_bgr.shape[0] != 40 or img_bgr.shape[1] != 80:
                    img_bgr = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
                
                samples.append(img_bgr)
                time.sleep(0.1)
            
            # Use middle sample
            img_bgr = samples[1]
            
            # Save image
            self.button_count += 1
            filename = self.assets_dir / f'accept_button_{self.button_count}.png'
            cv2.imwrite(str(filename), img_bgr)
            
            # Save coordinates
            coords_file = self.assets_dir / f'click_coords_{self.button_count}.txt'
            with open(coords_file, 'w') as f:
                f.write(f"40,20")  # Center of 80x40 region
            
            self.add_message(f"Captured button {self.button_count}!")
            self.status_label.config(text="Ready")
            
        except Exception as e:
            self.add_message(f"Error: {str(e)}")
            self.status_label.config(text="Error")
            
        finally:
            self.capturing = False
            self.capture_button.config(state=tk.NORMAL)
            
    def finish_calibration(self):
        if self.button_count == 0:
            self.add_message("Please capture at least one button first!")
            return
            
        self.add_message("\nCalibration complete!")
        self.add_message(f"Captured {self.button_count} button variations")
        self.root.after(2000, self.root.destroy)
        
    def run(self):
        self.root.mainloop()

def main():
    # Clean up old calibration files
    assets_dir = Path('assets/monitor_0')
    if assets_dir.exists():
        for file in assets_dir.glob("*"):
            file.unlink()
    
    window = HoverCalibrationWindow()
    window.run()

if __name__ == "__main__":
    main() 