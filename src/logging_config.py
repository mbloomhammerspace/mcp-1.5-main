"""
Logging configuration for Hammerspace client.
"""

import logging
import functools
from typing import Callable, Any


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_api_call(endpoint: str, method: str):
    """Decorator to log API calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = get_logger("hammerspace_client")
            logger.info(f"API call started: {method} {endpoint}")
            try:
                result = await func(*args, **kwargs)
                logger.info(f"API call completed: {method} {endpoint}")
                return result
            except Exception as e:
                logger.error(f"API call failed: {method} {endpoint} - {e}")
                raise
        return wrapper
    return decorator 