#!/usr/bin/env python3
"""
Example: Clean Pytest with Dual Protocol Tapper System

This shows how to write clean tests using the tapper_system architecture.
The tests work identically with HTTP or MQTT - the system handles protocol fallback.
"""

import pytest
import sys
from typing import Generator

sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system import TapperService
from tappers_service.tapper_system.command import dual_sequences


@pytest.fixture
def tapper() -> Generator[TapperService, None, None]:
    """
    Clean tapper fixture with dual protocol support.
    
    Automatically connects via HTTP → MQTT fallback.
    No need to specify protocol - the system handles it.
    """
    service = TapperService("station1")
    
    if service.connect():
        yield service
        service.disconnect()
    else:
        pytest.skip("No tapper protocols available (HTTP/MQTT)")


def test_dual_protocol_connection(tapper: TapperService):
    """Test that dual protocol connection works."""
    
    # Should be connected via one of the protocols
    assert tapper.protocol is not None, "Should have connected via HTTP or MQTT"
    
    # Should have an active protocol name
    protocol_name = tapper.protocol.protocol_name
    assert protocol_name in ['HTTP', 'MQTT', 'Fallback'], f"Unexpected protocol: {protocol_name}"
    
    print(f"\n✅ Connected via {protocol_name}")


def test_dual_card_operations(tapper: TapperService):
    """Test dual card operations work with any protocol."""
    
    # Test Card 2 tap - works with HTTP or MQTT
    dual_sequences.tap_card2_timed(tapper.protocol)
    
    # Verify device is responsive
    status = tapper.protocol.get_status()
    assert status, "Should receive status from device"
    
    print(f"\n🔴 Card 2 tap completed, status: {status}")


def test_custom_timing_operations(tapper: TapperService):
    """Test custom timing operations."""
    
    # Test adaptive tap with custom timing
    final_status = dual_sequences.adaptive_tap_card2(tapper.protocol, extend_time=1385)
    
    assert final_status, "Should receive final status"
    print(f"\n🧠 Adaptive tap completed, final position: {final_status}")


def test_sequence_operations(tapper: TapperService):
    """Test sequence operations."""
    
    # Test dual card sequence
    dual_sequences.dual_card_sequence_timed(tapper.protocol)
    
    # Verify device is still responsive
    status = tapper.protocol.get_status()
    assert status, "Device should be responsive after sequence"
    
    print(f"\n🔄 Dual card sequence completed")


def test_protocol_agnostic_commands(tapper: TapperService):
    """Test that all commands work regardless of protocol."""
    
    # These commands work identically with HTTP or MQTT
    commands_to_test = [
        lambda: dual_sequences.quick_tap_card2(tapper.protocol),
        lambda: dual_sequences.tap_card2_timed(tapper.protocol, retract_time=1400, return_time=1385),
        lambda: tapper.protocol.get_status()
    ]
    
    for i, command in enumerate(commands_to_test):
        try:
            result = command()
            print(f"\n✅ Command {i+1} executed successfully via {tapper.protocol.protocol_name}")
        except Exception as e:
            pytest.fail(f"Command {i+1} failed: {e}")


@pytest.mark.parametrize("extend_time", [1380, 1385, 1390])
def test_timing_variations(tapper: TapperService, extend_time: int):
    """Test different timing values - protocol independent."""
    
    # This test works with any protocol
    final_status = dual_sequences.adaptive_tap_card2(tapper.protocol, extend_time=extend_time)
    
    # Basic validation
    assert final_status, f"Should receive status with extend_time={extend_time}"
    
    print(f"\n🧪 Timing test: {extend_time}ms → {final_status}")


def test_fallback_protocol_behavior(tapper: TapperService):
    """Test fallback protocol behavior."""
    
    # Check if we can get active protocol information
    if hasattr(tapper.protocol, 'get_active_protocols'):
        active_protocols = tapper.protocol.get_active_protocols()
        print(f"\n🔧 Active protocols: {active_protocols}")
    
    # Verify protocol works
    status = tapper.protocol.get_status()
    assert status, "Protocol should be functional"


def test_context_manager_usage():
    """Test context manager usage with dual protocols."""
    
    with TapperService("station1") as service:
        if service.protocol is None:
            pytest.skip("No protocols available")
            
        # Service should be connected
        assert service.protocol is not None
        
        # Should work with any protocol
        status = service.protocol.get_status()
        assert status, "Should get status via context manager"
        
        print(f"\n🔄 Context manager test via {service.protocol.protocol_name}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s", "--tb=short"])