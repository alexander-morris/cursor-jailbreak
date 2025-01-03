import logging
import os
from pathlib import Path

def setup_logging(name, debug=False):
    """Set up logging configuration"""
    # Create logs directory
    log_dir = Path('temp/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / f'{name}.log')
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_error_with_context(logger, error, message):
    """Log error with context information"""
    logger.error(f"{message}: {str(error)}")
    if hasattr(error, "__traceback__"):
        import traceback
        logger.debug("".join(traceback.format_tb(error.__traceback__)))

def save_debug_image(image, name, debug_dir='temp/debug'):
    """Save an image for debugging purposes"""
    if not isinstance(debug_dir, Path):
        debug_dir = Path(debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Save image with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = debug_dir / f'{name}_{timestamp}.png'
    
    try:
        import cv2
        import numpy as np
        
        # Convert PIL Image to cv2 format if needed
        if not isinstance(image, np.ndarray):
            image = np.array(image)
        
        # Save image
        cv2.imwrite(str(path), image)
        return str(path)
    except Exception as e:
        logger = logging.getLogger('debug')
        log_error_with_context(logger, e, f"Failed to save debug image {name}")
        return None 