from typing import Any, Generator

import pytest
from tapper_system.tapper_service import TapperService, BaseProtocol
from tapper_system.tapper_service.commands import dual_tap_sequences


@pytest.fixture(scope="session")
def tapper_service() -> Generator[TapperService, Any, None]:
    service = TapperService("station1")
    if not service.connect():
        pytest.skip("No tapper hardware available - skipping integration tests")
    yield service
    service.disconnect()


@pytest.fixture(scope="function")
def tapper(tapper_service) -> Generator[TapperService, Any, None]:
    yield tapper_service


@pytest.fixture
def protocol(tapper) -> BaseProtocol:
    return tapper.protocol


@pytest.fixture(autouse=True)
def reset_hardware_state(protocol):
    try:
        status = protocol.get_status()
        if "middle" not in str(status).lower():
            dual_tap_sequences.reset_to_middle_timed(protocol, "unknown")
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to reset hardware state: {e}")


# Optional: simple logger fixtures for test output
@pytest.fixture
def test_logger(request):
    import logging
    logger = logging.getLogger(request.node.name)
    logger.setLevel(logging.INFO)
    yield logger


# Markers for pytest
def pytest_configure(config):
    config.addinivalue_line("markers", "hardware: marks tests that require real hardware")
    config.addinivalue_line("markers", "timing: marks tests that validate timing operations")
    config.addinivalue_line("markers", "protocol: marks tests that validate protocol behavior")
    config.addinivalue_line("markers", "slow: marks tests that take significant time to run")
    config.addinivalue_line("markers", "card1: marks tests specific to Card 1 operations")
    config.addinivalue_line("markers", "card2: marks tests specific to Card 2 operations")
    config.addinivalue_line("markers", "dual_card: marks tests that use both cards")