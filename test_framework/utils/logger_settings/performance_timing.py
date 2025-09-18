"""
Performance timing decorators and context managers for test framework logging.

Provides automatic timing capabilities for test phases, session operations,
and other critical framework components.
"""

import time
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager

from test_framework.utils import get_logger


class PerformanceTimer:
    """Centralized performance timing for test framework components."""
    
    def __init__(self, logger_name: str = "framework.performance"):
        self.logger = get_logger(logger_name)
        
    def time_operation(self, operation_name: str, threshold_seconds: float = None):
        """
        Decorator to time any operation and log performance metrics.
        
        :param operation_name: Name of the operation being timed
        :param threshold_seconds: Optional threshold - log warning if exceeded
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    
                    # Log performance metrics
                    if threshold_seconds and elapsed > threshold_seconds:
                        self.logger.warning(
                            f"{operation_name} took {elapsed:.3f}s (exceeds {threshold_seconds}s threshold)"
                        )
                    else:
                        self.logger.info(f"{operation_name} completed in {elapsed:.3f}s")
                    
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    self.logger.error(f"{operation_name} failed after {elapsed:.3f}s: {e}")
                    raise
            return wrapper
        return decorator
    
    @contextmanager
    def time_context(self, operation_name: str, threshold_seconds: float = None):
        """
        Context manager for timing code blocks.
        
        Usage:
            with timer.time_context("Database query", threshold_seconds=2.0):
                result = database.query(...)
        """
        start_time = time.time()
        try:
            yield
            elapsed = time.time() - start_time
            
            if threshold_seconds and elapsed > threshold_seconds:
                self.logger.warning(
                    f"{operation_name} took {elapsed:.3f}s (exceeds {threshold_seconds}s threshold)"
                )
            else:
                self.logger.info(f"{operation_name} completed in {elapsed:.3f}s")
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"{operation_name} failed after {elapsed:.3f}s: {e}")
            raise


# Global timer instance for framework use
framework_timer = PerformanceTimer()

# Convenience decorators for common operations
def time_session_operation(operation_name: str, threshold_seconds: float = 30.0):
    """Decorator for timing session operations with 30s default threshold."""
    return framework_timer.time_operation(operation_name, threshold_seconds)

def time_tapper_operation(operation_name: str, threshold_seconds: float = 5.0):
    """Decorator for timing tapper operations with 5s default threshold."""
    return framework_timer.time_operation(operation_name, threshold_seconds)

def time_grpc_operation(operation_name: str, threshold_seconds: float = 10.0):
    """Decorator for timing gRPC operations with 10s default threshold."""
    return framework_timer.time_operation(operation_name, threshold_seconds)