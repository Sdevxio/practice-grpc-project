"""
Test configuration fixtures.

Provides clean, simple configuration loading for tests.
"""

import os
import pytest
from test_framework.utils.loaders.station_loader import StationLoader


@pytest.fixture(scope="function")
def test_config():
    """
    Single configuration fixture for all test needs.
    
    Provides essential test configuration with environment overrides.
    """
    station_id = os.environ.get("TEST_STATION", "station1")
    station_loader = StationLoader()

    station_config = station_loader.get_complete_station_config(station_id)
    test_users = station_loader.get_test_users()
    test_cards = station_loader.get_test_cards()
    e2e_defaults = station_loader.get_e2e_defaults()

    expected_user = (
        os.environ.get("TEST_USER") or
        test_users.get('test_user', {}).get('username') or
        "macos_lab_1"
    )

    expected_card = (
        os.environ.get("TEST_CARD") or
        (next(iter(test_cards.values())).get('card_id') if test_cards else None) or
        "AF17C52201"
    )

    return {
        "station_id": station_id,
        "expected_user": expected_user,
        "expected_card": expected_card,
        "login_timeout": e2e_defaults.get('login_timeout', 60),
        "station_config": station_config,
        "log_file_path": e2e_defaults.get("log_file_path", "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"),
        "test_users": test_users,
        "e2e_defaults": e2e_defaults,
    }


@pytest.fixture(scope="function")
def hardware_config():
    """Configuration for hardware operations."""
    config_map = {
        "enable_tapping": ("ENABLE_TAPPING", "true", lambda x: x.lower() == "true"),
        "login_max_attempts": ("LOGIN_TAP_ATTEMPTS", "3", int),
        "logoff_max_attempts": ("LOGOFF_TAP_ATTEMPTS", "3", int),
        "verification_timeout": ("TAP_VERIFICATION_TIMEOUT", "15", int),
        "retry_delay": ("TAP_RETRY_DELAY", "2.0", float),
    }

    return {
        key: converter(os.environ.get(env_var, default))
        for key, (env_var, default, converter) in config_map.items()
    }