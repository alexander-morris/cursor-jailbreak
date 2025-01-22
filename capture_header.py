import os
import time
from PIL import ImageGrab
import pyautogui

print("This script will help you capture the Cursor window header.")
print("1. Make sure your Cursor window is visible")
print("2. Move your mouse to the top-left corner of the Cursor window header")
input("3. Press Enter when ready...")
time.sleep(0.5)

# Get the starting position
start_x, start_y = pyautogui.position()

print("\nNow move your mouse to the bottom-right corner of the header")
input("Press Enter when ready...")
time.sleep(0.5)

# Get the ending position
end_x, end_y = pyautogui.position()

# Capture the region
region = (start_x, start_y, end_x, end_y)
screenshot = ImageGrab.grab(bbox=region)

# Ensure images directory exists
os.makedirs('images', exist_ok=True)

# Save the image
screenshot.save('images/cursor-screen-head.png')
print("\nHeader image saved as 'images/cursor-screen-head.png'")
print("You can now run main.py --debug") 