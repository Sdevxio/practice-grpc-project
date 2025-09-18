"""
Dual card sequences using timed operations approach.

This module provides functions to control a dual-card tapper device,
enabling operations such as tapping each card, resetting to the middle position,
and performing sequences of taps. The functions use timed commands to
control the tapper's movements, with built-in wait times to ensure operations
complete before proceeding.

"""

import time

from tapper_system.tapper_service import BaseProtocol
from test_framework.utils import get_logger

logger = get_logger("DualSequences")


# ================= Timed Tap Commands ==================
# =======================================================

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
    Wait for a device to return to idle state (fallback method).

    :param protocol: Protocol instance to check status through
    :param max_wait: Maximum wait time in seconds
    :return: True if a device became idle, False if timeout
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


def quick_timed_tap_card1(protocol: BaseProtocol, extend_time: int = 1385) -> None:
    """
    Quick tap Card 1 with minial pause.

    :param protocol: Protocol instance to execute commands through.
    :param extend_time: Time to extend in milliseconds.
    """
    logger.info(f"Quick tapping Card 1: extend {extend_time}ms")

    # Quick extend and return with minimal buffer
    logger.debug(f"Extending 1485ms to Card 1")
    protocol.extend_for_time(1485)
    _wait_for_operation(1485, buffer_ms=20)

    logger.debug(f"Retracting 995ms to middle")
    protocol.retract_for_time(995)
    _wait_for_operation(extend_time, buffer_ms=20)
    logger.info("Quick Card 1 tap complete.")


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


# Legacy compatibility functions (redirect to timed versions)
def safe_tap_card1_timed(protocol: BaseProtocol) -> None:
    """Legacy compatibility - safe Card 1 tap."""
    reset_to_middle_timed(protocol, "unknown")
    tap_card1_timed(protocol)


def safe_tap_card2_timed(protocol: BaseProtocol) -> None:
    """Legacy compatibility - safe Card 2 tap."""
    reset_to_middle_timed(protocol, "unknown")
    tap_card2_timed(protocol)


# ================= Built-in Tap Commands ==================
# ==========================================================

def tap_card1_endpoint(protocol: BaseProtocol) -> None:
    """
    Perform tap Card 1 using single tap command.
    Using the built-in tap command /tap_card1.

    This is firmware's built-in /tap_card1 endpoint that handles all timing internally.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Tapping Card 1 via tap endpoint command")
    protocol.send_command("tap_card1")
    logger.info("Card 1 tap complete.")


def tap_card2_endpoint(protocol: BaseProtocol) -> None:
    """
    Perform tap Card 2 using single tap command.
    Using the built-in tap command /tap_card2.

    This is firmware's built-in /tap_card2 endpoint that handles all timing internally.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Tapping Card 2 via tap endpoint command")
    protocol.send_command("tap_card2")
    logger.info("Card 2 tap complete.")


def reset_to_middle_endpoint(protocol: BaseProtocol) -> None:
    """
    Reset the tapper to the middle position using built-in reset command.
    Using the built-in reset command /reset_to_middle.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Resetting to middle via reset_to_middle endpoint command")
    protocol.send_command("reset_to_middle")
    _wait_for_idle(protocol)
    logger.info("Reset to middle complete.")


def dual_card_sequence_endpoint(protocol: BaseProtocol) -> None:
    """
    Perform a dual card tap sequence using built-in tap commands.
    Using the built-in tap commands /tap_card1 and /tap_card2.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Starting dual card tap sequence via built-in endpoint commands.")

    reset_to_middle_timed(protocol)
    time.sleep(0.3)
    reset_to_middle_endpoint(protocol)

    tap_card1_timed(protocol)
    _wait_for_idle(protocol, max_wait=50)

    tap_card2_timed(protocol)
    _wait_for_idle(protocol, max_wait=50)
    logger.info("Dual card tap sequence complete.")


def safe_tap_card1_endpoint(protocol: BaseProtocol) -> None:
    """
    Safely tap Card 1 by ensuring the tapper is in the middle position first.
    Using the built-in tap command /tap_card1.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Safely tapping Card 1 with home reset.")

    reset_to_middle_timed(protocol)
    _wait_for_idle(protocol, max_wait=10)
    reset_to_middle_endpoint(protocol)
    tap_card1_endpoint(protocol)

    logger.info("Safe Card 1 tap complete.")


def safe_tap_card2_endpoint(protocol: BaseProtocol) -> None:
    """
    Safely tap Card 2 by ensuring the tapper is in the middle position first.
    Using the built-in tap command /tap_card2.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Safely tapping Card 2 with home reset.")

    reset_to_middle_timed(protocol)
    _wait_for_idle(protocol, max_wait=10)
    tap_card2_endpoint(protocol)

    logger.info("Safe Card 2 tap complete.")


def to_middle(protocol: BaseProtocol):
    """ To middle position """
    logger.info("Moving to middle position.")
    reset_to_middle_timed(protocol)
    _wait_for_idle(protocol, max_wait=10)
    reset_to_middle_endpoint(protocol)