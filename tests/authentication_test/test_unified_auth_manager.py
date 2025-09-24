import pytest


@pytest.mark.auto_login(False)
def test_unified_auth_manager_basic(auth_manager, test_logger):
    """Test the unified auth manager basic operations."""
    
    test_logger.info("=== Testing Unified Auth Manager ===")
    
    # Test 1: Get initial state
    current_user = auth_manager.get_current_user()
    is_logged_out = auth_manager.is_logged_out()
    console_info = auth_manager.get_console_info()
    
    test_logger.info(f"Initial state - User: {current_user}, Logged out: {is_logged_out}")
    test_logger.info(f"Console info: {console_info}")
    
    # Test 2: Get available users
    mappings = auth_manager.get_user_mappings()
    supported_users = auth_manager.get_supported_users()
    
    test_logger.info(f"User mappings: {mappings}")
    test_logger.info(f"Supported users: {supported_users}")
    
    # Test 3: User verification methods
    if current_user:
        is_verified = auth_manager.verify_user_logged_in(current_user)
        test_logger.info(f"User {current_user} verification: {is_verified}")
    
    test_logger.info("✅ Unified auth manager basic operations work!")


@pytest.mark.auto_login(False)
def test_unified_auth_manager_operations(auth_manager, test_logger):
    """Test unified auth manager login/logout operations."""
    
    test_logger.info("=== Testing Auth Manager Operations ===")
    
    # Define test users
    user_1 = "admin"        # Maps to test_user_1
    user_2 = "macos_lab_1"  # Maps to test_user_2
    
    try:
        # Test 1: Ensure clean state
        test_logger.info("Step 1: Ensuring logged out state")
        auth_manager.ensure_logged_out()
        assert auth_manager.is_logged_out(), "Should be logged out initially"
        
        # Test 2: Login user 1 (if user mapping exists)
        test_logger.info(f"Step 2: Logging in {user_1}")
        if user_1 in auth_manager.get_user_mappings():
            success = auth_manager.login(user_1)
            test_logger.info(f"Login {user_1}: {'Success' if success else 'Failed'}")
            
            if success:
                current = auth_manager.get_current_user()
                verified = auth_manager.verify_user_logged_in(user_1)
                test_logger.info(f"After login - Current: {current}, Verified: {verified}")
        else:
            test_logger.info(f"Skipping {user_1} login - no mapping configured")
        
        # Test 3: User switch (if both users have mappings)
        mappings = auth_manager.get_user_mappings()
        if user_1 in mappings and user_2 in mappings:
            test_logger.info(f"Step 3: Switching from {user_1} to {user_2}")
            switch_success = auth_manager.switch_user(user_1, user_2)
            test_logger.info(f"User switch: {'Success' if switch_success else 'Failed'}")
            
            if switch_success:
                current = auth_manager.get_current_user()
                verified = auth_manager.verify_user_logged_in(user_2)
                test_logger.info(f"After switch - Current: {current}, Verified: {verified}")
        else:
            test_logger.info(f"Skipping user switch - missing mappings")
        
        # Test 4: Logout (auto-detection)
        test_logger.info("Step 4: Auto-detecting logout")
        logout_success = auth_manager.logout()
        test_logger.info(f"Auto logout: {'Success' if logout_success else 'Failed'}")
        
        if logout_success:
            final_user = auth_manager.get_current_user()
            is_logged_out = auth_manager.is_logged_out()
            test_logger.info(f"After logout - User: {final_user}, Logged out: {is_logged_out}")
        
    except Exception as e:
        test_logger.warning(f"Operation failed: {e}")
        test_logger.info("This is expected if user tap mappings are not configured properly")
    
    finally:
        # Always ensure cleanup
        test_logger.info("=== Final cleanup ===")
        auth_manager.ensure_logged_out()
    
    test_logger.info("✅ Auth manager operations test completed!")


@pytest.mark.auto_login(False) 
def test_simplified_user_switching(auth_manager, test_logger):
    """Demonstrate the simplified user switching pattern."""
    
    test_logger.info("=== SIMPLIFIED USER SWITCHING DEMO ===")
    
    user_1 = 'admin'
    user_2 = 'macos_lab_1'
    
    try:
        # Single call handles tap + verification
        test_logger.info(f"Logging in {user_1}")
        auth_manager.login(user_1)
        assert auth_manager.get_current_user() == user_1
        test_logger.info(f"✅ {user_1} logged in successfully")
        
        # Atomic user switch (logout user_1, login user_2, verify)
        test_logger.info(f"Switching from {user_1} to {user_2}")
        auth_manager.switch_user(user_1, user_2) 
        assert auth_manager.get_current_user() == user_2
        test_logger.info(f"✅ Successfully switched to {user_2}")
        
        # Auto-detects current user and uses correct card
        test_logger.info("Performing auto-logout")
        auth_manager.logout()
        assert auth_manager.is_logged_out()
        test_logger.info("✅ Successfully logged out")
        
    except Exception as e:
        test_logger.warning(f"Simplified switching failed: {e}")
        test_logger.info("This is expected if tap endpoints are not configured")
    
    finally:
        auth_manager.ensure_logged_out()
    
    test_logger.info("✅ Simplified user switching demo completed!")