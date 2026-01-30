"""
Structured Logging Configuration for Honey-Pot API
Provides JSON-formatted logs for production analysis
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from functools import wraps
import traceback
from contextlib import contextmanager

from config import LOGGING_CONFIG


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if all(record.exc_info) else None,
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'message', 'taskName'
            ):
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        base = f"{timestamp} | {color}{record.levelname:8}{reset} | {record.name} | {record.getMessage()}"
        
        # Add extra fields
        extras = []
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'message', 'taskName'
            ):
                extras.append(f"{key}={value}")
        
        if extras:
            base += f" | {' '.join(extras)}"
        
        if record.exc_info:
            base += f"\n{''.join(traceback.format_exception(*record.exc_info))}"
        
        return base


def setup_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
) -> None:
    """
    Configure application logging
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 'json' or 'text'
    """
    level = level or LOGGING_CONFIG.get("level", "INFO")
    format_type = format_type or LOGGING_CONFIG.get("format", "json")
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Set formatter based on type
    if format_type.lower() == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(TextFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger with proper configuration"""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding contextual information to logs"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self._old_factory = None
    
    def __enter__(self):
        self._old_factory = logging.getLogRecordFactory()
        context = self.context
        
        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self._old_factory)


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Log a message with additional context fields"""
    extra = {k: v for k, v in context.items()}
    logger.log(level, message, extra=extra)


def log_function_call(logger: logging.Logger):
    """Decorator to log function entry/exit with timing"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_name = func.__name__
            
            log_with_context(
                logger, logging.DEBUG,
                f"Entering {func_name}",
                function=func_name
            )
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                log_with_context(
                    logger, logging.DEBUG,
                    f"Exiting {func_name}",
                    function=func_name,
                    duration_ms=round(duration_ms, 2)
                )
                
                return result
                
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                log_with_context(
                    logger, logging.ERROR,
                    f"Error in {func_name}: {str(e)}",
                    function=func_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_name = func.__name__
            
            log_with_context(
                logger, logging.DEBUG,
                f"Entering {func_name}",
                function=func_name
            )
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                log_with_context(
                    logger, logging.DEBUG,
                    f"Exiting {func_name}",
                    function=func_name,
                    duration_ms=round(duration_ms, 2)
                )
                
                return result
                
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                log_with_context(
                    logger, logging.ERROR,
                    f"Error in {func_name}: {str(e)}",
                    function=func_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Request/Response logging helper
class APILogger:
    """Helper class for logging API requests and responses"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        path: str,
        session_id: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
    ):
        """Log an incoming API request"""
        log_data = {
            "event": "api_request",
            "method": method,
            "path": path,
        }
        
        if session_id:
            log_data["session_id"] = session_id
        
        if body and LOGGING_CONFIG.get("include_request_body", True):
            max_len = LOGGING_CONFIG.get("max_body_length", 1000)
            body_str = json.dumps(body, default=str)
            if len(body_str) > max_len:
                body_str = body_str[:max_len] + "...(truncated)"
            log_data["body"] = body_str
        
        log_with_context(self.logger, logging.INFO, "API Request", **log_data)
    
    def log_response(
        self,
        status_code: int,
        duration_ms: float,
        session_id: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
    ):
        """Log an API response"""
        log_data = {
            "event": "api_response",
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }
        
        if session_id:
            log_data["session_id"] = session_id
        
        if body and LOGGING_CONFIG.get("include_response_body", True):
            max_len = LOGGING_CONFIG.get("max_body_length", 1000)
            body_str = json.dumps(body, default=str)
            if len(body_str) > max_len:
                body_str = body_str[:max_len] + "...(truncated)"
            log_data["body"] = body_str
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        log_with_context(self.logger, level, "API Response", **log_data)
    
    def log_scam_detection(
        self,
        session_id: str,
        is_scam: bool,
        confidence: float,
        scam_type: str,
        keywords: list,
    ):
        """Log scam detection results"""
        log_with_context(
            self.logger, logging.INFO,
            "Scam Detection",
            event="scam_detection",
            session_id=session_id,
            is_scam=is_scam,
            confidence=round(confidence, 4),
            scam_type=scam_type,
            keywords_count=len(keywords),
        )
    
    def log_intelligence_extraction(
        self,
        session_id: str,
        phone_count: int,
        upi_count: int,
        link_count: int,
        account_count: int,
    ):
        """Log intelligence extraction results"""
        log_with_context(
            self.logger, logging.INFO,
            "Intelligence Extraction",
            event="intelligence_extraction",
            session_id=session_id,
            phone_numbers=phone_count,
            upi_ids=upi_count,
            phishing_links=link_count,
            bank_accounts=account_count,
        )
    
    def log_callback(
        self,
        session_id: str,
        success: bool,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
        attempt: int = 1,
    ):
        """Log GUVI callback result"""
        log_data = {
            "event": "guvi_callback",
            "session_id": session_id,
            "success": success,
            "attempt": attempt,
        }
        
        if status_code:
            log_data["status_code"] = status_code
        if error:
            log_data["error"] = error
        
        level = logging.INFO if success else logging.WARNING
        log_with_context(self.logger, level, "GUVI Callback", **log_data)


# Initialize default logger
setup_logging()
api_logger = APILogger(get_logger("honeypot.api"))
