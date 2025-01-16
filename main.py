import os
import json
import time
import signal
import logging
from threading import Thread, Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global stop event for threads
stop_event = Event()

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
    thread = Thread(target=stuck_monitor.monitor_region, daemon=False)
    thread.start()
    return thread

def start_click_monitor():
    """Start the click monitor in a separate thread"""
    import basic_clicker
    thread = Thread(target=basic_clicker.run_clicker, daemon=False)
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
                logger.info(f"Killed process: {' '.join(cmdline)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if not killed:
        logger.info("No existing monitor sessions found")
    else:
        logger.info("Successfully killed existing sessions")
    time.sleep(1)  # Give processes time to clean up

def main():
    """Main entry point"""
    # First kill any existing sessions
    kill_existing_sessions()
    
    has_click_targets, has_stuck_region = check_calibration()
    active_threads = []
    
    try:
        if not has_click_targets and not has_stuck_region:
            logger.info("\nNo calibration found. Running initial setup...")
            run_calibration()
        else:
            logger.info("\nExisting calibration found.")
            if has_click_targets:
                targets = load_click_targets()
                logger.info(f"Found {len(targets)} click targets:")
                for i, target in enumerate(targets, 1):
                    logger.info(f"Target {i} at ({target['x']}, {target['y']})")
            
            action = input("\nWhat would you like to do?\n1. Add new click targets\n2. Run calibration again\n3. Start monitors\n4. Kill existing sessions\nChoice (1-4): ")
            
            if action == '4':
                kill_existing_sessions()
                return
            elif action == '1':
                add_new_targets()
            elif action == '2':
                run_calibration()
        
            if action != '4':
                logger.info("\nStarting monitors...")
                if has_stuck_region or action == '2':
                    stuck_thread = start_stuck_monitor()
                    active_threads.append(stuck_thread)
                if has_click_targets or action in ('1', '2'):
                    click_thread = start_click_monitor()
                    active_threads.append(click_thread)
                
                try:
                    while True:
                        # Check if threads are still alive
                        for thread in active_threads:
                            if not thread.is_alive():
                                logger.error("A monitor thread has died unexpectedly")
                                return
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("\nStopping monitors...")
                    stop_event.set()  # Signal threads to stop
                    
                    # Wait for threads to finish
                    for thread in active_threads:
                        thread.join(timeout=5)
                        if thread.is_alive():
                            logger.warning("Thread did not stop gracefully")
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Ensure we always try to clean up
        stop_event.set()
        for thread in active_threads:
            if thread.is_alive():
                thread.join(timeout=1)

if __name__ == "__main__":
    main() 