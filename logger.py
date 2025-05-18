import logging
from typing import Optional

class LoggerSetupError(Exception):
    """Custom exception for logger setup failures."""
    pass

def setup_logger(log_file: str) -> logging.Logger:
    """Sets up and returns a configured logger with UTF-8 encoding."""
    try:
        logger = logging.getLogger('sync_logger')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()  # Clear existing handlers to prevent duplicates
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger
    except (IOError, PermissionError) as e:
        raise LoggerSetupError(f"Failed to set up logger with file {log_file}: {str(e)}")