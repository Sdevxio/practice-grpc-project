#!/usr/bin/env python3
"""
Pytest tests for smart tuning with timed operations.
Uses fixtures for clean test setup and teardown.
"""

import pytest
import time
from typing import Generator

from tappers_service.tapper_system.controller.tapper_service import TapperService
from tappers_service.tapper_system.command import dual_sequences


@pytest.fixture
def tapper_service() -> Generator[TapperService, None, None]:
    """
    Fixture that provides a connected TapperService instance.
    Handles connection and cleanup automatically.
    """
    service = TapperService("station1")
    service.connect()
    
    yield service  # This is what the test gets
    
    # Cleanup after test
    service.disconnect()


@pytest.fixture
def tuning_config():
    """
    Fixture that provides tuning configuration.
    Modify these values to test different timings.
    """
    return {
        "retract_time": 1400,    # Fixed - time to reach Card 2
        "extend_time": 1385,     # ← TUNE THIS VALUE to find perfect timing
        "wait_buffer": 50        # Extra wait time buffer
    }


# Helper functions
def _wait_for_operation(duration_ms: int, buffer_ms: int = 50):
    """Wait for timed operation to complete."""
    wait_time = (duration_ms + buffer_ms) / 1000.0
    time.sleep(wait_time)

def _analyze_drift(status: str) -> str:
    """Analyze drift from status and return guidance."""
    status_lower = status.lower()
    
    if "middle" in status_lower:
        return "✅ PERFECT - Still at middle position!"
    elif "extended" in status_lower or "card1" in status_lower:
        return "⚠️  DRIFT: Too far FORWARD → REDUCE extend_time by 5-10ms"
    elif "retracted" in status_lower or "card2" in status_lower:
        return "⚠️  DRIFT: Too far BACK → INCREASE extend_time by 5-10ms"
    else:
        return f"❓ Unknown position: {status}"


def test_single_timed_tap(tapper_service: TapperService, tuning_config: dict):
    """Test a single timed tap operation."""
    
    print(f"\n🔧 Testing extend_time = {tuning_config['extend_time']}ms")
    
    # Get initial status
    initial_status = tapper_service.protocol.get_status()
    print(f"BEFORE: {initial_status}")
    
    # Retract to Card 2
    print(f"↓ Retracting {tuning_config['retract_time']}ms to Card 2...")
    tapper_service.protocol.retract_for_time(tuning_config['retract_time'])
    _wait_for_operation(tuning_config['retract_time'], tuning_config['wait_buffer'])
    
    # Return to middle
    print(f"↑ Extending {tuning_config['extend_time']}ms back to middle...")
    tapper_service.protocol.extend_for_time(tuning_config['extend_time'])
    _wait_for_operation(tuning_config['extend_time'], tuning_config['wait_buffer'])
    
    # Check final position
    final_status = tapper_service.protocol.get_status()
    print(f"AFTER:  {final_status}")
    
    # Analyze drift
    drift_analysis = _analyze_drift(final_status)
    print(f"ANALYSIS: {drift_analysis}")
    
    # Assert that we're back at middle (for automated testing)
    assert "middle" in final_status.lower(), f"Expected middle position, got: {final_status}"

def test_multiple_taps_drift_detection(tapper_service: TapperService, tuning_config: dict):
    """Test multiple taps to detect drift accumulation."""
    
    print(f"\n📊 Testing {tuning_config['extend_time']}ms with multiple taps")
    
    positions = []
    
    for tap_num in range(1, 4):  # Test 3 taps
        print(f"\n{'='*30}")
        print(f"TAP #{tap_num}")
        print(f"{'='*30}")
        
        # Before tap
        before_status = tapper_service.protocol.get_status()
        positions.append(f"Before tap {tap_num}: {before_status}")
        
        # Perform tap
        tapper_service.protocol.retract_for_time(tuning_config['retract_time'])
        _wait_for_operation(tuning_config['retract_time'], tuning_config['wait_buffer'])
        
        tapper_service.protocol.extend_for_time(tuning_config['extend_time'])
        _wait_for_operation(tuning_config['extend_time'], tuning_config['wait_buffer'])
        
        # After tap
        after_status = tapper_service.protocol.get_status()
        positions.append(f"After tap {tap_num}: {after_status}")
        
        # Brief pause between taps
        time.sleep(0.2)
    
    # Print drift analysis
    print(f"\n📈 DRIFT ANALYSIS:")
    for position in positions:
        print(f"  {position}")
    
    # Check final position
    final_status = tapper_service.protocol.get_status()
    drift_analysis = _analyze_drift(final_status)
    print(f"\n🎯 FINAL ANALYSIS: {drift_analysis}")
    
    # For automated testing - warn if not at middle
    if "middle" not in final_status.lower():
        pytest.fail(f"Drift detected after multiple taps. {drift_analysis}")

