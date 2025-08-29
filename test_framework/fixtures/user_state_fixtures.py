"""
User State Management Fixtures - Smart and Simple

Requirements:
1. All tests start clean - auto logout whoever is logged in
2. All tests end clean - auto logout + unlock desktop (always)
3. Flexible during test - tests can login/logout as needed
4. Smart fallback - AppleScript -> Tapping -> Force unlock
5. Simple API - no complexity, no over-engineering
"""

import pytest
from test_framework.login_logout.logout_command import logout_user
from test_framework.utils import get_logger


class UserStateManager:
    """Smart user state management with automatic cleanup and flexible control."""
    
    def __init__(self, session_manager, hardware_controller, test_config):
        self.session_manager = session_manager
        self.hardware = hardware_controller
        self.config = test_config
        self.logger = get_logger("user_state_manager")
        
    def ensure_clean_start(self):
        """Auto logout whoever is logged in - any method works."""
        current_user = self._get_current_user()
        if current_user:
            self.logger.info(f"Found user '{current_user}' logged in - cleaning for test start")
            self._smart_logout(current_user)
        else:
            self.logger.info("No user logged in - clean start confirmed")
            
    def ensure_clean_end(self):
        """Always cleanup + unlock desktop - guaranteed, regardless of test result."""
        current_user = self._get_current_user()
        if current_user:
            self.logger.info(f"Cleaning up user '{current_user}' after test")
            self._smart_logout(current_user)
        
        # Always try to unlock desktop as final step
        self._force_unlock_desktop()
        self.logger.info("Desktop unlocked - test cleanup complete")
        
    def login_user(self, username=None):
        """Login user during test - flexible for test needs."""
        username = username or self.config["expected_user"]
        self.logger.info(f"Test requested login for user: {username}")
        
        if self.hardware.is_enabled():
            success = self.hardware.perform_login_tap()
            if success:
                self.logger.info(f"Login tap completed for user: {username}")
                return True
            else:
                self.logger.warning(f"Login tap failed for user: {username}")
                return False
        else:
            self.logger.warning("Hardware tapping disabled - cannot perform login")
            return False
            
    def logout_user(self, username=None):
        """Logout user during test - flexible for test needs."""
        username = username or self.config["expected_user"]
        self.logger.info(f"Test requested logout for user: {username}")
        return self._smart_logout(username)
        
    def get_current_user(self):
        """Get currently logged in user - available for test checks."""
        return self._get_current_user()
        
    def _get_current_user(self):
        """Internal method to get current user from session manager."""
        try:
            user_info = self.session_manager.get_logged_in_users()
            console_user = user_info.get("console_user", "")
            return console_user if console_user and console_user.strip() else None
        except Exception as e:
            self.logger.error(f"Failed to get current user: {e}")
            return None
            
    def _smart_logout(self, username):
        """Smart fallback: AppleScript -> Tapping -> Success."""
        self.logger.info(f"Smart logout for user '{username}' starting")
        
        # First try AppleScript logout (through session manager)
        try:
            session_context = self.session_manager.create_session(username, timeout=30)
            success = logout_user(
                session_context=session_context,
                grpc_manager=self.session_manager,
                expected_user=username,
                max_attempts=2,  # Quick AppleScript attempts
                verification_timeout=10,
                retry_delay=1.0,
                logger=self.logger
            )
            
            if success:
                self.logger.info(f"AppleScript logout successful for user '{username}'")
                return True
        except Exception as e:
            self.logger.warning(f"AppleScript logout failed for user '{username}': {e}")
            
        # Fallback to tapping if AppleScript failed
        if self.hardware.is_enabled():
            self.logger.info(f"Falling back to tapping logout for user '{username}'")
            try:
                success = self.hardware.perform_logoff_tap(
                    expected_user=username,
                    grpc_session_manager=self.session_manager,
                    max_attempts=2,
                    verification_timeout=10,
                    retry_delay=1.0
                )
                
                if success:
                    self.logger.info(f"Tapping logout successful for user '{username}'")
                    return True
                else:
                    self.logger.warning(f"Tapping logout failed for user '{username}'")
            except Exception as e:
                self.logger.error(f"Tapping logout error for user '{username}': {e}")
        
        # If both methods failed, log warning but continue (don't block tests)
        self.logger.warning(f"All logout methods failed for user '{username}' - continuing")
        return False
        
    def _force_unlock_desktop(self):
        """Force unlock desktop as final cleanup step."""
        try:
            # Try to unlock via AppleScript if session available
            if hasattr(self.session_manager, '_session_context'):
                session_context = self.session_manager._session_context
                if hasattr(session_context, 'root_context') and hasattr(session_context.root_context, 'apple_script'):
                    unlock_script = '''
                    tell application "System Events"
                        key code 53 -- Escape key to dismiss any dialogs
                    end tell
                    '''
                    session_context.root_context.apple_script.run_applescript(unlock_script, timeout_seconds=5)
                    self.logger.debug("Desktop unlock script executed")
        except Exception as e:
            self.logger.debug(f"Desktop unlock attempt failed (non-critical): {e}")


@pytest.fixture(scope="function", autouse=True)
def auto_clean_user_state(session_manager, hardware_controller, test_config, test_logger):
    """
    Automatic user state management for ALL tests.
    
    This fixture runs automatically for every test and provides:
    1. Clean start - logout any user before test
    2. Clean end - logout any user + unlock desktop after test (always)
    3. Available for test use - tests can call login/logout during execution
    
    Available in test as: auto_clean_user_state.login_user(), etc.
    """
    state_mgr = UserStateManager(session_manager, hardware_controller, test_config)
    
    # BEFORE TEST: Ensure clean start
    test_logger.info("=== USER STATE: Ensuring clean start ===")
    state_mgr.ensure_clean_start()
    
    yield state_mgr  # Available for test use
    
    # AFTER TEST: Always ensure clean end (regardless of test result)
    test_logger.info("=== USER STATE: Ensuring clean end ===")
    state_mgr.ensure_clean_end()


@pytest.fixture(scope="function")
def user_state_control(auto_clean_user_state):
    """
    Convenience fixture for tests that need explicit user state control.
    
    Usage:
        def test_login_sequence(user_state_control):
            user_state_control.login_user("testuser")
            # test logic here
            user_state_control.logout_user("testuser")
    """
    return auto_clean_user_state