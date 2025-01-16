import pyautogui
import time
from queue import Queue
from threading import Lock, Thread
import json
from pathlib import Path

class ActionController:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ActionController, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.action_queue = Queue()
        self.last_action_time = 0
        self.cooldowns = {
            'click': 5,  # 5 seconds for click actions
            'click_and_type': 300  # 5 minutes for stuck monitor actions
        }
        self.last_action_type = None
        self.last_action_params = None
        self.action_log_file = 'action_log.json'
        self.load_action_log()
        self.worker_thread = Thread(target=self._process_actions, daemon=True)
        self.worker_thread.start()
        self._initialized = True
    
    def load_action_log(self):
        """Load or create the action log"""
        try:
            with open(self.action_log_file, 'r') as f:
                self.action_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.action_log = {
                'last_action_time': 0,
                'last_action_type': None,
                'last_action_params': None
            }
            self.save_action_log()
    
    def save_action_log(self):
        """Save the current action log"""
        with open(self.action_log_file, 'w') as f:
            json.dump(self.action_log, f)
    
    def queue_action(self, action_type, **kwargs):
        """Add an action to the queue"""
        current_time = time.time()
        cooldown = self.cooldowns.get(action_type, 300)  # Default 5 min cooldown for unknown actions
        
        # Check global action log for same type of action
        if (current_time - self.action_log['last_action_time'] < cooldown and
            action_type == self.action_log['last_action_type']):
            print(f"\nSkipping {action_type} action during {cooldown}s cooldown")
            return
        
        action = {
            'type': action_type,
            'params': kwargs,
            'timestamp': current_time
        }
        self.action_queue.put(action)
        print(f"\nQueued {action_type} action")
    
    def _process_actions(self):
        """Worker thread to process queued actions"""
        while True:
            try:
                # Get next action from queue
                action = self.action_queue.get()
                current_time = time.time()
                cooldown = self.cooldowns.get(action['type'], 300)
                
                # Check cooldown against global log for same type of action
                if (current_time - self.action_log['last_action_time'] < cooldown and
                    action['type'] == self.action_log['last_action_type']):
                    time.sleep(1)
                    # Put action back in queue if it's still within its timeout
                    # and it's not a duplicate of the last action
                    if current_time - action['timestamp'] < 600:  # 10 minute timeout
                        self.action_queue.put(action)
                    continue
                
                # Process the action
                if action['type'] == 'click_and_type':
                    self._perform_click_and_type(**action['params'])
                elif action['type'] == 'click':
                    self._perform_click(**action['params'])
                
                # Update global action log
                self.action_log['last_action_time'] = time.time()
                self.action_log['last_action_type'] = action['type']
                self.action_log['last_action_params'] = action['params']
                self.save_action_log()
                
                # Small delay between actions
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing action: {str(e)}")
                time.sleep(1)
    
    def _perform_click_and_type(self, x, y, message, use_command_enter=True):
        """Perform click and type action"""
        print("\nExecuting click_and_type action...")
        
        # Store original position
        original_x, original_y = pyautogui.position()
        
        try:
            # Move and click
            print(f"Moving to ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.05)
            pyautogui.click()
            time.sleep(0.5)
            
            # Click again to ensure focus and wait longer
            print("Double-clicking to ensure focus")
            pyautogui.click()
            pyautogui.click()
            time.sleep(1.0)  # Longer wait after clicks
            
            # Type message with longer interval
            print(f"Typing message: {message}")
            pyautogui.write(message, interval=0.1)  # Slower typing
            time.sleep(1.0)  # Longer wait after typing
            
            # Send Command + Enter if requested
            if use_command_enter:
                print("Sending Command + Enter")
                pyautogui.keyDown('command')
                time.sleep(0.2)
                pyautogui.press('return')
                time.sleep(0.2)
                pyautogui.keyUp('command')
                time.sleep(0.5)
            
            print("Action completed successfully")
            
        except Exception as e:
            print(f"Error during click_and_type: {str(e)}")
            raise
        finally:
            # Always restore cursor position
            print(f"Restoring cursor to ({original_x}, {original_y})")
            pyautogui.moveTo(original_x, original_y, duration=0.05)
    
    def _perform_click(self, x, y):
        """Perform simple click action"""
        original_x, original_y = pyautogui.position()
        try:
            pyautogui.moveTo(x, y, duration=0.05)
            pyautogui.click()
        finally:
            pyautogui.moveTo(original_x, original_y, duration=0.05)

# Global instance
controller = ActionController() 