"""
Tapper sequence functions.

Simple functions that execute predefined sequences using any protocol.
Each function is focused, testable, and easy to understand.

Usage:
    from tappers_service import sequences.
    simple_tap(tapper.protocol)
    sequences.safe_simple_tap(tapper.protocol) # With home reset first
"""

import time

from tappers_service.protocols.base_protocol import BaseProtocol


def reset_to_home(protocol: BaseProtocol) -> None:
    """
    Reset tapper to home (retracted) position using timing.
    Always retracts for 3 seconds to ensure it's fully retracted.

    :param protocol: Protocol instance to execute commands through.
    """
    print("Resetting tapper to home position...")
    protocol.send_command("retract")
    time.sleep(3)  # 3 seconds should be enough to fully retract
    protocol.send_command("stop")
    print("Tapper reset to home position")


def simple_tap(protocol: BaseProtocol) -> None:
    """
    Execute a simple tap sequence: extend → wait → retract.

    :param protocol: Protocol instance to execute commands through.
    """
    protocol.send_command("extend")
    time.sleep(1.65)
    protocol.send_command("retract")
    time.sleep(2)
    protocol.send_command("stop")


def safe_simple_tap(protocol: BaseProtocol) -> None:
    """
    Execute simple tap with home reset first.
    Ensures tapper starts from known position.

    :param protocol: Protocol instance to execute commands through.
    """
    reset_to_home(protocol)
    simple_tap(protocol)
    print("Safe simple tap completed")


def long_tap(protocol: BaseProtocol) -> None:
    """
    Execute a long tap using the device's built-in tap command.

    :param protocol: Protocol instance to execute commands through.
    """
    protocol.send_command("tap")


def safe_long_tap(protocol: BaseProtocol) -> None:
    """
    Execute long tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    """
    reset_to_home(protocol)
    long_tap(protocol)
    print("Safe long tap completed")


