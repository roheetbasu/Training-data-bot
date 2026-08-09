"""
    Simple logging configuration for Training Data Bot
"""

import logging
import sys
from functools import wraps
from typing import Any

def get_logger(name: str = "training_data_bot") -> logging.Logger:
    """ Get a logger instance """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # set up basic logging
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s '
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger

def log_api_call(api_name: str):
    """ Simple decorator to log API calls """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.debug(f"API call to {api_name} started")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"API call to {api_name} completed")
                return result
            except Exception as e:
                logger.error(f"API call tp {api_name} failed: {e}")
                raise
        return wrapper
    return decorator
    
class LogContext:
    """ Simple context manager for logging """
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.logger = get_logger()
        
    def __enter__(self):
        self.logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.debug(f"Completed {self.operation}")
        else:
            self.logger.error(f"Failed {self.operation}: {exc_val}")
            

#Place holder functions for compatibility
def audit_log(event: str, **kwargs):
    logger = get_logger()
    logger.info(f"AUDIT: {event}")
    
def perfomance_log(operation: str, duration: float, **kwargs):
    logger = get_logger()
    logger.info(f"PERF: {operation} took {duration:.2f}s")