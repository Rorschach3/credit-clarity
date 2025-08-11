"""
Enhanced logging configuration with structured logging
JSON logging, error tracking, and performance monitoring
"""
import logging
import logging.config
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from core.config import get_settings

settings = get_settings()

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    Includes additional context and error tracking.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        
        # Add performance data if available
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        
        # Add error information
        if record.exc_info:
            log_entry['error'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """
    Add context information to log records.
    Enriches logs with request and user context.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        
        # Add application context
        record.app_version = "3.0.0"
        record.environment = settings.environment
        
        # Try to get request context from contextvars or thread local
        try:
            import contextvars
            request_id = contextvars.ContextVar('request_id', default=None).get()
            user_id = contextvars.ContextVar('user_id', default=None).get()
            
            if request_id:
                record.request_id = request_id
            if user_id:
                record.user_id = user_id
                
        except Exception:
            pass
        
        return True

class ErrorTracker:
    """
    Track and aggregate error information.
    Provides error analytics and alerting.
    """
    
    def __init__(self):
        self.error_counts = {}
        self.error_details = []
        self.max_errors = 1000  # Keep last 1000 errors
    
    def track_error(
        self, 
        error_type: str, 
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track an error occurrence."""
        
        # Count errors by type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Store error details
        error_detail = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context or {}
        }
        
        self.error_details.append(error_detail)
        
        # Keep only recent errors
        if len(self.error_details) > self.max_errors:
            self.error_details = self.error_details[-self.max_errors:]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        recent_errors = [
            error for error in self.error_details 
            if error["timestamp"] > cutoff_str
        ]
        
        # Count by type
        error_counts = {}
        for error in recent_errors:
            error_type = error["type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": error_counts,
            "error_rate": len(recent_errors) / max(hours, 1),
            "most_common": max(error_counts.items(), key=lambda x: x[1]) if error_counts else None
        }

# Global error tracker
error_tracker = ErrorTracker()

class ErrorTrackingHandler(logging.Handler):
    """
    Custom handler that tracks errors for analytics.
    Integrates with error tracking system.
    """
    
    def emit(self, record: logging.LogRecord):
        """Track errors and warnings."""
        
        if record.levelno >= logging.ERROR:
            error_type = getattr(record, 'error_type', record.levelname)
            context = {
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "request_id": getattr(record, 'request_id', None),
                "user_id": getattr(record, 'user_id', None)
            }
            
            error_tracker.track_error(error_type, record.getMessage(), context)

def setup_logging():
    """
    Configure comprehensive logging system.
    Sets up structured logging with multiple handlers.
    """
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "filters": {
            "context_filter": {
                "()": ContextFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "structured" if settings.is_production() else "simple",
                "filters": ["context_filter"],
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filters": ["context_filter"],
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "structured",
                "filters": ["context_filter"],
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10
            },
            "error_tracker": {
                "()": ErrorTrackingHandler,
                "level": "WARNING"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file", "error_tracker"]
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Suppress verbose logs
            "pdfminer": {
                "level": "WARNING"
            },
            "google.cloud": {
                "level": "WARNING"
            },
            "urllib3": {
                "level": "WARNING"
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set up structured logging for production
    if settings.is_production():
        # In production, you might want to send logs to external services
        # like CloudWatch, DataDog, or Elasticsearch
        pass

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger with context support.
    """
    logger = logging.getLogger(name)
    
    # Add convenience methods
    def log_with_context(level: int, message: str, **context):
        """Log message with additional context."""
        extra = {k: v for k, v in context.items() if v is not None}
        logger.log(level, message, extra=extra)
    
    def log_error_with_context(message: str, error: Exception, **context):
        """Log error with full context and traceback."""
        extra = {
            **context,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        logger.error(message, exc_info=True, extra=extra)
    
    def log_performance(message: str, duration_ms: float, **context):
        """Log performance information."""
        extra = {
            **context,
            "duration_ms": duration_ms,
            "performance": True
        }
        logger.info(message, extra=extra)
    
    # Monkey patch the logger with convenience methods
    logger.log_with_context = log_with_context
    logger.log_error_with_context = log_error_with_context
    logger.log_performance = log_performance
    
    return logger

# Context management utilities
class LogContext:
    """
    Context manager for adding request context to logs.
    """
    
    def __init__(self, request_id: str, user_id: Optional[str] = None, endpoint: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.endpoint = endpoint
        self.context_vars = {}
    
    def __enter__(self):
        """Set log context."""
        import contextvars
        
        self.context_vars['request_id'] = contextvars.ContextVar('request_id')
        self.context_vars['user_id'] = contextvars.ContextVar('user_id')
        self.context_vars['endpoint'] = contextvars.ContextVar('endpoint')
        
        self.context_vars['request_id'].set(self.request_id)
        if self.user_id:
            self.context_vars['user_id'].set(self.user_id)
        if self.endpoint:
            self.context_vars['endpoint'].set(self.endpoint)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear log context."""
        # Context vars are automatically cleared when context exits
        pass

# Initialize logging on import
setup_logging()