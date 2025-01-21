import mss
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def print_monitor_info():
    with mss.mss() as sct:
        # Print info for "all monitors" monitor
        logger.info("Monitor 'all':")
        logger.info(f"  {sct.monitors[0]}")
        
        # Print info for each individual monitor
        for i, m in enumerate(sct.monitors[1:], 1):
            logger.info(f"\nMonitor {i-1}:")  # Use 0-based indexing in output
            logger.info(f"  Resolution: {m['width']}x{m['height']}")
            logger.info(f"  Position: ({m['left']}, {m['top']})")
            logger.info(f"  Raw data: {m}")

if __name__ == "__main__":
    print_monitor_info() 