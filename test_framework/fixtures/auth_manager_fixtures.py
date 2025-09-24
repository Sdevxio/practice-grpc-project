import time
from typing import Optional

import pytest

from test_framework.login_state.login_manager import LoginManager
from test_framework.utils import get_logger


@pytest.fixture
def auth_manager(test_config, request, console_user_tracker):
    """
    Authentication manager fixture that provides login, logout, and user switching operations.
    This fixture combines card tap operations with console state verification to ensure reliable
    authentication testing. It manages the authentication lifecycle and provides verification
    of operations through console state checking.
    
    :return: AuthenticationManager instance with methods for authentication operations.
    """
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.auth_manager")
    
    # Check if auto-login is enabled (default: True unless @pytest.mark.auto_login(False))
    auto_login_marker = request.node.get_closest_marker("auto_login")
    auto_login_enabled = True  # Default to enabled
    if auto_login_marker and auto_login_marker.args:
        auto_login_enabled = auto_login_marker.args[0]
    
    class AuthenticationManager:
        """
        Authentication manager class for handling user login, logout, and switching operations.
        This class provides methods for authentication operations with optional console verification
        to ensure operations completed successfully. It combines LoginManager for card tapping
        with console user tracking for state verification.
        
        Attributes:
            logger (Logger): Logger instance for authentication operations.
            _login_manager (LoginManager): Handles card tap operations.
            _console_tracker: Tracks console user state for verification.
        """
        
        def __init__(self):
            self.logger = logger
            
            # Get station and expected user from test config
            station_id = test_config.get("station_id", "station1")
            expected_user = test_config.get("expected_user")
            user_tap_mapping = test_config.get("user_tap_mapping")
            
            # Create login manager directly
            self._login_manager = LoginManager(
                station_id=station_id, 
                logger=logger, 
                user_tap_mapping=user_tap_mapping
            )
            
            # Console tracking component
            self._console_tracker = console_user_tracker
        
        def login(self, user: str, verify: bool = True) -> bool:
            """
            Perform card tap login operation for specified user.
            This method executes a card tap login for the given user and optionally verifies
            the login was successful by checking console state.
            
            :param user: Username to login
            :param verify: Whether to verify login via console state check
            :return: True if login operation completed successfully
            """
            self.logger.info(f"Logging in user: {user}")
            
            # Check if user is already logged in
            if verify and self.get_current_user() == user:
                self.logger.info(f"User {user} already logged in")
                return True
            
            # Perform tap login
            success = self._login_manager.login_tap(user)
            
            if success and verify:
                # Verify login was successful
                if not self._verify_login(user):
                    self.logger.warning(f"Login tap succeeded but verification failed for: {user}")
                    return False
                    
            self.logger.info(f"Login {'successful' if success else 'failed'} for user: {user}")
            return success
        
        def logout(self, user: Optional[str] = None, verify: bool = True) -> bool:
            """
            Perform card tap logout operation for specified user.
            This method executes a card tap logout for the given user and optionally verifies
            the logout was successful by checking console state. If no user is specified,
            it will auto-detect the current user.
            
            :param user: Username to logout, if None will auto-detect current user
            :param verify: Whether to verify logout via console state check
            :return: True if logout operation completed successfully
            """
            # Auto-detect current user if not specified
            target_user = user or self.get_current_user()
            
            if not target_user:
                self.logger.info("No user to logout")
                return True
                
            self.logger.info(f"Logging out user: {target_user}")
            
            # Check if already logged out
            if verify and self.is_logged_out():
                self.logger.info("Already logged out")
                return True
            
            # Perform logout (simplified - just use logout tap)
            success = self._login_manager.logout_tap(target_user)
            
            if success and verify:
                # Verify logout was successful
                if not self._verify_logout(target_user):
                    self.logger.warning(f"Logout completed but verification failed for: {target_user}")
                    return False
                    
            self.logger.info(f"Logout {'successful' if success else 'failed'} for user: {target_user}")
            return success
        
        def switch_user(self, from_user: str, to_user: str, verify: bool = True) -> bool:
            """
            Switch from one user to another in a single atomic operation.
            This method performs user switching by logging in the target user, which automatically
            handles logout of the previous user. It optionally verifies both operations completed
            successfully through console state checking.
            
            :param from_user: Current user that should be logged out
            :param to_user: Target user to login
            :param verify: Whether to verify operations via console state checks
            :return: True if user switch completed successfully
            """
            self.logger.info(f"Switching user: {from_user} → {to_user}")
            
            # Verify from_user is actually logged in
            if verify and not self.verify_user_logged_in(from_user):
                self.logger.warning(f"Cannot switch: {from_user} is not logged in")
                return False
            
            # Perform the switch (login automatically handles logout of previous user)
            success = self.login(to_user, verify=verify)
            
            if success and verify:
                # Double-check the switch worked
                current = self.get_current_user()
                if current != to_user:
                    self.logger.error(f"Switch failed: expected {to_user}, got {current}")
                    return False
                    
            self.logger.info(f"User switch {'successful' if success else 'failed'}: {from_user} → {to_user}")
            return success
        
        # Delegation methods (clean API using existing components)
        def get_current_user(self) -> Optional[str]:
            """
            Get the username of the currently logged in console user.
            
            :return: Username of current console user, or None if logged out
            """
            return self._console_tracker.get_current_user()
        
        def verify_user_logged_in(self, user: str) -> bool:
            """
            Verify that specified user is currently logged into the console.
            
            :param user: Username to verify
            :return: True if user is logged in, False otherwise
            """
            return self._console_tracker.verify_user_logged_in(user)
        
        def verify_user_logged_out(self, user: str) -> bool:
            """
            Verify that specified user is not logged into the console.
            
            :param user: Username to verify
            :return: True if user is logged out, False otherwise
            """
            return self._console_tracker.verify_user_logged_out(user)
        
        def is_logged_out(self) -> bool:
            """
            Check if console is in logged out state with root user active.
            
            :return: True if console shows root user (logged out state)
            """
            return self._console_tracker.is_console_root()
        
        def get_console_info(self) -> dict:
            """
            Get complete console user state information.
            
            :return: Dictionary containing console user and logged in users
            """
            return self._console_tracker.get_console_user_info()
        
        def get_user_mappings(self) -> dict:
            """Get available user-to-card mappings."""
            return self._login_manager.get_user_tap_mapping()
        
        def get_supported_users(self) -> list:
            """Get list of users with configured tap mappings."""
            return self._login_manager.get_supported_users()
        
        # Private helper methods
        def _verify_login(self, user: str, max_retries: int = 5) -> bool:
            """Verify login was successful."""
            for attempt in range(max_retries):
                if self.verify_user_logged_in(user):
                    return True
                if attempt < max_retries - 1:
                    time.sleep(1.5)  # Increased delay for tapover scenarios
            return False
        
        def _verify_logout(self, user: str, max_retries: int = 3) -> bool:
            """Verify logout was successful."""
            for attempt in range(max_retries):
                if self.verify_user_logged_out(user) or self.is_logged_out():
                    return True
                if attempt < max_retries - 1:
                    time.sleep(1.0)
            return False
        
        # Advanced operations
        def force_login(self, user: str, verify: bool = True) -> bool:
            """Force login regardless of current state."""
            self.logger.info(f"Force logging in user: {user}")
            success = self._login_manager.force_tap(user)
            
            if success and verify:
                success = self._verify_login(user)
                
            return success
        
        def ensure_logged_out(self, verify: bool = True) -> bool:
            """Ensure system is in logged out state."""
            if self.is_logged_out():
                return True
                
            current_user = self.get_current_user()
            if current_user:
                return self.logout(current_user, verify=verify)
                
            return True
        
        def get_login_history(self) -> list:
            """Get login history for debugging (if available)."""
            # LoginManager doesn't track history, but we can return empty list
            # for backward compatibility
            return []
        
        def get_last_tap_timestamp(self):
            """
            Get timestamp of the last successful tap operation.
            
            :return: DateTime of last tap operation, or None if no taps performed
            """
            return self._login_manager.last_tap_timestamp
    
    # Create auth manager instance
    auth_mgr = AuthenticationManager()
    
    # Step 1: Check initial state and prepare for test
    logger.info("=== Auth Manager Setup ===")
    initial_state = auth_mgr.get_console_info()
    logger.info(f"Initial console state: {initial_state}")
    
    # Perform auto-login if enabled
    if auto_login_enabled:
        expected_user = test_config.get("expected_user")
        if expected_user:
            logger.info(f"Auto-login enabled: logging in {expected_user}")
            success = auth_mgr.login(expected_user, verify=True)
            if not success:
                logger.warning(f"Auto-login failed for user: {expected_user}")
            else:
                logger.info(f"✅ Auto-login successful for {expected_user}")
        else:
            logger.debug("Auto-login enabled but no expected_user configured")
    else:
        logger.info("Auto-login disabled - manual login required")
    
    # Yield the auth manager for test use
    try:
        yield auth_mgr
    finally:
        # Step 2: Always ensure cleanup
        logger.info("=== Auth Manager Cleanup ===")
        try:
            current_user = auth_mgr.get_current_user()
            if current_user:
                logger.info(f"Cleaning up: logging out current user '{current_user}'")
                cleanup_success = auth_mgr.ensure_logged_out(verify=True)
                if cleanup_success:
                    logger.info("✅ Cleanup successful - logged out")
                else:
                    logger.warning("⚠️ Cleanup incomplete - logout may have failed")
            else:
                logger.info("✅ No cleanup needed - already logged out")
                
            final_state = auth_mgr.get_console_info()
            logger.info(f"Final console state: {final_state}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        logger.info("=== Auth Manager Cleanup Complete ===")