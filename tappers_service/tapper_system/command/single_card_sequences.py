"""
Legacy tapper sequence functions.

Legacy single-card tapper sequences for backward compatibility.
For modern dual-card operations, use dual_sequences module instead.

These functions maintain the original single-card tapper behavior
with home position resets and basic extend/retract operations.

Usage:
    from tappers_service.tapper_system.command import legacy_sequences
    legacy_sequences.legacy_simple_tap(tapper.protocol)
    legacy_sequences.safe_legacy_simple_tap(tapper.protocol) # With home reset first
"""

import time

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from test_framework.utils import get_logger

# Module logger
logger = get_logger("LegacySequences")


def legacy_reset_to_home(protocol: BaseProtocol) -> None:
    """
    Reset tapper to home (retracted) position using timing.
    Always retracts for 3 seconds to ensure it's fully retracted.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.info("Resetting tapper to home position...")
    protocol.send_command("retract")
    time.sleep(3)  # 3 seconds should be enough to fully retract
    protocol.send_command("stop")
    logger.info("Tapper reset to home position")


def legacy_simple_tap(protocol: BaseProtocol) -> None:
    """
    Execute a legacy simple tap sequence: extend → wait → retract.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.debug("Starting legacy simple tap")
    protocol.send_command("extend")
    time.sleep(1.65)
    protocol.send_command("retract")
    time.sleep(2)
    protocol.send_command("stop")
    logger.info("Legacy simple tap completed")


def safe_legacy_simple_tap(protocol: BaseProtocol) -> None:
    """
    Execute legacy simple tap with home reset first.
    Ensures tapper starts from known position.

    :param protocol: Protocol instance to execute commands through.
    """
    legacy_reset_to_home(protocol)
    legacy_simple_tap(protocol)
    logger.info("Safe legacy simple tap completed")


def legacy_long_tap(protocol: BaseProtocol) -> None:
    """
    Execute a legacy long tap using the device's built-in tap command.

    :param protocol: Protocol instance to execute commands through.
    """
    logger.debug("Starting legacy long tap")
    protocol.send_command("tap")
    logger.info("Legacy long tap completed")


def safe_legacy_long_tap(protocol: BaseProtocol) -> None:
    """
    Execute legacy long tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    """
    legacy_reset_to_home(protocol)
    legacy_long_tap(protocol)
    logger.info("Safe legacy long tap completed")


