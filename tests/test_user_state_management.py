"""
Test the smart user state management system.
"""

import pytest


def test_auto_clean_state_available(auto_clean_user_state, test_logger):
    """Test that auto clean state fixture is available and working."""
    assert auto_clean_user_state is not None
    assert hasattr(auto_clean_user_state, 'login_user')
    assert hasattr(auto_clean_user_state, 'logout_user')
    assert hasattr(auto_clean_user_state, 'get_current_user')
    test_logger.info("Auto clean user state fixture working")


def test_user_state_control_fixture(user_state_control, test_logger):
    """Test the convenience user state control fixture."""
    assert user_state_control is not None
    current_user = user_state_control.get_current_user()
    test_logger.info(f"Current user from state control: {current_user}")


def test_flexible_login_logout(user_state_control, test_logger):
    """Test flexible login/logout during test execution."""
    # Test can control login/logout as needed
    current_user_before = user_state_control.get_current_user()
    test_logger.info(f"User before test operations: {current_user_before}")
    
    # Simulate test that needs to control login state
    # (This would normally involve actual hardware operations)
    if user_state_control.hardware.is_enabled():
        test_logger.info("Hardware tapping is enabled - could perform operations")
    else:
        test_logger.info("Hardware tapping is disabled - operations would be skipped")
    
    current_user_after = user_state_control.get_current_user()
    test_logger.info(f"User after test operations: {current_user_after}")
    
    # Note: Cleanup happens automatically via auto_clean_user_state fixture


def test_smart_state_management_integration(session_manager, hardware_controller, test_config, test_logger):
    """Test that state management integrates properly with existing components."""
    from test_framework.fixtures.user_state_fixtures import UserStateManager
    
    state_mgr = UserStateManager(session_manager, hardware_controller, test_config)
    
    # Test basic functionality
    current_user = state_mgr.get_current_user()
    test_logger.info(f"Current user via direct state manager: {current_user}")
    
    # Test that it can coordinate with session manager and hardware
    assert state_mgr.session_manager == session_manager
    assert state_mgr.hardware == hardware_controller
    assert state_mgr.config == test_config
    
    test_logger.info("Smart state management integration working")