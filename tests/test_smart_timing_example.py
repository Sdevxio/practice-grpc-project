"""
Example showing how the smart user state management works with timing tests.

This demonstrates the clean, simple approach where:
1. Auto cleanup happens before/after test (invisible)
2. Test controls user state flexibly during execution
3. No complexity - just works
"""

import datetime
import pytest


def test_timing_with_smart_state_management(user_state_control, monitoring_ready_workflow, test_logger):
    """
    Example: Timing test that needs gRPC session BEFORE login tap.
    
    Smart state management handles:
    - Clean start automatically
    - Flexible login during test
    - Clean end automatically
    """
    # 1. Test starts clean automatically (user logged out if needed)
    test_logger.info("Test starting - state automatically cleaned")
    
    # 2. Setup monitoring workflow (needs gRPC session first)
    workflow = monitoring_ready_workflow()
    
    # 3. Start logs monitoring before any user action
    logs_client = workflow["event_monitor_factory"]()
    test_logger.info("Log monitoring started")
    
    # 4. Record timing and perform controlled login
    tap_start_time = datetime.datetime.now()
    test_logger.info(f"Tap timing started: {tap_start_time}")
    
    # 5. Use smart state management for flexible login
    login_success = user_state_control.login_user()
    if login_success:
        test_logger.info("Smart login completed successfully")
    else:
        test_logger.info("Smart login skipped (tapping disabled)")
        
    # 6. Verify current user state
    current_user = user_state_control.get_current_user()
    test_logger.info(f"Current user after login: {current_user}")
    
    # 7. Test timing correlation would happen here
    # correlation_results = logs_client.stream_entries_for_tap_correlation(...)
    
    # 8. Test can logout user if needed during test
    if current_user:
        logout_success = user_state_control.logout_user(current_user)
        test_logger.info(f"Test-controlled logout: {logout_success}")
    
    test_logger.info("Test logic complete - auto cleanup will happen")
    # 9. Auto cleanup happens after test (guaranteed clean end)


def test_simple_login_logout_control(user_state_control, test_logger):
    """
    Example: Simple test showing flexible user state control.
    """
    test_logger.info("Test demonstrating flexible user control")
    
    # Check initial state
    initial_user = user_state_control.get_current_user()
    test_logger.info(f"Initial user: {initial_user}")
    
    # Test can request login
    if not initial_user:
        user_state_control.login_user()
        after_login = user_state_control.get_current_user()
        test_logger.info(f"After login request: {after_login}")
    
    # Test can request logout
    current_user = user_state_control.get_current_user()
    if current_user:
        user_state_control.logout_user(current_user)
        after_logout = user_state_control.get_current_user()
        test_logger.info(f"After logout request: {after_logout}")
    
    # Auto cleanup ensures clean end regardless


def test_no_state_control_needed(test_logger):
    """
    Example: Test that doesn't need user state control.
    
    Even tests that don't use user_state_control still get:
    - Auto clean start
    - Auto clean end
    """
    test_logger.info("This test doesn't control user state")
    test_logger.info("But it still gets automatic cleanup")
    
    # Test logic here - no user state management needed
    # Auto cleanup still happens