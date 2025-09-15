#!/usr/bin/env python3
"""
Integration Test: Tapper System Core Functionality

Tests the core tapper system functionality using the actual TapperService API.
This focuses on basic operations and system behavior validation.
"""

import pytest
from typing import Generator
import sys

sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system import TapperService
from tappers_service.tapper_system.command import dual_sequences


@pytest.fixture
def tapper() -> Generator[TapperService, None, None]:
    """
    Fixture providing a connected TapperService.
    
    Clean, simple fixture - no complex setup.
    """
    service = TapperService("station1")
    
    if service.connect():
        yield service
        service.disconnect()
    else:
        pytest.skip("No tapper hardware available")


def test_basic_connection(tapper: TapperService):
    """Test basic connection and service functionality."""
    
    # Should be connected
    assert tapper.is_connected(), "Service should be connected"
    
    # Should have protocol
    assert tapper.protocol is not None, "Should have active protocol"
    
    # Should be able to get status
    status = tapper.get_status()
    assert status, "Should get valid status"
    
    print(f"\n✅ Connected via {tapper.protocol.protocol_name}")
    print(f"📊 Status: {status}")


def test_basic_card_operations(tapper: TapperService):
    """Test basic card operations using dual_sequences."""
    
    # Test Card 2 tap
    dual_sequences.tap_card2_timed(tapper.protocol)
    
    # Verify device responds
    status = tapper.protocol.get_status()
    assert status, "Should get status after Card 2 tap"
    
    print(f"\n🔴 Card 2 tap completed, status: {status}")


def test_protocol_commands(tapper: TapperService):
    """Test protocol command interface."""
    
    # Test extend for time command
    response = tapper.protocol.extend_for_time(1000)
    assert response, "Should get response from extend_for_time"
    
    # Wait for operation to complete
    import time
    time.sleep(1.1)  # 1000ms + buffer
    
    # Test retract for time command
    response = tapper.protocol.retract_for_time(1000)
    assert response, "Should get response from retract_for_time"
    
    time.sleep(1.1)  # Wait for completion
    
    print("\n⏱️ Timed operations completed successfully")


def test_service_context_manager(tapper: TapperService):
    """Test service context manager functionality."""
    
    # Test that existing service works as context
    with tapper as service:
        assert service.is_connected(), "Should be connected in context"
        status = service.get_status()
        assert status, "Should get status in context"
    
    # Service should still be connected after context (fixture manages it)
    assert tapper.is_connected(), "Fixture should still manage connection"
    
    print("\n🔄 Context manager test completed")


def test_dual_sequences_integration(tapper: TapperService):
    """Test integration with dual_sequences module."""
    
    # Test adaptive card 2 tap
    final_status = dual_sequences.adaptive_tap_card2(tapper.protocol, extend_time=1385)
    
    assert final_status, "Should get final status from adaptive tap"
    print(f"\n🧠 Adaptive tap completed: {final_status}")
    
    # Test quick tap
    dual_sequences.quick_tap_card2(tapper.protocol, extend_time=1390)
    
    print("\n⚡ Quick tap completed")


def test_protocol_agnostic_behavior(tapper: TapperService):
    """Test that operations work regardless of underlying protocol."""
    
    protocol_name = tapper.protocol.protocol_name
    print(f"\n🌐 Testing with protocol: {protocol_name}")
    
    # These should work with HTTP, MQTT, or Fallback protocol
    commands_to_test = [
        lambda: tapper.protocol.get_status(),
        lambda: tapper.protocol.extend_for_time(500),
        lambda: tapper.protocol.retract_for_time(500)
    ]
    
    for i, command in enumerate(commands_to_test):
        try:
            result = command()
            print(f"✅ Command {i+1} successful via {protocol_name}")
            
            if i > 0:  # For timed operations, wait for completion
                import time
                time.sleep(0.6)
                
        except Exception as e:
            pytest.fail(f"Command {i+1} failed with {protocol_name}: {e}")


@pytest.mark.parametrize("extend_time", [1380, 1385, 1390])
def test_timing_variations(tapper: TapperService, extend_time: int):
    """Test different timing values."""
    
    final_status = dual_sequences.adaptive_tap_card2(
        tapper.protocol, 
        extend_time=extend_time
    )
    
    # Basic validation
    assert final_status, f"Should get status with extend_time={extend_time}"
    
    print(f"\n🧪 Timing test: {extend_time}ms → {final_status}")


def test_service_health_check(tapper: TapperService):
    """Test service health check functionality."""
    
    health_info = tapper.health_check()
    
    # Validate health check structure
    assert "station_id" in health_info, "Should have station_id"
    assert "service_connected" in health_info, "Should have service_connected"
    assert "protocol_type" in health_info, "Should have protocol_type"
    assert "device_status" in health_info, "Should have device_status"
    
    # Validate health status
    assert health_info["service_connected"], "Service should be connected"
    assert health_info["station_id"] == "station1", "Should have correct station ID"
    
    print(f"\n🏥 Health check: {health_info}")


def test_send_raw_command(tapper: TapperService):
    """Test sending raw commands through service."""
    
    # Test raw status command
    result = tapper.send_command("status")
    assert result, "Should get response from raw status command"
    
    print(f"\n📨 Raw command response: {result}")


if __name__ == "__main__":
    # For direct execution
    pytest.main([__file__, "-v", "-s"])