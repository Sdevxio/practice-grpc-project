import pytest
import time
from typing import Optional

from test_framework.login_state.login_manager import LoginManager
from test_framework.login_state.applescript_logout import AppleScriptLogoutManager
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger


@pytest.fixture
def auth_manager(test_config, request, console_user_tracker):
    """
    Unified authentication manager facade.
    
    Provides a clean, simple API while keeping underlying components separate.
    Composes login_state (tapping) + console_user_tracker (verification).
    
    Usage:
        def test_example(auth_manager):
            auth_manager.login("admin")
            auth_manager.switch_user("admin", "macos_lab_1") 
            auth_manager.logout()
    """
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.auth_manager")
    
    class AuthenticationManager:
        """
        Unified facade for authentication operations.
        
        Combines tapping operations with console verification for atomic operations.
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
            Login user with automatic verification.
            
            Args:
                user: Username to login
                verify: Whether to verify login via console (default: True)
                
            Returns:
                True if login successful (and verified if requested)
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
            Logout user with automatic verification.
            
            Args:
                user: Username to logout (None = auto-detect current user)
                verify: Whether to verify logout via console (default: True)
                
            Returns:
                True if logout successful (and verified if requested)
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
            Atomic user switch operation.
            
            Args:
                from_user: Current user to logout
                to_user: New user to login
                verify: Whether to verify operations via console
                
            Returns:
                True if switch successful
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
            """Get currently logged in user."""
            return self._console_tracker.get_current_user()
        
        def verify_user_logged_in(self, user: str) -> bool:
            """Verify specific user is logged in."""
            return self._console_tracker.verify_user_logged_in(user)
        
        def verify_user_logged_out(self, user: str) -> bool:
            """Verify specific user is logged out."""
            return self._console_tracker.verify_user_logged_out(user)
        
        def is_logged_out(self) -> bool:
            """Check if console is in logged out state (root)."""
            return self._console_tracker.is_console_root()
        
        def get_console_info(self) -> dict:
            """Get full console user information."""
            return self._console_tracker.get_console_user_info()
        
        def get_user_mappings(self) -> dict:
            """Get available user-to-card mappings."""
            return self._login_manager.get_user_tap_mapping()
        
        def get_supported_users(self) -> list:
            """Get list of users with configured tap mappings."""
            return self._login_manager.get_supported_users()
        
        # Private helper methods
        def _verify_login(self, user: str, max_retries: int = 3) -> bool:
            """Verify login was successful."""
            for attempt in range(max_retries):
                if self.verify_user_logged_in(user):
                    return True
                if attempt < max_retries - 1:
                    time.sleep(1.0)
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
    
    return AuthenticationManager()