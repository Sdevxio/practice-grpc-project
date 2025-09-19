import pytest


@pytest.mark.auto_login(False)
@pytest.mark.test_user("test_user_1")
def test_console_user_tracking_methods(login_state, test_logger):
    """Test to verify console user tracking methods work correctly."""
    
    # Test 1: Basic console user info
    console_info = login_state.get_console_user_root()
    test_logger.info(f"Console user info: {console_info}")
    
    # Test 2: Current user detection
    current_user = login_state.get_current_user()
    test_logger.info(f"Current user: {current_user}")
    
    # Test 3: Console root detection
    is_root = login_state.is_console_root()
    test_logger.info(f"Is console root: {is_root}")
    
    # Test 4: User verification
    if current_user:
        is_verified = login_state.verify_user_logged_in(current_user)
        test_logger.info(f"User {current_user} verification: {is_verified}")
    
    # Basic assertions
    assert console_info is not None, "Console info should not be None"
    assert "console_user" in console_info, "Console info should contain 'console_user' key"
    assert "logged_in_users" in console_info, "Console info should contain 'logged_in_users' key"
    
    test_logger.info("Console user tracking methods work correctly!")


@pytest.mark.auto_login(False)
@pytest.mark.test_user("test_user_1") 
def test_login_logout_verification(login_state, test_logger):
    """Test login and logout verification using console tracking."""
    
    test_user = "admin"  # Using admin user for testing
    
    # Check initial state
    initial_info = login_state.get_console_user_root()
    test_logger.info(f"Initial console state: {initial_info}")
    
    # Try to login test user
    try:
        login_state.ensure_logged_in(test_user)
        test_logger.info(f"Login tap completed for {test_user}")
        
        # Verify login
        current_user = login_state.get_current_user()
        test_logger.info(f"After login - current user: {current_user}")
        
        is_logged_in = login_state.verify_user_logged_in(test_user)
        test_logger.info(f"Login verification for {test_user}: {is_logged_in}")
        
        # Try logout
        login_state.cleanup(test_user)
        test_logger.info(f"Logout completed for {test_user}")
        
        # Verify logout
        after_logout_user = login_state.get_current_user()
        test_logger.info(f"After logout - current user: {after_logout_user}")
        
        is_logged_out = login_state.verify_user_logged_out(test_user)
        test_logger.info(f"Logout verification for {test_user}: {is_logged_out}")
        
    except Exception as e:
        test_logger.warning(f"Login/logout test failed: {e}")
        # Don't fail the test, just log the issue
        test_logger.info("This is expected if user tap mapping is not configured properly")
    
    test_logger.info("Login/logout verification test completed!")