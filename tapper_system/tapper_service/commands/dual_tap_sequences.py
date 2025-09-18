#!/usr/bin/env python3
"""
Dual card sequences using timed operations approach.
Modern replacement for legacy sequences that use fixed timing instead of firmware delays.
"""

import time
from typing import Optional

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from test_framework.utils import get_logger

# Module logger
logger = get_logger("DualSequences")


def _wait_for_operation(duration_ms: int, buffer_ms: int = 50) -> None:
    """
    Wait for timed operation to complete.
    
    :param duration_ms: Expected operation duration in milliseconds
    :param buffer_ms: Additional buffer time in milliseconds
    """
    wait_time = (duration_ms + buffer_ms) / 1000.0
    time.sleep(wait_time)


def _wait_for_idle(protocol: BaseProtocol, max_wait: int = 5) -> bool:
    """
    Wait for device to return to idle state (fallback method).
    
    :param protocol: Protocol instance to check status through
    :param max_wait: Maximum wait time in seconds
    :return: True if device became idle, False if timeout
    """
    for _ in range(max_wait * 10):  # Check every 100ms
        status = protocol.get_status()
        if status and ("idle" in status.lower() or "middle" in status.lower()):
            return True
        time.sleep(0.1)
    return False


def reset_to_middle_timed(protocol: BaseProtocol, from_position: str = "unknown") -> None:
    """
    Reset tapper to middle position using timed operations.
    
    :param protocol: Protocol instance to execute commands through
    :param from_position: Current position hint ("card1", "card2", "unknown")
    """
    logger.info(f"Resetting to middle from {from_position} position")
    
    if from_position == "card1":
        # From Card 1 (extended), retract to middle
        logger.debug("From Card 1: retracting 995ms to middle")
        protocol.retract_for_time(995)  # Card1 to home timing
        _wait_for_operation(995)
        logger.info("Reset to middle from Card 1 complete")
        
    elif from_position == "card2":
        # From Card 2 (retracted), extend to middle  
        logger.debug("From Card 2: extending 1395ms to middle")
        protocol.extend_for_time(1395)  # Card2 to home timing
        _wait_for_operation(1395)
        logger.info("Reset to middle from Card 2 complete")
        
    else:
        # Unknown position - full retract then extend to middle
        logger.warning("Unknown position - performing full reset sequence")
        logger.debug("Step 1: Full retract 2611ms")
        protocol.retract_for_time(2611)  # Full retract
        _wait_for_operation(2611)
        
        logger.debug("Step 2: Extend 1284ms to middle from retracted")
        protocol.extend_for_time(1284)  # Home from retracted
        _wait_for_operation(1284)
        logger.info("Reset to middle from unknown position complete")


def tap_card1_timed(protocol: BaseProtocol, extend_time: int = 1000, return_time: int = 995) -> None:
    """
    Tap Card 1 using timed operations (extend direction).
    
    :param protocol: Protocol instance to execute commands through
    :param extend_time: Time to extend to Card 1 (ms)
    :param return_time: Time to return to middle (ms)
    """
    logger.info(f"Tapping Card 1 - extend {extend_time}ms, return {return_time}ms")
    
    # Extend to Card 1
    logger.debug(f"Extending to Card 1 for {extend_time}ms")
    protocol.extend_for_time(extend_time)
    _wait_for_operation(extend_time)
    
    # Return to middle (with drift compensation)
    logger.debug(f"Returning to middle for {return_time}ms")
    protocol.retract_for_time(return_time)
    _wait_for_operation(return_time)
    
    logger.info("Card 1 tap complete")


def tap_card2_timed(protocol: BaseProtocol, retract_time: int = 1400, return_time: int = 1395) -> None:
    """
    Tap Card 2 using timed operations (retract direction).
    
    :param protocol: Protocol instance to execute commands through
    :param retract_time: Time to retract to Card 2 (ms)
    :param return_time: Time to return to middle (ms)
    """
    logger.info(f"Tapping Card 2 - retract {retract_time}ms, return {return_time}ms")
    
    # Retract to Card 2
    logger.debug(f"Retracting to Card 2 for {retract_time}ms")
    protocol.retract_for_time(retract_time)
    _wait_for_operation(retract_time)
    
    # Return to middle (with drift compensation)  
    logger.debug(f"Returning to middle for {return_time}ms")
    protocol.extend_for_time(return_time)
    _wait_for_operation(return_time)
    
    logger.info("Card 2 tap complete")


