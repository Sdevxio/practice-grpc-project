import time
from datetime import datetime
from typing import Optional, Callable, Dict

from tapper_system.tapper_service import TapperService
from tapper_system.tapper_service.commands import dual_tap_sequences
from test_framework.utils import get_logger


class LoginManager:
    # User to tap endpoint mapping - can be overridden at test level
    DEFAULT_USER_TAP_MAPPING = {
        "macos_lab_1": "tap_card2_endpoint",
        "macos_lab_2": "tap_card1_endpoint"
    }

    def __init__(self, station_id: str, logger=None, user_tap_mapping: Dict[str, str] = None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"tapper.{station_id}.login")
        self.last_tap_timestamp = None
        # Allow custom user-tap mapping to be passed in, otherwise use default
        self.user_tap_mapping = user_tap_mapping or self.DEFAULT_USER_TAP_MAPPING.copy()

    def set_user_tap_mapping(self, user: str, tap_endpoint: str):
        """Set tap endpoint for a specific user."""
        self.user_tap_mapping[user] = tap_endpoint
        self.logger.info(f"Set tap mapping: {user} -> {tap_endpoint}")

    def login_tap(self, user: str = None, max_attempts: int = 3, retry_delay: float = 1.0) -> bool:
        """Perform login tap for specific user"""
        return self._perform_tap("login", user, max_attempts, retry_delay)

    def logout_tap(self, user: str = None, max_attempts: int = 3, retry_delay: float = 2.0) -> bool:
        """Perform logout tap for specific user"""
        return self._perform_tap("logout", user, max_attempts, retry_delay)

    def force_tap(self, user: str = None, max_attempts: int = 3, retry_delay: float = 1.0) -> bool:
        """Force tap regardless of current login state for specific user"""
        return self._perform_tap("force_login", user, max_attempts, retry_delay)

    def _perform_tap(self, operation: str, user: str = None, max_attempts: int = 3, retry_delay: float = 1.0) -> bool:
        """Perform tap operation with retries for specific user."""
        user_info = f" for user '{user}'" if user else ""
        self.logger.info(f"Starting {operation} tap{user_info} (max attempts: {max_attempts})")

        for attempt in range(max_attempts):
            self.logger.info(f"{operation.title()} tap attempt {attempt + 1}/{max_attempts}{user_info}")

            if self._execute_single_tap(user):
                self.logger.info(f"{operation.title()} tap completed successfully{user_info}")
                return True
            else:
                self.logger.warning(f"{operation.title()} tap failed on attempt {attempt + 1}{user_info}")
                if attempt < max_attempts - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

        self.logger.error(f"All {max_attempts} {operation} tap attempts failed{user_info}")
        return False

    def _execute_single_tap(self, user: str = None) -> bool:
        """Execute single tap for both login/logout. Handles connection and errors."""
        try:
            tapper_service = TapperService(station_id=self.station_id)

            self.logger.debug(f"Attempting to connect to tapper service for station '{self.station_id}'...")
            if not tapper_service.connect():
                self.logger.error("Failed to connect to tapper service")
                return False

            try:
                self.last_tap_timestamp = datetime.now()
                tap_endpoint_name = self._get_tap_endpoint_for_user(user)
                self.logger.debug(f"Resolved tap endpoint for user '{user}': {tap_endpoint_name}")
                tap_function = self._get_tap_function(tap_endpoint_name)
                self.logger.debug(f"Resolved tap function for endpoint '{tap_endpoint_name}': {tap_function}")
                tap_function(tapper_service.protocol)
                user_info = f" for user '{user}'" if user else ""
                self.logger.debug(f"Tap executed successfully using {tap_endpoint_name}{user_info}")
                return True
            finally:
                self.logger.debug(f"Disconnecting tapper service for station '{self.station_id}'...")
                tapper_service.disconnect()

        except Exception as e:
            user_info = f" for user '{user}'" if user else ""
            self.logger.error(f"Tap execution failed{user_info}: {e}")
            return False

    def _get_tap_endpoint_for_user(self, user: str = None) -> str:
        """Get the appropriate tap endpoint for the given user."""
        if user and user in self.user_tap_mapping:
            tap_endpoint = self.user_tap_mapping[user]
            self.logger.debug(f"Using tap endpoint '{tap_endpoint}' for user '{user}'")
            return tap_endpoint
        else:
            # Default to tap_card2_endpoint for backward compatibility
            default_endpoint = "tap_card2_endpoint"
            if user:
                self.logger.warning(f"No tap mapping found for user '{user}', using default '{default_endpoint}'")
            else:
                self.logger.debug(f"No user specified, using default '{default_endpoint}'")
            return default_endpoint

    def _get_tap_function(self, tap_endpoint_name: str):
        """Get the tap function from dual_tap_sequences module."""
        try:
            tap_function = getattr(dual_tap_sequences, tap_endpoint_name)
            return tap_function
        except AttributeError:
            self.logger.error(f"Tap endpoint '{tap_endpoint_name}' not found in dual_tap_sequences")
            # Fallback to default
            return dual_tap_sequences.tap_card2_endpoint

    def get_supported_users(self) -> list:
        """Get list of users with configured tap mappings."""
        return list(self.user_tap_mapping.keys())

    def get_user_tap_mapping(self) -> Dict[str, str]:
        """Get current user to tap endpoint mapping."""
        return self.user_tap_mapping.copy()


