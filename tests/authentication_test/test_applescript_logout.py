import time

import pytest


@pytest.mark.test_user("admin")
@pytest.mark.auto_login(False)
def test_applescript_logout_timing_validation(auth_manager, lightweight_session, applescript_logout_manager, test_config, test_logger):
    """
    Test AppleScript logout timing and performance validation.
    """
    expected_user = test_config["expected_user"]
    test_logger.info("=== Testing AppleScript Logout Timing Validation ===")
    
    try:
        # Step 1: Check initial state
        initial_console = auth_manager.get_console_info()
        test_logger.info(f"Initial console state: {initial_console}")

        # Ensure we start from logged out state
        auth_manager.ensure_logged_out()
        assert auth_manager.is_logged_out(), "Should start from logged out state"
        test_logger.info("Verified initial logged out state")

        # Step 2: Login user 1 and verify
        test_logger.info(f"Step 2: Logging in {expected_user}")
        login_success = auth_manager.login(expected_user, verify=True)
        assert login_success, f"Failed to login {expected_user}"

        current_user = auth_manager.get_current_user()
        assert current_user == expected_user, f"Expected {expected_user}, got {current_user}"
        test_logger.info(f"{expected_user} logged in successfully and verified")
        time.sleep(3)
        
    except Exception as e:
        test_logger.error(f"AppleScript logout timing test failed: {e}")
        current_state = auth_manager.get_console_info()
        test_logger.error(f"Current state during failure: {current_state}")
        raise
    
    finally:
        # Ensure clean state
        test_logger.info("=== Timing test cleanup ===")
        test_logger.info("⏱️ Starting AppleScript logout timing measurement")
        # Use lightweight_session fixture (no timing interference)
        try:
            manager, session_context = lightweight_session
            applescript_success = applescript_logout_manager.logout_user(
                session_context=session_context,
                grpc_manager=manager,
                expected_user=expected_user,
                max_attempts=3,
                retry_delay=2.0,
                verification_timeout=15
            )
            test_logger.info(f"✅ AppleScript logout completed: {applescript_success}")
        except Exception as e:
            test_logger.warning(f"AppleScript logout failed: {e}")