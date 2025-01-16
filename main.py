import os
import json
import time
import signal
from threading import Thread

def check_calibration():
    """Check if calibration files exist"""
    has_click_targets = os.path.exists('click_targets.json')
    has_stuck_region = os.path.exists('stuck_region.json')
    return has_click_targets, has_stuck_region

def load_click_targets():
    """Load existing click targets"""
    try:
        with open('click_targets.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def run_calibration():
    """Run the setup script for calibration"""
    import setup_monitors
    setup_monitors.setup_monitors()

def start_stuck_monitor():
    """Start the stuck monitor in a separate thread"""
    import stuck_monitor
    thread = Thread(target=stuck_monitor.monitor_region, daemon=True)
    thread.start()
    return thread

def start_click_monitor():
    """Start the click monitor in a separate thread"""
    import basic_clicker
    thread = Thread(target=basic_clicker.run_clicker, daemon=True)
    thread.start()
    return thread

def add_new_targets():
    """Add new click targets"""
    import setup_monitors
    setup_monitors.add_click_targets()

def kill_existing_sessions():
    """Kill any existing Python processes running the monitors"""
    import psutil
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any(x in ['stuck_monitor.py', 'basic_clicker.py'] for x in cmdline):
                proc.kill()
                killed = True
                print(f"Killed process: {' '.join(cmdline)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if not killed:
        print("No existing monitor sessions found")
    else:
        print("Successfully killed existing sessions")
    time.sleep(1)  # Give processes time to clean up

def main():
    """Main entry point"""
    has_click_targets, has_stuck_region = check_calibration()
    
    if not has_click_targets and not has_stuck_region:
        print("\nNo calibration found. Running initial setup...")
        run_calibration()
    else:
        print("\nExisting calibration found.")
        if has_click_targets:
            targets = load_click_targets()
            print(f"Found {len(targets)} click targets:")
            for i, target in enumerate(targets, 1):
                print(f"Target {i} at ({target['x']}, {target['y']})")
        
        action = input("\nWhat would you like to do?\n1. Add new click targets\n2. Run calibration again\n3. Start monitors\n4. Kill existing sessions\nChoice (1-4): ")
        
        if action == '4':
            kill_existing_sessions()
            return
        elif action == '1':
            add_new_targets()
        elif action == '2':
            run_calibration()
    
        if action != '4':
            print("\nStarting monitors...")
            if has_stuck_region or action == '2':
                stuck_thread = start_stuck_monitor()
            if has_click_targets or action in ('1', '2'):
                click_thread = start_click_monitor()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitors...")

if __name__ == "__main__":
    main() 