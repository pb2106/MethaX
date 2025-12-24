"""
Structured logging setup with IST timezone.
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from app.config import settings


class ISTFormatter(logging.Formatter):
    """Custom formatter that uses IST timezone."""
    
    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        """Format time in IST timezone."""
        dt = datetime.fromtimestamp(record.created, tz=settings.timezone)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with extra fields."""
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            extra = record.extra_data
            record.msg = f"{record.msg} | {extra}"
        
        return super().format(record)


def setup_logger(name: str = "methax") -> logging.Logger:
    """
    Setup structured logger with IST timezone.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatter
    if settings.is_production:
        # JSON format for production
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","name":"%(name)s",'
            '"message":"%(message)s","module":"%(module)s","function":"%(funcName)s"}'
        )
    else:
        # Human-readable format for development
        formatter = ISTFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %Z'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Global logger instance
logger = setup_logger()


def log_trade_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Log trading-related events with structured data.
    
    Args:
        event_type: Type of event (entry, exit, rejection, etc.)
        data: Event data dictionary
    """
    logger.info(f"TRADE_EVENT: {event_type}", extra={'extra_data': data})


def log_filter_result(filter_name: str, passed: bool, reason: str = "") -> None:
    """
    Log filter evaluation result.
    
    Args:
        filter_name: Name of the filter
        passed: Whether the filter passed
        reason: Reason for failure (if failed)
    """
    status = "PASS" if passed else "FAIL"
    msg = f"FILTER: {filter_name} | {status}"
    if reason:
        msg += f" | {reason}"
    logger.info(msg)