def adaptive_tap_card2(protocol: BaseProtocol, extend_time: Optional[int] = None) -> str:
    """
    Adaptive Card 2 tap that can accept custom timing.
    
    :param protocol: Protocol instance to execute commands through
    :param extend_time: Custom extend time (ms), uses default if None
    :return: Final position status for drift analysis
    """
    retract_time = 1400  # Fixed
    extend_time = extend_time or 1395  # Use provided or default
    
    logger.info(f"Adaptive Card 2 tap - retract {retract_time}ms, extend {extend_time}ms")
    
    # Retract to Card 2
    logger.debug(f"Adaptive retract to Card 2 for {retract_time}ms")
    protocol.retract_for_time(retract_time)
    _wait_for_operation(retract_time)
    
    # Return to middle with custom timing
    logger.debug(f"Adaptive return to middle for {extend_time}ms")
    protocol.extend_for_time(extend_time)
    _wait_for_operation(extend_time)
    
    # Get final status for drift analysis
    final_status = protocol.get_status()
    logger.info(f"Adaptive tap complete - final position: {final_status}")
    
    return final_status


def dual_card_sequence_timed(protocol: BaseProtocol) -> None:
    """
    Perform taps on both cards in sequence using timed operations.
    
    :param protocol: Protocol instance to execute commands through
    """
    logger.info("Starting dual card sequence")
    
    # Tap Card 1 first
    logger.debug("Dual sequence: tapping Card 1")
    tap_card1_timed(protocol)
    time.sleep(0.5)  # Brief pause between cards
    
    # Tap Card 2 second  
    logger.debug("Dual sequence: tapping Card 2")
    tap_card2_timed(protocol)
    
    logger.info("Dual card sequence complete")


def alternating_taps_timed(protocol: BaseProtocol, iterations: int = 3) -> None:
    """
    Perform alternating taps between Card 1 and Card 2.
    
    :param protocol: Protocol instance to execute commands through
    :param iterations: Number of iterations to perform
    """
    logger.info(f"Starting {iterations} alternating taps")
    
    for i in range(iterations):
        logger.debug(f"Alternating taps: iteration {i+1}/{iterations}")
        
        # Card 1 tap
        tap_card1_timed(protocol)
        time.sleep(0.3)
        
        # Card 2 tap
        tap_card2_timed(protocol)
        time.sleep(0.3)
    
    logger.info("Alternating taps complete")


def quick_tap_card2(protocol: BaseProtocol, extend_time: int = 1385) -> None:
    """
    Quick Card 2 tap with minimal pause (for fast testing).
    
    :param protocol: Protocol instance to execute commands through
    :param extend_time: Custom extend time for tuning
    """
    logger.info(f"Quick Card 2 tap - extend {extend_time}ms")
    
    # Quick retract and return with minimal buffer
    logger.debug("Quick retract 1400ms with minimal buffer")
    protocol.retract_for_time(1400)
    _wait_for_operation(1400, 25)  # Reduced buffer for speed
    
    logger.debug(f"Quick extend {extend_time}ms with minimal buffer")
    protocol.extend_for_time(extend_time)  
    _wait_for_operation(extend_time, 25)  # Reduced buffer for speed
    
    logger.info("Quick tap complete")


def calibration_sequence_timed(protocol: BaseProtocol) -> dict:
    """
    Perform calibration sequence to measure actual timing.
    
    :param protocol: Protocol instance to execute commands through
    :return: Dictionary with timing measurements
    """
    logger.info("Starting calibration sequence")
    
    results = {}
    
    # Test different extend times
    test_timings = [1375, 1380, 1385, 1390, 1395]
    
    for timing in test_timings:
        logger.info(f"Testing extend_time: {timing}ms")
        
        # Get before status
        before = protocol.get_status()
        logger.debug(f"Before status: {before}")
        
        # Perform tap
        protocol.retract_for_time(1400)
        _wait_for_operation(1400)
        
        protocol.extend_for_time(timing)
        _wait_for_operation(timing)
        
        # Get after status
        after = protocol.get_status()
        logger.debug(f"After status: {after}")
        
        # Analyze result
        is_middle = "middle" in after.lower() if after else False
        
        results[timing] = {
            'before': before,
            'after': after, 
            'is_perfect': is_middle,
            'drift_direction': _analyze_drift_direction(after)
        }
        
        logger.info(f"Result for {timing}ms: {results[timing]['drift_direction']}")
        time.sleep(0.5)
    
    # Log summary
    logger.info("CALIBRATION RESULTS:")
    perfect_timings = []
    for timing, result in results.items():
        status = "PERFECT" if result['is_perfect'] else "DRIFT"
        logger.info(f"  {timing}ms: {status} - {result['drift_direction']}")
        if result['is_perfect']:
            perfect_timings.append(timing)
    
    if perfect_timings:
        logger.info(f"Recommended timing: {perfect_timings[0]}ms")
    else:
        logger.warning("No perfect timing found, manual adjustment needed")
    
    return results