class TappingManager:

    def __init__(self, station_id: str, enable_tapping: bool = True, logger=None,
                 user_tap_mapping: Dict[str, str] = None):
        self.station_id = station_id
        self.enable_tapping = enable_tapping
        self.logger = logger or get_logger(f"tapper.{station_id}.manager")
        self.tapper = LoginManager(station_id, logger, user_tap_mapping) if enable_tapping else None

    def perform_login_tap(self, user: str = None, verification_callback: Optional[Callable] = None) -> bool:
        """Perform login tap API for specific user."""
        if not self.enable_tapping:
            user_info = f" for user '{user}'" if user else ""
            self.logger.info(f"Tapping disabled - skipping login tap{user_info}")
            return True

        return self.tapper.login_tap(user=user)

    def perform_logoff_tap(self, expected_user: str, grpc_session_manager, **kwargs) -> bool:
        """Perform logout tap API for specific user."""
        if not self.enable_tapping:
            self.logger.info(f"Tapping disabled - skipping logout tap for user '{expected_user}'")
            return True

        # Perform tap for the specific user
        tap_success = self.tapper.logout_tap(user=expected_user)
        if not tap_success:
            return False

        # Verify logout
        return self._verify_logout(expected_user, grpc_session_manager, kwargs.get('verification_timeout', 15))

    def _verify_logout(self, expected_user: str, grpc_session_manager, timeout: int) -> bool:
        """Verify logout occurred by checking logged-in users."""
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                user_info = grpc_session_manager.get_logged_in_users()
                console_user = user_info.get("console_user", "")

                if console_user != expected_user:
                    self.logger.info(f"Logout verified - user changed from '{expected_user}' to '{console_user}'")
                    return True

                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Logout verification failed: {e}")
                return False

        self.logger.warning(f"Logout verification timed out - user may still be '{expected_user}'")
        return False

    def is_enabled(self) -> bool:
        """Check if tapping is enabled."""
        return self.enable_tapping

    def get_last_tap_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last successful tap."""
        return self.tapper.last_tap_timestamp if self.tapper else None

    def set_user_tap_mapping(self, user: str, tap_endpoint: str):
        """Set tap endpoint for a specific user."""
        if self.tapper:
            self.tapper.set_user_tap_mapping(user, tap_endpoint)

    def get_supported_users(self) -> list:
        """Get list of users with configured tap mappings."""
        return self.tapper.get_supported_users() if self.tapper else []