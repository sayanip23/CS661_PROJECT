"""
utils/logger.py

Centralized logging configuration for the dashboard.
Ensures consistent log formatting and handles writing to a file if needed.
"""

import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Creates or retrieves a configured logger with standard formatting.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Standard format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
        
    return logger
