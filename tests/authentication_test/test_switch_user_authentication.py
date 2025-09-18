import pytest
import time

@pytest.mark.auto_login(False)
def test_card_tap_authentication_user_switch(login_state, test_config, test_logger):
    """Test to verify user switching via card taps."""
    user_2 = 'macos_lab_1'
    user_1 = 'macos_lab_2'

    # login user 1
    # login_state.ensure_logged_in(user_1)

    result = login_state.get_console_user_root()
    test_logger.info(f"Current console{result}")
    #
    # # Initialize session manager
    # manager, _ = session_manager
    # test_logger.info(f"Logged in as {user_1}")
    # session_context_1 = manager.create_session(
    #     expected_user=user_1,
    #     timeout=test_config.get("session_timeout", 15)
    # )
    # assert session_context_1.username == user_1, f"Session should be for {user_1}"
    # test_logger.info(f"Session established for user: {session_context_1.username}")
    #
    # # Switch to user 2
    # login_state.ensure_logged_in(user_2)
    # test_logger.info(f"Switched login to {user_2}")
    # # wait a moment to ensure session stability
    # time.sleep(2.0)
    # session_context_2 = manager.create_session(
    #     expected_user=user_2,
    #     timeout=test_config.get("session_timeout", 15)
    # )
    # assert session_context_2.username == user_2, f"Session should be for {user_2}"
    # test_logger.info(f"Session established for user: {session_context_2.username}")
    #
    # # Explicit cleanup at the end of the test
    # test_logger.info("Cleaning up: logging out the latest logged-in user.")
    # time.sleep(5.0)
    # login_state.cleanup(user_2)

@pytest.mark.auto_login(False)
def test_monitor_single(login_state, test_logger, test_config):
    """Test to verify single user authentication log entries."""


    result = login_state.get_console_user_root('admin')
    test_logger.info(f"Current console: {result}")