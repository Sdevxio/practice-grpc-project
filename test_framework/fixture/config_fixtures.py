import os

import pytest

from test_framework.utils.consts.constants import IMPRIVATA_LOG_PATH
from test_framework.utils.loaders.station_loader import StationLoader


@pytest.fixture(scope="function")
def test_config(request):
    """Configuration for tests, including station ID, expected user/card, timeouts, and station settings.
    Reads from environment variables or defaults from station configuration.

    Supported markers:
    - @pytest.mark.test_user("macos_lab_2") or @pytest.mark.test_user("test_user2")
    - @pytest.mark.station("station3")
    - @pytest.mark.session_timeout(30)
    - @pytest.mark.test_card("0987654321")
    - @pytest.mark.hardware_config(enable_tapping=False, login_max_attempts=5)
    """
    station_loader = StationLoader()

    # Get station ID with marker support: marker > env > default
    station_id = _get_station_id(request)

    # Get base configuration from files
    station_config = station_loader.get_complete_station_config(station_id)
    test_users = station_loader.get_test_users()
    test_cards = station_loader.get_test_cards()
    e2e_defaults = station_loader.get_e2e_defaults()

    # Simple user resolution: marker > env > config default
    expected_user = _get_expected_user(request, test_users, e2e_defaults)

    # Get the resolved user details
    expected_user_details = _get_user_details_by_username(test_users, expected_user)

    # Simple card resolution: marker > env > user's default card > config default
    expected_card = _get_expected_card(request, test_users, test_cards, expected_user, e2e_defaults)

    # Build user-tap mapping directly from config
    user_tap_mapping = _get_user_tap_mapping(test_users)

    # Simple timeout resolution
    session_timeout = _get_session_timeout(request, station_config, e2e_defaults)

    # Simple hardware config
    hardware_config = _get_hardware_config(request, e2e_defaults)

    return {
        "station_id": station_id,
        "expected_user": expected_user,
        "expected_user_details": expected_user_details,
        "expected_card": expected_card,
        "session_timeout": session_timeout,
        "station_config": station_config,
        "log_file_path": IMPRIVATA_LOG_PATH,
        "test_users": test_users,
        "test_cards": test_cards,
        "e2e_defaults": e2e_defaults,
        "user_tap_mapping": user_tap_mapping,
        "hardware_config": hardware_config,
    }


def _get_station_id(request):
    # 1. Test marker override
    station_marker = request.node.get_closest_marker("station")
    if station_marker and station_marker.args:
        return station_marker.args[0]

    # 2. Environment variable override
    env_station = os.environ.get("TEST_STATION")
    if env_station:
        return env_station

    # 3. Default
    return "station1"


def _get_expected_user(request, test_users, e2e_defaults):
    # 1. Test marker override
    user_marker = request.node.get_closest_marker("test_user")
    if user_marker and user_marker.args:
        user_key = user_marker.args[0]
        # If it's a config key, resolve it
        if user_key in test_users:
            return test_users[user_key]["username"]
        # Otherwise it's a direct username
        return user_key

    # 2. Environment variable override
    env_user = os.environ.get("TEST_USER")
    if env_user:
        return env_user

    # 3. Use configured default user
    default_user_key = e2e_defaults.get("default_user")
    if default_user_key and default_user_key in test_users:
        return test_users[default_user_key]["username"]

    # 4. Raise error if config is incomplete
    raise ValueError(
        f"No user configured. Please set 'default_user' in e2e_test_defaults or use TEST_USER env var. "
        f"Available users: {list(test_users.keys())}"
    )


def _get_expected_card(request, test_users, test_cards, expected_user, e2e_defaults):
    # 1. Test marker override
    card_marker = request.node.get_closest_marker("test_card")
    if card_marker and card_marker.args:
        return card_marker.args[0]

    # 2. Environment variable override
    env_card = os.environ.get("TEST_CARD")
    if env_card:
        return env_card

    # 3. User's default card from config
    for user_info in test_users.values():
        if user_info["username"] == expected_user:
            default_card = user_info.get("default_card")
            if default_card:
                return default_card
            break

    # 4. User-card mapping from e2e_defaults
    user_card_mapping = e2e_defaults.get("user_card_mapping", {})
    if expected_user in user_card_mapping:
        return user_card_mapping[expected_user]

    # 5. Raise error if config is incomplete
    if not test_cards:
        raise ValueError("No cards configured in test_cards")

    # Return first available card
    first_card = next(iter(test_cards.values()))
    return first_card["card_id"]


def _get_user_tap_mapping(test_users):
    mapping = {}

    for user_info in test_users.values():
        username = user_info["username"]
        tap_endpoint = user_info.get("tap_endpoint")

        if not tap_endpoint:
            raise ValueError(
                f"User '{username}' missing tap_endpoint configuration. "
                f"Please add 'tap_endpoint' field to user config."
            )

        mapping[username] = tap_endpoint

    return mapping


def _get_session_timeout(request, station_config, e2e_defaults):
    # Test marker override
    timeout_marker = request.node.get_closest_marker("session_timeout")
    if timeout_marker and timeout_marker.args:
        return int(timeout_marker.args[0])

    # Environment variable override
    env_timeout = os.environ.get("SESSION_TIMEOUT")
    if env_timeout:
        return int(env_timeout)

    # Station-specific timeout
    if hasattr(station_config, 'overrides') and station_config.overrides:
        station_timeout = station_config.overrides.get("timeouts", {}).get("session_timeout")
        if station_timeout:
            return station_timeout

    # Global default from config
    return e2e_defaults.get("session_timeout", 60)


def _get_hardware_config(request, e2e_defaults):
    config = e2e_defaults.get("hardware_defaults", {})

    # Environment variable overrides
    if "ENABLE_TAPPING" in os.environ:
        config["enable_tapping"] = os.environ["ENABLE_TAPPING"].lower() == "true"
    if "LOGIN_TAP_ATTEMPTS" in os.environ:
        config["login_max_attempts"] = int(os.environ["LOGIN_TAP_ATTEMPTS"])
    if "LOGOFF_TAP_ATTEMPTS" in os.environ:
        config["logoff_max_attempts"] = int(os.environ["LOGOFF_TAP_ATTEMPTS"])
    if "TAP_VERIFICATION_TIMEOUT" in os.environ:
        config["verification_timeout"] = int(os.environ["TAP_VERIFICATION_TIMEOUT"])
    if "TAP_RETRY_DELAY" in os.environ:
        config["retry_delay"] = float(os.environ["TAP_RETRY_DELAY"])

    # Test marker overrides
    hardware_marker = request.node.get_closest_marker("hardware_config")
    if hardware_marker and hardware_marker.kwargs:
        config.update(hardware_marker.kwargs)

    return config


def _get_user_details_by_username(test_users, username):
    for user_key, user_info in test_users.items():
        if user_info.get("username") == username:
            return user_info
    return {}