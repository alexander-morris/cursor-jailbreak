import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(component_name, debug_mode=False):
    """Configure logging for the specified component following best practices."""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Set up the logger
    logger = logging.getLogger(component_name)
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # File handler with rotation
    log_file = os.path.join(log_dir, f'{component_name}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_error_with_context(logger, error, context=None):
    """Log an error with full context information."""
    error_msg = f"Error: {str(error)}\nType: {type(error).__name__}"
    if context:
        error_msg += f"\nContext: {context}"
    logger.error(error_msg, exc_info=True)

def log_match_result(logger, match_info, confidence, region=None):
    """Log template matching results with coordinates and confidence."""
    msg = f"Match found - Confidence: {confidence:.4f}"
    if region:
        msg += f" | Region: {region}"
    logger.debug(msg)

def save_debug_image(image, prefix, debug_dir='debug_output'):
    """Save a debug image with timestamp."""
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{prefix}_{timestamp}.png"
    path = os.path.join(debug_dir, filename)
    image.save(path)
    return path 