def legacy_double_tap(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute two legacy tap commands with status checking.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    logger.info(f"Starting legacy double tap with {delay_ms}ms delay")
    protocol.send_command("tap")

    # Wait for first tap to complete
    _wait_for_legacy_idle(protocol)
    time.sleep(delay_ms / 1000.0)

    protocol.send_command("tap")
    logger.info("Legacy double tap completed")


def safe_legacy_double_tap(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute legacy double tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    legacy_reset_to_home(protocol)
    legacy_double_tap(protocol, delay_ms)
    logger.info("Safe legacy double tap completed")


def legacy_double_tap_manual(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute legacy double tap using manual extend/retract commands.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    logger.info(f"Starting manual legacy double tap with {delay_ms}ms delay")
    
    # First tap
    logger.debug("Manual tap 1: extending")
    protocol.send_command("extend")
    time.sleep(2)  # Wait for extension
    logger.debug("Manual tap 1: retracting")
    protocol.send_command("retract")
    time.sleep(2)  # Wait for retraction

    # Delay between taps
    logger.debug(f"Delay between taps: {delay_ms}ms")
    time.sleep(delay_ms / 1000.0)

    # Second tap
    logger.debug("Manual tap 2: extending")
    protocol.send_command("extend")
    time.sleep(2)  # Wait for extension
    logger.debug("Manual tap 2: retracting")
    protocol.send_command("retract")
    time.sleep(2)  # Wait for retraction
    
    logger.info("Manual legacy double tap completed")


def safe_legacy_double_tap_manual(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute manual legacy double tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    legacy_reset_to_home(protocol)
    legacy_double_tap_manual(protocol, delay_ms)
    logger.info("Safe manual legacy double tap completed")


def legacy_custom_sequence(protocol: BaseProtocol, extend_time: float = 1.5, retract_time: float = 2.0) -> None:
    """
    Execute a legacy custom timing sequence.

    :param protocol: Protocol instance to execute commands through.
    :param extend_time: Time to stay extended in seconds.
    :param retract_time: Time for retraction in seconds.
    """
    logger.info(f"Starting legacy custom sequence: extend {extend_time}s, retract {retract_time}s")
    protocol.send_command("extend")
    time.sleep(extend_time)
    protocol.send_command("retract")
    time.sleep(retract_time)
    protocol.send_command("stop")
    logger.info("Legacy custom sequence completed")


def safe_legacy_custom_sequence(protocol: BaseProtocol, extend_time: float = 1.5, retract_time: float = 2.0) -> None:
    """
    Execute legacy custom sequence with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param extend_time: Time to stay extended in seconds.
    :param retract_time: Time for retraction in seconds.
    """
    legacy_reset_to_home(protocol)
    legacy_custom_sequence(protocol, extend_time, retract_time)
    logger.info("Safe legacy custom sequence completed")


def _wait_for_legacy_idle(protocol: BaseProtocol, max_wait: int = 10) -> None:
    """
    Wait for device to return to legacy idle state.
    Used internally by legacy double_tap functions.
    """
    logger.debug(f"Waiting for legacy idle state (max {max_wait}s)")
    for i in range(max_wait * 10):  # Check every 100ms for max_wait seconds
        status = protocol.get_status()
        if status in ["idle", "retracted"] or "Operation: idle" in status:
            logger.debug(f"Device reached idle after {(i+1)*0.1:.1f}s")
            return
        time.sleep(0.1)
    logger.warning(f"Device did not reach idle within {max_wait}s")


# ============ DEPRECATED: LEGACY DUAL CARD SEQUENCES ============
# These functions are deprecated. Use dual_sequences module for modern dual card operations.

def deprecated_reset_to_middle(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Reset tapper to middle position for dual card operations.
    Use dual_sequences.reset_to_middle_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_reset_to_middle is deprecated. Use dual_sequences.reset_to_middle_timed() instead")
    logger.info("Resetting tapper to middle position...")
    protocol.send_command("reset_to_middle")
    _wait_for_deprecated_dual_card_idle(protocol)
    logger.info("Tapper reset to middle position")


def deprecated_tap_card1(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Tap Card 1 (extend direction from middle).
    Use dual_sequences.tap_card1_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_tap_card1 is deprecated. Use dual_sequences.tap_card1_timed() instead")
    logger.info("Tapping Card 1...")
    protocol.send_command("tap_card1")
    _wait_for_deprecated_dual_card_idle(protocol)
    logger.info("Card 1 tap completed")


def deprecated_tap_card2(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Tap Card 2 (retract direction from middle).
    Use dual_sequences.tap_card2_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_tap_card2 is deprecated. Use dual_sequences.tap_card2_timed() instead")
    logger.info("Tapping Card 2...")
    protocol.send_command("tap_card2")
    _wait_for_deprecated_dual_card_idle(protocol)
    logger.info("Card 2 tap completed")


def deprecated_safe_tap_card1(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Tap Card 1 with automatic middle reset first.
    Use dual_sequences.safe_tap_card1_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_safe_tap_card1 is deprecated. Use dual_sequences.safe_tap_card1_timed() instead")
    deprecated_reset_to_middle(protocol)
    deprecated_tap_card1(protocol)
    logger.info("Safe Card 1 tap completed")


def deprecated_safe_tap_card2(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Tap Card 2 with automatic middle reset first.
    Use dual_sequences.safe_tap_card2_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_safe_tap_card2 is deprecated. Use dual_sequences.safe_tap_card2_timed() instead")
    deprecated_reset_to_middle(protocol)
    deprecated_tap_card2(protocol)
    logger.info("Safe Card 2 tap completed")


def deprecated_dual_card_sequence(protocol: BaseProtocol, delay_between_taps: float = 1.0) -> None:
    """
    DEPRECATED: Execute a complete dual card sequence: Card 1 → delay → Card 2.
    Use dual_sequences.dual_card_sequence_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    :param delay_between_taps: Delay between card taps in seconds.
    """
    logger.warning("deprecated_dual_card_sequence is deprecated. Use dual_sequences.dual_card_sequence_timed() instead")
    logger.info("Starting deprecated dual card sequence...")
    deprecated_reset_to_middle(protocol)
    
    logger.info("Tapping Card 1...")
    deprecated_tap_card1(protocol)
    
    logger.info(f"Waiting {delay_between_taps} seconds between taps...")
    time.sleep(delay_between_taps)
    
    logger.info("Tapping Card 2...")
    deprecated_tap_card2(protocol)
    
    logger.info("Deprecated dual card sequence completed")


def deprecated_alternating_card_taps(protocol: BaseProtocol, iterations: int = 3, delay_between_taps: float = 0.5) -> None:
    """
    DEPRECATED: Execute alternating card taps: Card1 → Card2 → Card1 → Card2...
    Use dual_sequences.alternating_taps_timed() instead.
    
    :param protocol: Protocol instance to execute commands through.
    :param iterations: Number of complete Card1+Card2 cycles.
    :param delay_between_taps: Delay between individual taps in seconds.
    """
    logger.warning("deprecated_alternating_card_taps is deprecated. Use dual_sequences.alternating_taps_timed() instead")
    logger.info(f"Starting deprecated alternating card taps for {iterations} iterations...")
    deprecated_reset_to_middle(protocol)
    
    for i in range(iterations):
        logger.info(f"Iteration {i+1}/{iterations}: Card 1")
        deprecated_tap_card1(protocol)
        
        if delay_between_taps > 0:
            time.sleep(delay_between_taps)
        
        logger.info(f"Iteration {i+1}/{iterations}: Card 2")
        deprecated_tap_card2(protocol)
        
        if delay_between_taps > 0 and i < iterations - 1:  # Don't delay after last iteration
            time.sleep(delay_between_taps)
    
    logger.info("Deprecated alternating card taps completed")


def deprecated_capture_middle_position(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Capture current position as middle for calibration.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_capture_middle_position is deprecated")
    logger.info("Capturing current position as middle...")
    protocol.send_command("capture_middle")
    time.sleep(0.5)  # Give ESP32 time to process
    logger.info("Current position captured as middle")


def deprecated_set_power_source_12v(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Set tapper to use 12V external power timing.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_set_power_source_12v is deprecated")
    logger.info("Setting power source to 12V external...")
    protocol.send_command("power_12v")
    time.sleep(0.2)
    logger.info("Power source set to 12V - using fast timing")


def deprecated_set_power_source_usb(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Set tapper to use USB power timing (slower).
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_set_power_source_usb is deprecated")
    logger.info("Setting power source to USB...")
    protocol.send_command("power_usb")
    time.sleep(0.2)
    logger.info("Power source set to USB - using slow timing (2.3x multiplier)")


def deprecated_manual_calibration_extend(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Start manual extend for timing calibration.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_manual_calibration_extend is deprecated")
    logger.info("Starting manual extend for calibration...")
    logger.info("Use deprecated_manual_calibration_stop() to capture timing")
    protocol.send_command("manual_extend")


def deprecated_manual_calibration_retract(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Start manual retract for timing calibration.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_manual_calibration_retract is deprecated")
    logger.info("Starting manual retract for calibration...")
    logger.info("Use deprecated_manual_calibration_stop() to capture timing")
    protocol.send_command("manual_retract")


def deprecated_manual_calibration_stop(protocol: BaseProtocol) -> None:
    """
    DEPRECATED: Stop manual operation and capture timing measurement.
    
    :param protocol: Protocol instance to execute commands through.
    """
    logger.warning("deprecated_manual_calibration_stop is deprecated")
    logger.info("Stopping manual operation and capturing timing...")
    protocol.send_command("manual_stop")
    time.sleep(0.5)
    logger.info("Timing measurement captured - check ESP32 serial output")


def _wait_for_deprecated_dual_card_idle(protocol: BaseProtocol, max_wait: int = 5) -> None:
    """
    DEPRECATED: Wait for dual card operation to complete.
    Use dual_sequences._wait_for_idle() instead.
    """
    logger.debug("Waiting for deprecated dual card operation to complete...")
    for i in range(max_wait * 10):  # Check every 100ms for max_wait seconds
        status = protocol.get_status()
        
        # Debug: Show status on first few checks
        if i < 3:
            logger.debug(f"Status check {i+1}: {status}")
        
        # Check for dual card idle status
        if "Operation: idle" in status or "idle" == status.strip():
            logger.info(f"✅ Operation completed after {(i+1)*0.1:.1f}s")
            return
        
        # Show progress every 2 seconds but less verbose
        if i > 0 and i % 20 == 0:
            logger.debug(f"Still waiting {i/10:.1f}s... Status: {status}")
        
        time.sleep(0.1)
    
    logger.warning(f"⚠️ Operation did not complete within {max_wait} seconds")
    logger.warning(f"Final status: {protocol.get_status()}")
    logger.warning("Proceeding anyway - operation may have completed but status not detected")


# ============ BACKWARD COMPATIBILITY ALIASES ============
# These maintain the original function names for existing code

# Legacy single-card function aliases
reset_to_home = legacy_reset_to_home
simple_tap = legacy_simple_tap
safe_simple_tap = safe_legacy_simple_tap
long_tap = legacy_long_tap
safe_long_tap = safe_legacy_long_tap
double_tap = legacy_double_tap
safe_double_tap = safe_legacy_double_tap
double_tap_manual = legacy_double_tap_manual
safe_double_tap_manual = safe_legacy_double_tap_manual
custom_sequence = legacy_custom_sequence
safe_custom_sequence = safe_legacy_custom_sequence

# Deprecated dual card function aliases
reset_to_middle = deprecated_reset_to_middle
tap_card1 = deprecated_tap_card1
tap_card2 = deprecated_tap_card2
safe_tap_card1 = deprecated_safe_tap_card1
safe_tap_card2 = deprecated_safe_tap_card2
dual_card_sequence = deprecated_dual_card_sequence
alternating_card_taps = deprecated_alternating_card_taps
capture_middle_position = deprecated_capture_middle_position
set_power_source_12v = deprecated_set_power_source_12v
set_power_source_usb = deprecated_set_power_source_usb
manual_calibration_extend = deprecated_manual_calibration_extend
manual_calibration_retract = deprecated_manual_calibration_retract
manual_calibration_stop = deprecated_manual_calibration_stop