def _analyze_drift_direction(status: str) -> str:
    """
    Analyze drift direction from status string.
    
    :param status: Status string from device
    :return: Human-readable drift analysis
    """
    if not status:
        return "❓ No status received"
    
    status_lower = status.lower()
    
    if "middle" in status_lower:
        return "✅ Perfect - at middle"
    elif "extended" in status_lower or "card1" in status_lower:
        return "⚠️  Too far forward - reduce extend_time" 
    elif "retracted" in status_lower or "card2" in status_lower:
        return "⚠️  Too far back - increase extend_time"
    else:
        return f"❓ Unknown position: {status}"


# Legacy compatibility functions (redirect to timed versions)
def safe_tap_card1_timed(protocol: BaseProtocol) -> None:
    """Legacy compatibility - safe Card 1 tap."""
    reset_to_middle_timed(protocol, "unknown")
    tap_card1_timed(protocol)


def safe_tap_card2_timed(protocol: BaseProtocol) -> None:
    """Legacy compatibility - safe Card 2 tap.""" 
    reset_to_middle_timed(protocol, "unknown")
    tap_card2_timed(protocol)


# ============================================================================
# SIMPLE FIRMWARE ENDPOINT FUNCTIONS
# ============================================================================
# These functions use built-in ESP32 endpoints - firmware handles all timing!

def simple_tap_card1(protocol: BaseProtocol) -> None:
    """
    Simple Card 1 tap using built-in ESP32 endpoint.
    
    This uses the firmware's built-in /tap_card1 endpoint which handles
    all timing internally. No Python-side timing calculations needed.
    
    :param protocol: Protocol instance to execute commands through
    """
    logger.info("Simple Card 1 tap using firmware endpoint")
    protocol.send_command("tap_card1")
    logger.info("Card 1 tap completed")


def simple_tap_card2(protocol: BaseProtocol) -> None:
    """
    Simple Card 2 tap using built-in ESP32 endpoint.
    
    This uses the firmware's built-in /tap_card2 endpoint which handles
    all timing internally. No Python-side timing calculations needed.
    
    :param protocol: Protocol instance to execute commands through
    """
    logger.info("Simple Card 2 tap using firmware endpoint")
    protocol.send_command("tap_card2")
    logger.info("Card 2 tap completed")


def simple_reset_to_middle(protocol: BaseProtocol) -> None:
    """
    Simple reset to middle using built-in ESP32 endpoint.
    
    This uses the firmware's built-in /reset_to_middle endpoint which handles
    all timing internally. No Python-side timing calculations needed.
    
    :param protocol: Protocol instance to execute commands through
    """
    logger.info("Simple reset to middle using firmware endpoint")
    protocol.send_command("reset_to_middle")
    logger.info("Reset to middle completed")


def simple_dual_card_sequence(protocol: BaseProtocol) -> None:
    """
    Simple dual card sequence using firmware endpoints only.
    
    Performs: reset -> tap_card1 -> reset -> tap_card2 -> reset
    All timing handled by firmware, very fast execution.
    
    :param protocol: Protocol instance to execute commands through
    """
    logger.info("Starting simple dual card sequence using firmware endpoints")
    
    simple_reset_to_middle(protocol)
    time.sleep(0.2)  # Brief pause between operations
    
    simple_tap_card1(protocol) 
    time.sleep(0.2)
    
    simple_reset_to_middle(protocol)
    time.sleep(0.2)
    
    simple_tap_card2(protocol)
    time.sleep(0.2)
    
    simple_reset_to_middle(protocol)  # End at middle
    
    logger.info("Simple dual card sequence completed")


# Safe versions with status checking
def safe_simple_tap_card1(protocol: BaseProtocol) -> None:
    """Safe simple Card 1 tap with middle reset first."""
    logger.info("Safe simple Card 1 tap")
    simple_reset_to_middle(protocol)
    time.sleep(0.5)  # Allow reset to complete
    simple_tap_card1(protocol)


def safe_simple_tap_card2(protocol: BaseProtocol) -> None:
    """Safe simple Card 2 tap with middle reset first."""
    logger.info("Safe simple Card 2 tap") 
    simple_reset_to_middle(protocol)
    time.sleep(0.5)  # Allow reset to complete
    simple_tap_card2(protocol)