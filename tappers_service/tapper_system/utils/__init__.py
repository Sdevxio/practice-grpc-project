"""
Tapper service utilities.

This package provides utility modules for tapper service operations:

- exceptions: Custom exception classes for error handling
- timing: Timing utilities, configurations, and profiling
- endpoints: Endpoint definitions, URL builders, and validation

Usage:
    from tappers_service.utils.timing import get_timing_config, wait_for_operation
    from tappers_service.utils.endpoints import EndpointBuilder, TAPPER_ENDPOINTS
    from tappers_service.utils.exceptions import TapperError, TapperConnectionError
"""

# Import main utility classes and functions for easy access
from .exceptions import (
    TapperError,
    TapperConnectionError,
    TapperTimeoutError,
    TapperProtocolError,
    TapperConfigurationError
)

from .timing import (
    get_timing_config,
    wait_for_operation,
)

from .endpoints import (
    EndpointBuilder,
    TAPPER_ENDPOINTS,
)

__all__ = [
    # Exceptions
    'TapperError',
    'TapperConnectionError', 
    'TapperTimeoutError',
    'TapperProtocolError',
    'TapperConfigurationError',
    
    # Timing utilities
    'get_timing_config',
    'wait_for_operation',
    
    # Endpoint utilities
    'EndpointBuilder',
    'TAPPER_ENDPOINTS',
]