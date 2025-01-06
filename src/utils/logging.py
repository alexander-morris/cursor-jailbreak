"""
Logging configuration for the Cursor Auto Accept application.
"""

import logging
import queue
from datetime import datetime

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.queue = log_queue
        
    def emit(self, record):
        """Add formatted log message to queue."""
        try:
            msg = f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} - {record.levelname} - {record.getMessage()}"
            self.queue.put(msg)
        except Exception:
            self.handleError(record)

def get_logger(name):
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger 