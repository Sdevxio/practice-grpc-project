"""
Hardware operation fixtures.

Provides tapping and physical interaction capabilities for tests.
"""

import pytest
from test_framework.login_logout.simple_tapper import SimpleTappingManager
from test_framework.utils import get_logger


@pytest.fixture(scope="function")
def hardware_controller(test_config, hardware_config, test_logger):
    """Hardware controller for physical interactions - simplified approach."""
    return SimpleTappingManager(
        station_id=test_config["station_id"],
        enable_tapping=hardware_config["enable_tapping"],
        logger=test_logger
    )