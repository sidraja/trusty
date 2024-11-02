import logging
import sys
from typing import Optional

def setup_logging(level: Optional[str] = "INFO") -> logging.Logger:
    """Setup logging configuration for the test suite."""
    logger = logging.getLogger('api_tests')
    logger.setLevel(getattr(logging, level))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))
    
    # Create formatter
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger 