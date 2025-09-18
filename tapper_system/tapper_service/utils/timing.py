"""
Simple timing utilities for tapper operations.
"""

import time
from test_framework.utils import get_logger

logger = get_logger("TapperTiming")

# Basic timing constants (in milliseconds)
TIMING_DEFAULTS = {
    'extend_time': 1500,     # Standard extend time
    'retract_time': 2000,    # Standard retract time  
    'long_tap_time': 3000,   # Extended hold time
    'double_tap_delay': 500, # Delay between double taps
    'safety_buffer': 50      # Safety buffer for operations
}


def get_timing_config(preset: str = "standard") -> dict:
    """Get timing configuration."""
    return TIMING_DEFAULTS.copy()


def wait_for_operation(duration_ms: int, buffer_ms: int = 50) -> None:
    """Wait for operation to complete with safety buffer."""
    total_time = (duration_ms + buffer_ms) / 1000.0
    logger.debug(f"Waiting {total_time:.3f}s for operation")
    time.sleep(total_time)


# Legacy timing constants for backward compatibility
LEGACY_TIMING = {
    'SIMPLE_TAP_EXTEND': 1500,
    'SIMPLE_TAP_RETRACT': 2000,
    'LONG_TAP_DURATION': 3000,
    'DOUBLE_TAP_DELAY': 500,
    'HOME_RESET_DURATION': 3000
}


def get_legacy_timing(operation: str) -> int:
    """Get legacy timing value."""
    return LEGACY_TIMING.get(operation, 1000)