def test_timing_variations(tapper_service: TapperService):
    """Test different extend_time values to find optimal timing."""
    
    # Different timing values to test
    timing_values = [1375, 1380, 1385, 1390, 1395]
    results = {}
    
    for extend_time in timing_values:
        print(f"\n🧪 Testing extend_time: {extend_time}ms")
        
        # Perform single tap
        tapper_service.protocol.retract_for_time(1400)
        _wait_for_operation(1400, 50)
        
        tapper_service.protocol.extend_for_time(extend_time)
        _wait_for_operation(extend_time, 50)
        
        # Check result
        status = tapper_service.protocol.get_status()
        drift_analysis = _analyze_drift(status)
        results[extend_time] = {
            'status': status,
            'analysis': drift_analysis,
            'is_perfect': "middle" in status.lower()
        }
        
        print(f"   Result: {drift_analysis}")
        time.sleep(0.5)  # Brief pause between tests
    
    # Print summary
    print(f"\n📊 TIMING VARIATION RESULTS:")
    perfect_timings = []
    for timing, result in results.items():
        status_icon = "✅" if result['is_perfect'] else "⚠️"
        print(f"  {status_icon} {timing}ms: {result['analysis']}")
        if result['is_perfect']:
            perfect_timings.append(timing)
    
    if perfect_timings:
        print(f"\n🎯 Perfect timings found: {perfect_timings}")
    else:
        print(f"\n⚠️  No perfect timings found in tested range")
    
    # For automated testing
    assert len(perfect_timings) > 0, "No perfect timing values found in test range"


# Parametrized test for easy timing adjustment
@pytest.mark.parametrize("extend_time", [1380, 1385, 1390])
def test_parametrized_timing(tapper_service: TapperService, extend_time: int):
    """
    Parametrized test to easily test multiple timing values.
    Add/remove values from the parametrize decorator to test different timings.
    """
    print(f"\n🔬 Parametrized test with extend_time: {extend_time}ms")
    
    # Perform tap
    tapper_service.protocol.retract_for_time(1400)
    time.sleep(1.5)
    
    tapper_service.protocol.extend_for_time(extend_time)
    time.sleep(1.5)
    
    # Check result
    status = tapper_service.protocol.get_status()
    print(f"Result: {status}")
    
    # This test just reports results, doesn't fail
    if "middle" in status.lower():
        print("✅ Perfect timing!")
    else:
        print("⚠️  Drift detected - adjust timing")


def test_dual_sequences_approach(tapper_service: TapperService, tuning_config: dict):
    """Test using the new dual_sequences module."""
    
    print("\n🔄 Testing dual_sequences approach")
    
    # Test adaptive tap with custom timing
    print(f"🧠 Using adaptive tap with extend_time: {tuning_config['extend_time']}ms")
    final_status = dual_sequences.adaptive_tap_card2(
        tapper_service.protocol, 
        tuning_config['extend_time']
    )
    
    # Analyze result
    drift_analysis = dual_sequences._analyze_drift_direction(final_status)
    print(f"📊 Analysis: {drift_analysis}")
    
    # Assert success for automated testing
    assert "middle" in final_status.lower(), f"Dual sequences failed: {final_status}"


def test_calibration_sequence(tapper_service: TapperService):
    """Test the automated calibration sequence."""
    
    print("\n📏 Running calibration sequence...")
    
    # Run calibration to find optimal timing
    results = dual_sequences.calibration_sequence_timed(tapper_service.protocol)
    
    # Check if we found perfect timings
    perfect_timings = [timing for timing, result in results.items() if result['is_perfect']]
    
    if perfect_timings:
        print(f"🎯 Calibration successful! Recommended: {perfect_timings[0]}ms")
    else:
        print("⚠️  No perfect timing found in calibration range")
    
    # For automated testing - ensure calibration ran successfully
    assert len(results) > 0, "Calibration sequence failed to run"


def test_quick_tap_approach(tapper_service: TapperService):
    """Test the quick tap for fast iteration."""
    
    print("\n⚡ Testing quick tap approach")
    
    # Test multiple quick taps with different timings
    test_timings = [1380, 1385, 1390]
    
    for timing in test_timings:
        print(f"\n🔥 Quick tap with {timing}ms")
        
        before = tapper_service.protocol.get_status()
        
        dual_sequences.quick_tap_card2(tapper_service.protocol, timing)
        
        after = tapper_service.protocol.get_status()
        analysis = dual_sequences._analyze_drift_direction(after)
        
        print(f"   Before: {before}")
        print(f"   After:  {after}")
        print(f"   Result: {analysis}")
        
        time.sleep(0.3)  # Brief pause between quick taps


if __name__ == "__main__":
    # For running directly with python (not recommended, use pytest)
    pytest.main([__file__, "-v", "-s"])