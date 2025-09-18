from tapper_system.tapper_service.commands import dual_tap_sequences


def test_get_status(protocol, test_logger):
    """Test getting status from the protocol."""
    status = protocol.get_status()
    test_logger.info(f"Initial status: {status}")
    # Accept both dict and str, but check for expected keys/words
    if isinstance(status, dict):
        assert "position" in status, "Status dict should include 'position'"
    elif isinstance(status, str):
        lowered = status.lower()
        assert "position" in lowered, "Status string should mention 'position'"
        assert any(word in lowered for word in
                   ["middle", "card1", "card2", "idle", "retracted"]), "Status string should mention a known state"
    else:
        assert False, f"Unexpected status type: {type(status)}"


def test_reset_to_middle_timed(protocol):
    """Test resetting tapper to middle position from unknown."""
    dual_tap_sequences.to_middle(protocol)


def test_tap_card1_timed(protocol):
    """Test tapping card 1 using timed sequence."""
    dual_tap_sequences.tap_card1_timed(protocol)


def test_tap_card2_timed(protocol):
    """Test tapping card 2 using timed sequence."""
    dual_tap_sequences.tap_card2_timed(protocol)


def test_test_tap_card1_buitin_endpoint(protocol):
    """Test tapping card 1 using built-in command."""
    dual_tap_sequences.tap_card1_endpoint(protocol)


def test_tap_card2_builtin_endpoint(protocol):
    """Test tapping card 2 using built-in command."""
    dual_tap_sequences.tap_card2_endpoint(protocol)


def test_dual_card_sequence(protocol):
    """Test full dual card tap sequence using timed commands."""
    dual_tap_sequences.dual_card_sequence_endpoint(protocol)


def test_safe_tap_card1(protocol):
    """Test safe tap of card 1 with home reset."""
    dual_tap_sequences.safe_tap_card1_endpoint(protocol)