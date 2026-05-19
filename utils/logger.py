import os
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a production-grade logger.
    Supports both console logging and file logging with rotation.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # Avoid duplicate logs if get_logger is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler (Rotating logs up to 5MB, keep 3 backups)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'platform.log'),
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
