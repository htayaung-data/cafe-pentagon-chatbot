"""
Logging configuration for Cafe Pentagon Chatbot
"""

import logging
import sys
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory
from src.config.settings import get_settings


def setup_logger(
    name: str = "cafe_pentagon",
    level: Optional[str] = None,
    log_format: Optional[str] = None
) -> structlog.BoundLogger:
    """
    Setup structured logging for the application
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format
        
    Returns:
        Configured structured logger
    """
    settings = get_settings()
    
    # Use provided level or default from settings
    log_level = level or settings.log_level
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format=log_format or "%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    return structlog.get_logger(name)


def get_logger(name: str = "cafe_pentagon") -> structlog.BoundLogger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        logger = get_logger("performance")
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                "function_executed",
                function_name=func.__name__,
                execution_time=execution_time,
                status="success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "function_failed",
                function_name=func.__name__,
                execution_time=execution_time,
                error=str(e),
                status="error"
            )
            raise
    
    return wrapper


def log_api_call(func):
    """Decorator to log API calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger("api")
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                "api_call_success",
                function_name=func.__name__,
                execution_time=execution_time,
                status="success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "api_call_failed",
                function_name=func.__name__,
                execution_time=execution_time,
                error=str(e),
                status="error"
            )
            raise
    
    return wrapper 