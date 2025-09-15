"""
Integration test configuration for tapper service.

This module provides shared fixtures and configuration for integration tests
that interact with real tapper hardware devices.
"""

import pytest
import sys
from typing import Generator, Optional

# Add project root to path
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system import TapperService
from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol


@pytest.fixture(scope="session")
def tapper_service() -> Generator[TapperService, None, None]:
    """
    Session-scoped tapper service fixture.
    
    Creates a single tapper service instance for the entire test session
    to minimize hardware connection overhead.
    """
    service = TapperService("station1")
    
    if service.connect():
        yield service
        service.disconnect()
    else:
        pytest.skip("No tapper hardware available - skipping integration tests")


@pytest.fixture(scope="function") 
def tapper() -> Generator[TapperService, None, None]:
    """
    Function-scoped tapper service fixture.
    
    Creates a fresh tapper service connection for each test function.
    Use this when tests need isolated connections.
    """
    service = TapperService("station1")
    
    if service.connect():
        yield service
        service.disconnect()
    else:
        pytest.skip("No tapper hardware available - skipping test")


@pytest.fixture
def protocol(tapper: TapperService) -> BaseProtocol:
    """
    Protocol fixture that provides direct access to the tapper protocol.
    
    :param tapper: Tapper service fixture
    :return: Active protocol instance
    """
    return tapper.protocol


@pytest.fixture
def skip_if_no_hardware():
    """
    Fixture to skip tests if no hardware is available.
    
    This is a more explicit way to handle hardware dependencies.
    """
    service = TapperService("station1")
    try:
        if not service.connect():
            pytest.skip("No tapper hardware available")
        service.disconnect()
    except Exception:
        pytest.skip("Failed to connect to tapper hardware")


@pytest.fixture(autouse=True)
def reset_hardware_state(tapper: TapperService):
    """
    Auto-use fixture to reset hardware state before each test.
    
    Ensures each test starts with the tapper in a known state (middle position).
    """
    if tapper.protocol:
        try:
            # Get current status
            status = tapper.protocol.get_status()
            
            # If not already at middle, reset to middle
            if "middle" not in status.lower():
                from tappers_service.tapper_system.command import dual_sequences
                dual_sequences.reset_to_middle_timed(tapper.protocol, "unknown")
                
        except Exception as e:
            # Don't fail the test if reset fails, just warn
            pytest.warns(UserWarning, f"Failed to reset hardware state: {e}")


# Test markers for different categories
def pytest_configure(config):
    """Configure custom markers for integration tests."""
    config.addinivalue_line("markers", "hardware: marks tests that require real hardware")
    config.addinivalue_line("markers", "timing: marks tests that validate timing operations")
    config.addinivalue_line("markers", "protocol: marks tests that validate protocol behavior") 
    config.addinivalue_line("markers", "slow: marks tests that take significant time to run")
    config.addinivalue_line("markers", "card1: marks tests specific to Card 1 operations")
    config.addinivalue_line("markers", "card2: marks tests specific to Card 2 operations")
    config.addinivalue_line("markers", "dual_card: marks tests that use both cards")


# Test collection and reporting
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add hardware marker to all integration tests
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.hardware)


def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Skip hardware tests if --skip-hardware flag is passed
    if hasattr(item, "get_closest_marker"):
        hardware_marker = item.get_closest_marker("hardware")
        if hardware_marker and item.config.getoption("--skip-hardware", default=False):
            pytest.skip("Hardware tests skipped by --skip-hardware flag")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--skip-hardware",
        action="store_true", 
        default=False,
        help="Skip tests that require hardware"
    )
    parser.addoption(
        "--station", 
        action="store",
        default="station1",
        help="Station ID to use for testing"
    )


@pytest.fixture
def station_id(request):
    """Fixture to get station ID from command line or use default."""
    return request.config.getoption("--station")