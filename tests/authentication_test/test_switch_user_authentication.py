import pytest
import time

@pytest.mark.auto_login(False)
def test_card_tap_authentication_user_switch(auth_manager, test_config, test_logger):
    """Test to verify user switching via card taps using tapover functionality.
    
    This test verifies:
    1. Login user 1 and verify authentication
    2. Login user 2 directly (tapover) without explicit logout of user 1
    3. Verify user 2 is now authenticated and user 1 is automatically logged out
    """
    user_1 = 'admin'           # Maps to test_user_1 
    user_2 = 'macos_lab_1'     # Maps to test_user_2
    
    test_logger.info("=== Testing Card Tap Authentication User Switch (Tapover) ===")
    
    try:
        # Step 1: Check initial state
        initial_console = auth_manager.get_console_info()
        test_logger.info(f"Initial console state: {initial_console}")
        
        # Ensure we start from logged out state
        auth_manager.ensure_logged_out()
        assert auth_manager.is_logged_out(), "Should start from logged out state"
        test_logger.info("✅ Verified initial logged out state")
        
        # Step 2: Login user 1 and verify
        test_logger.info(f"Step 2: Logging in {user_1}")
        login_success = auth_manager.login(user_1, verify=True)
        assert login_success, f"Failed to login {user_1}"
        
        current_user = auth_manager.get_current_user()
        assert current_user == user_1, f"Expected {user_1}, got {current_user}"
        test_logger.info(f"✅ {user_1} logged in successfully and verified")
        
        # Step 3: Wait a moment for authentication stability
        time.sleep(2.0)
        
        # Step 4: Login user 2 directly (tapover functionality)
        test_logger.info(f"Step 4: Testing tapover - logging in {user_2} directly")
        tapover_success = auth_manager.login(user_2, verify=True)
        assert tapover_success, f"Failed to login {user_2} via tapover"
        
        # Verify user 2 is now logged in and user 1 is automatically logged out
        current_user_after_tapover = auth_manager.get_current_user()
        assert current_user_after_tapover == user_2, f"Expected {user_2}, got {current_user_after_tapover}"
        test_logger.info(f"✅ Tapover successful: {user_2} is now logged in")
        
        # Verify user 1 is no longer logged in
        user_1_logged_out = auth_manager.verify_user_logged_out(user_1)
        assert user_1_logged_out, f"User {user_1} should be logged out after tapover"
        test_logger.info(f"✅ Verified {user_1} was automatically logged out during tapover")
        
        # Step 5: Verify final console state
        final_console = auth_manager.get_console_info()
        test_logger.info(f"Final console state: {final_console}")
        
        test_logger.info("✅ Tapover functionality test completed successfully!")
        
    except Exception as e:
        test_logger.error(f"Test failed: {e}")
        # Log current state for debugging
        current_state = auth_manager.get_console_info()
        test_logger.error(f"Current state during failure: {current_state}")
        raise
        
    finally:
        # Always ensure cleanup
        test_logger.info("=== Final cleanup ===")
        auth_manager.ensure_logged_out()
        test_logger.info("Cleanup completed")

@pytest.mark.auto_login(False)
def test_monitor_single_user_login(auth_manager, test_logger, test_config):
    """Test to verify single user authentication and console state monitoring."""
    test_user = 'admin'  # Maps to test_user_1
    
    test_logger.info("=== Testing Single User Login Monitoring ===")
    
    try:
        # Step 1: Check initial state
        console_info = auth_manager.get_console_info()
        test_logger.info(f"Initial console state: {console_info}")
        
        # Ensure logged out state
        auth_manager.ensure_logged_out()
        assert auth_manager.is_logged_out(), "Should start from logged out state"
        test_logger.info("✅ Verified initial logged out state")
        
        # Step 2: Login single user
        test_logger.info(f"Step 2: Logging in {test_user}")
        login_success = auth_manager.login(test_user, verify=True)
        assert login_success, f"Failed to login {test_user}"
        
        # Step 3: Verify authentication state
        current_user = auth_manager.get_current_user()
        assert current_user == test_user, f"Expected {test_user}, got {current_user}"
        test_logger.info(f"✅ {test_user} logged in and verified")
        
        # Step 4: Test console monitoring methods
        is_logged_out = auth_manager.is_logged_out()
        assert not is_logged_out, "Should not be in logged out state"
        test_logger.info("✅ Console state correctly shows user logged in")
        
        user_verified = auth_manager.verify_user_logged_in(test_user)
        assert user_verified, f"User {test_user} should be verified as logged in"
        test_logger.info(f"✅ User verification confirmed {test_user} is logged in")
        
        # Step 5: Check user mappings and supported users
        user_mappings = auth_manager.get_user_mappings()
        supported_users = auth_manager.get_supported_users()
        test_logger.info(f"Available user mappings: {user_mappings}")
        test_logger.info(f"Supported users: {supported_users}")
        
        assert test_user in user_mappings or test_user in supported_users, f"{test_user} should be in supported users"
        test_logger.info("✅ User configuration verified")
        
        # Step 6: Test logout
        test_logger.info(f"Step 6: Logging out {test_user}")
        logout_success = auth_manager.logout(test_user, verify=True)
        assert logout_success, f"Failed to logout {test_user}"
        
        # Verify logged out state
        assert auth_manager.is_logged_out(), "Should be in logged out state after logout"
        test_logger.info(f"✅ {test_user} logged out successfully")
        
        test_logger.info("✅ Single user login monitoring test completed successfully!")
        
    except Exception as e:
        test_logger.error(f"Test failed: {e}")
        # Log current state for debugging
        current_state = auth_manager.get_console_info()
        test_logger.error(f"Current state during failure: {current_state}")
        raise
        
    finally:
        # Always ensure cleanup
        test_logger.info("=== Final cleanup ===")
        auth_manager.ensure_logged_out()
        test_logger.info("Cleanup completed")
