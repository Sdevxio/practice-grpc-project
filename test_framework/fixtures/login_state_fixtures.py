import pytest
import time
from test_framework.login_state.login_manager import LoginManager
from test_framework.login_state.applescript_logout import AppleScriptLogoutManager
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger


@pytest.fixture
def login_state(test_config, request, console_user_tracker):
    """
    Login state fixtures with single responsibility: login/logout management.

    Usage:
    @pytest.mark.auto_manage(True)  # or False to disable auto-management
    """
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.login_state")

    # Get station and expected user from test config
    station_id = test_config.get("station_id", "station1")
    expected_user = test_config.get("expected_user")

    # Check for custom user-tap mappings in test config
    user_tap_mapping = test_config.get("user_tap_mapping")

    login_manager = LoginManager(station_id=station_id, logger=logger, user_tap_mapping=user_tap_mapping)

    # Check if auto-management is enabled
    marker = request.node.get_closest_marker("auto_login")
    if marker and marker.args:
        auto_manage = marker.args[0]
    else:
        auto_manage = True

    # Always fetch session_manager from request if available
    session_manager_value = None
    if "session_manager" in request.fixturenames:
        session_manager_value = request.getfixturevalue("session_manager")

    class LoginStateTester:
        def __init__(self):
            self.manager = login_manager
            self.logger = logger
            self.expected_user = expected_user
            self._last_login_time = None
            # Console user tracking
            self.console_tracker = console_user_tracker
            # Store session_manager/context if provided
            self._external_session_manager = None
            self._external_session_context = None
            if session_manager_value:
                if isinstance(session_manager_value, tuple) and len(session_manager_value) == 2:
                    self._external_session_manager, self._external_session_context = session_manager_value

        def ensure_logged_out(self, user: str = None):
            """Ensure logged out state."""
            target_user = user or self.expected_user
            self.logger.info(f"Ensuring logged-out state via logout tap for user: {target_user}")
            success = self.manager.logout_tap(user=target_user)
            if success:
                self.logger.info(f"Successfully logged out user: {target_user}")
                # Small delay to ensure logout is processed
                time.sleep(1.0)
            else:
                self.logger.warning(f"Logout tap may have failed for user: {target_user}, but continuing")
            return success

        def ensure_logged_in(self, user: str = None):
            """Ensure logged in state."""
            logger.info(f"{'=' * 30} LOGIN USERS {'=' * 30}")
            target_user = user or self.expected_user
            self.logger.info(f"Ensuring logged-in state via login tap for user: {target_user}")
            success = self.manager.login_tap(user=target_user)
            if success:
                self._last_login_time = self.manager.last_tap_timestamp
                self.logger.info(f"Successfully logged in user: {target_user} at {self._last_login_time}")
                # Small delay to ensure login is processed before session creation
                time.sleep(2.0)
            else:
                self.logger.error(f"Login tap failed for user: {target_user}")
                raise RuntimeError(f"Failed to perform login tap for user: {target_user}")
            return success

        def force_tap(self, user: str = None, max_attempts: int = 3, retry_delay: float = 1.0):
            """Force tap regardless of current login state."""
            target_user = user or self.expected_user
            self.logger.info(f"Performing force tap for user: {target_user}")
            success = self.manager.force_tap(user=target_user, max_attempts=max_attempts, retry_delay=retry_delay)
            if success:
                self._last_login_time = self.manager.last_tap_timestamp
                self.logger.info(f"Force tap successful for user: {target_user} at {self._last_login_time}")
                # Small delay to ensure tap is processed
                time.sleep(2.0)
            return success

        def get_last_tap_timestamp(self):
            """Get timestamp of last successful tap operation."""
            return self._last_login_time or self.manager.last_tap_timestamp

        def set_user_tap_mapping(self, user: str, tap_endpoint: str):
            """Set custom tap endpoint for a user."""
            """Set custom tap endpoint for a user."""
            self.manager.set_user_tap_mapping(user, tap_endpoint)
            self.logger.info(f"Updated tap mapping at test level: {user} -> {tap_endpoint}")

        def get_supported_users(self):
            """Get list of users with configured tap mappings."""
            return self.manager.get_supported_users()

        def get_user_tap_mapping(self):
            """Get current user to tap endpoint mapping."""
            return self.manager.get_user_tap_mapping()
        
        # Console user tracking methods
        def get_current_user(self):
            """Get currently logged in user from console."""
            return self.console_tracker.get_current_user()
        
        def get_console_user_root(self):
            """Get console user information (for compatibility with existing tests)."""
            return self.console_tracker.get_console_user_info()
        
        def verify_user_logged_in(self, expected_user: str) -> bool:
            """Verify specific user is logged in."""
            return self.console_tracker.verify_user_logged_in(expected_user)
        
        def verify_user_logged_out(self, expected_logged_out_user: str) -> bool:
            """Verify specific user is logged out."""
            return self.console_tracker.verify_user_logged_out(expected_logged_out_user)
        
        def is_console_root(self) -> bool:
            """Check if console user is 'root' (indicates logged out state)."""
            return self.console_tracker.is_console_root()

        def cleanup(self, user: str = None):
            """Enhanced cleanup with user verification and card mapping validation."""
            logger.info(f"{'=' * 30} LOGOUT USERS {'=' * 30}")
            
            # Determine target user for cleanup - prioritize current logged in user
            current_user = self.get_current_user()
            target_user = user or current_user or self.expected_user
            
            if not target_user:
                self.logger.warning("No user specified for cleanup and no user currently logged in")
                return True  # Nothing to cleanup
            
            self.logger.info(f"Cleaning up: performing logout for user: {target_user}")
            
            # Check if anyone is actually logged in
            if self.is_console_root():
                self.logger.info("Console is already root - no user to logout")
                return True
            
            # Verify target user is actually logged in
            if current_user and current_user != target_user:
                self.logger.info(f"Target user '{target_user}' not currently logged in. Current user: '{current_user}'")
                if user is None:  # If no specific user requested, logout whoever is logged in
                    target_user = current_user
                    self.logger.info(f"Switching cleanup target to current user: {current_user}")
                else:
                    self.logger.warning(f"Requested user '{user}' is not logged in, skipping cleanup")
                    return True
            
            # Validate user has tap endpoint mapping for reliable logout
            user_card_mapping = self.get_user_tap_mapping()
            if target_user not in user_card_mapping:
                self.logger.error(f"No card mapping found for user '{target_user}'. Cannot perform reliable logout.")
                self.logger.info(f"Available user mappings: {list(user_card_mapping.keys())}")
                return False
            
            tap_endpoint = user_card_mapping[target_user]
            self.logger.info(f"Using tap endpoint '{tap_endpoint}' for user '{target_user}' logout")

            # Using session_manager/context if available
            grpc_manager = None
            session_context = None
            if self._external_session_manager and self._external_session_context:
                grpc_manager = self._external_session_manager
                session_context = self._external_session_context
            else:
                # Fallback: create new session manager/context
                try:
                    grpc_manager = GrpcSessionManager(station_id=station_id, logger=logger)
                    session_timeout = test_config.get("session_timeout", 15)
                    session_context = grpc_manager.create_session(expected_user=target_user, timeout=session_timeout)
                except Exception as e:
                    self.logger.warning(f"Could not create session context for logout: {e}")
                    grpc_manager = None
                    session_context = None

            # Try AppleScript logout first (if session available)
            applescript_logout_manager = AppleScriptLogoutManager(logger=logger)
            applescript_success = False
            if grpc_manager and session_context:
                applescript_success = applescript_logout_manager.logout_user(
                    session_context=session_context,
                    grpc_manager=grpc_manager,
                    expected_user=target_user,
                    max_attempts=3,
                    retry_delay=2.0,
                    verification_timeout=15
                )
                if applescript_success:
                    self.logger.info(f"AppleScript logout successful for user: {target_user}")
                    # Verify logout was successful using console tracking
                    if self._verify_logout_success(target_user):
                        self.logger.info(f"Logout verification successful - console is now root")
                        return True
                    else:
                        self.logger.warning(f"AppleScript logout completed but verification failed")
                else:
                    self.logger.warning(f"AppleScript logout failed for user: {target_user}, falling back to tap logout")
            else:
                self.logger.warning(f"AppleScript logout not possible, falling back to tap logout for user: {target_user}")

            # Fallback to tap-based logout
            success = self.manager.logout_tap(user=target_user)
            if success:
                self.logger.info(f"Successfully logged out user via tap: {target_user}")
                time.sleep(2.0)  # Give time for logout to process
                
                # Verify logout was successful using console tracking
                if self._verify_logout_success(target_user):
                    self.logger.info(f"Tap logout verification successful - console is now root")
                    return True
                else:
                    self.logger.warning(f"Tap logout completed but user may still be logged in")
                    return False
            else:
                self.logger.warning(f"Tap logout failed for user: {target_user}")
                return False
        
        def _verify_logout_success(self, expected_logged_out_user: str, max_retries: int = 5) -> bool:
            """Verify logout was successful by checking console_user is 'root'."""
            for attempt in range(max_retries):
                try:
                    # Check if console is root (logout state)
                    if self.is_console_root():
                        self.logger.debug(f"Logout verification successful: console is root")
                        return True
                    
                    # Also check if current user changed
                    current_user = self.get_current_user()
                    if current_user != expected_logged_out_user:
                        self.logger.debug(f"Logout verification: user changed from {expected_logged_out_user} to {current_user}")
                        return True
                    
                    if attempt < max_retries - 1:
                        self.logger.debug(f"Logout verification attempt {attempt + 1}/{max_retries} failed, retrying...")
                        time.sleep(1.0)
                        
                except Exception as e:
                    self.logger.warning(f"Error during logout verification attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1.0)
            
            self.logger.warning(f"Logout verification failed after {max_retries} attempts")
            return False

    login_state = LoginStateTester()

    # Auto-manage initial login if enabled
    if auto_manage:
        login_state.ensure_logged_in()

    yield login_state

    # Auto cleanup if enabled
    if auto_manage:
        login_state.cleanup()