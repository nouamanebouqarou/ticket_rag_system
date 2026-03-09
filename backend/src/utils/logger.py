"""Logging configuration for the Ticket RAG System."""

import logging
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> logging.Logger:
    """Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        json_format: If True, use JSON formatting for logs
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    if json_format:
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger


# Create default logger
default_logger = setup_logger('ticket_rag', level='INFO')