def double_tap(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute two tap commands with status checking.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    protocol.send_command("tap")

    # Wait for first tap to complete
    _wait_for_idle(protocol)
    time.sleep(delay_ms / 1000.0)

    protocol.send_command("tap")


def safe_double_tap(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute double tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    reset_to_home(protocol)
    double_tap(protocol, delay_ms)
    print("Safe double tap completed")


def double_tap_manual(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute double tap using manual extend/retract commands.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    # First tap
    protocol.send_command("extend")
    time.sleep(2)  # Wait for extension
    protocol.send_command("retract")
    time.sleep(2)  # Wait for retraction

    # Delay between taps
    time.sleep(delay_ms / 1000.0)

    # Second tap
    protocol.send_command("extend")
    time.sleep(2)  # Wait for extension
    protocol.send_command("retract")
    time.sleep(2)  # Wait for retraction


def safe_double_tap_manual(protocol: BaseProtocol, delay_ms: int = 500) -> None:
    """
    Execute manual double tap with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param delay_ms: Delay between taps in milliseconds.
    """
    reset_to_home(protocol)
    double_tap_manual(protocol, delay_ms)
    print("Safe manual double tap completed")


def custom_sequence(protocol: BaseProtocol, extend_time: float = 1.5, retract_time: float = 2.0) -> None:
    """
    Execute a custom timing sequence.

    :param protocol: Protocol instance to execute commands through.
    :param extend_time: Time to stay extended in seconds.
    :param retract_time: Time for retraction in seconds.
    """
    protocol.send_command("extend")
    time.sleep(extend_time)
    protocol.send_command("retract")
    time.sleep(retract_time)
    protocol.send_command("stop")


def safe_custom_sequence(protocol: BaseProtocol, extend_time: float = 1.5, retract_time: float = 2.0) -> None:
    """
    Execute custom sequence with home reset first.

    :param protocol: Protocol instance to execute commands through.
    :param extend_time: Time to stay extended in seconds.
    :param retract_time: Time for retraction in seconds.
    """
    reset_to_home(protocol)
    custom_sequence(protocol, extend_time, retract_time)
    print("Safe custom sequence completed")


def _wait_for_idle(protocol: BaseProtocol, max_wait: int = 10) -> None:
    """
    Wait for device to return to idle state.
    Used internally by double_tap function.
    """
    for _ in range(max_wait * 10):  # Check every 100ms for max_wait seconds
        status = protocol.get_status()
        if status in ["idle", "retracted"] or "Operation: idle" in status:
            return
        time.sleep(0.1)


# ============ NEW: DUAL CARD SEQUENCES ============

def reset_to_middle(protocol: BaseProtocol) -> None:
    """
    Reset tapper to middle position for dual card operations.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Resetting tapper to middle position...")
    protocol.send_command("reset_to_middle")
    _wait_for_dual_card_idle(protocol)
    print("Tapper reset to middle position")


def tap_card1(protocol: BaseProtocol) -> None:
    """
    Tap Card 1 (extend direction from middle).
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Tapping Card 1...")
    protocol.send_command("tap_card1")
    _wait_for_dual_card_idle(protocol)
    print("Card 1 tap completed")


def tap_card2(protocol: BaseProtocol) -> None:
    """
    Tap Card 2 (retract direction from middle).
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Tapping Card 2...")
    protocol.send_command("tap_card2")
    _wait_for_dual_card_idle(protocol)
    print("Card 2 tap completed")


def safe_tap_card1(protocol: BaseProtocol) -> None:
    """
    Tap Card 1 with automatic middle reset first.
    Ensures tapper starts from known middle position.
    
    :param protocol: Protocol instance to execute commands through.
    """
    reset_to_middle(protocol)
    tap_card1(protocol)
    print("Safe Card 1 tap completed")


def safe_tap_card2(protocol: BaseProtocol) -> None:
    """
    Tap Card 2 with automatic middle reset first.
    Ensures tapper starts from known middle position.
    
    :param protocol: Protocol instance to execute commands through.
    """
    reset_to_middle(protocol)
    tap_card2(protocol)
    print("Safe Card 2 tap completed")


def dual_card_sequence(protocol: BaseProtocol, delay_between_taps: float = 1.0) -> None:
    """
    Execute a complete dual card sequence: Card 1 → delay → Card 2.
    
    :param protocol: Protocol instance to execute commands through.
    :param delay_between_taps: Delay between card taps in seconds.
    """
    print("Starting dual card sequence...")
    reset_to_middle(protocol)
    
    print("Tapping Card 1...")
    tap_card1(protocol)
    
    print(f"Waiting {delay_between_taps} seconds between taps...")
    time.sleep(delay_between_taps)
    
    print("Tapping Card 2...")
    tap_card2(protocol)
    
    print("Dual card sequence completed")


def alternating_card_taps(protocol: BaseProtocol, iterations: int = 3, delay_between_taps: float = 0.5) -> None:
    """
    Execute alternating card taps: Card1 → Card2 → Card1 → Card2...
    
    :param protocol: Protocol instance to execute commands through.
    :param iterations: Number of complete Card1+Card2 cycles.
    :param delay_between_taps: Delay between individual taps in seconds.
    """
    print(f"Starting alternating card taps for {iterations} iterations...")
    reset_to_middle(protocol)
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}: Card 1")
        tap_card1(protocol)
        
        if delay_between_taps > 0:
            time.sleep(delay_between_taps)
        
        print(f"Iteration {i+1}/{iterations}: Card 2")
        tap_card2(protocol)
        
        if delay_between_taps > 0 and i < iterations - 1:  # Don't delay after last iteration
            time.sleep(delay_between_taps)
    
    print("Alternating card taps completed")


def capture_middle_position(protocol: BaseProtocol) -> None:
    """
    Capture current position as middle for calibration.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Capturing current position as middle...")
    protocol.send_command("capture_middle")
    time.sleep(0.5)  # Give ESP32 time to process
    print("Current position captured as middle")


def set_power_source_12v(protocol: BaseProtocol) -> None:
    """
    Set tapper to use 12V external power timing.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Setting power source to 12V external...")
    protocol.send_command("power_12v")
    time.sleep(0.2)
    print("Power source set to 12V - using fast timing")


def set_power_source_usb(protocol: BaseProtocol) -> None:
    """
    Set tapper to use USB power timing (slower).
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Setting power source to USB...")
    protocol.send_command("power_usb")
    time.sleep(0.2)
    print("Power source set to USB - using slow timing (2.3x multiplier)")


def manual_calibration_extend(protocol: BaseProtocol) -> None:
    """
    Start manual extend for timing calibration.
    Use manual_calibration_stop() to capture timing.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Starting manual extend for calibration...")
    print("Use manual_calibration_stop() to capture timing")
    protocol.send_command("manual_extend")


def manual_calibration_retract(protocol: BaseProtocol) -> None:
    """
    Start manual retract for timing calibration.
    Use manual_calibration_stop() to capture timing.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Starting manual retract for calibration...")
    print("Use manual_calibration_stop() to capture timing")
    protocol.send_command("manual_retract")


def manual_calibration_stop(protocol: BaseProtocol) -> None:
    """
    Stop manual operation and capture timing measurement.
    
    :param protocol: Protocol instance to execute commands through.
    """
    print("Stopping manual operation and capturing timing...")
    protocol.send_command("manual_stop")
    time.sleep(0.5)
    print("Timing measurement captured - check ESP32 serial output")


def _wait_for_dual_card_idle(protocol: BaseProtocol, max_wait: int = 5) -> None:
    """
    Wait for dual card operation to complete.
    Looks for "Operation: idle" in detailed status.
    """
    print("Waiting for dual card operation to complete...")
    for i in range(max_wait * 10):  # Check every 100ms for max_wait seconds
        status = protocol.get_status()
        
        # Debug: Show status on first few checks
        if i < 3:
            print(f"Status check {i+1}: {status}")
        
        # Check for dual card idle status
        if "Operation: idle" in status or "idle" == status.strip():
            print(f"✅ Operation completed after {(i+1)*0.1:.1f}s")
            return
        
        # Show progress every 2 seconds but less verbose
        if i > 0 and i % 20 == 0:
            print(f"Still waiting {i/10:.1f}s... Status: {status}")
        
        time.sleep(0.1)
    
    print(f"⚠️ Operation did not complete within {max_wait} seconds")
    print(f"Final status: {protocol.get_status()}")
    print("Proceeding anyway - operation may have completed but status not detected")