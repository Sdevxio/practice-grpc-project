"""
Simplified Tapping - One class, clear purpose, no duplication.

Replaces: TappingManager + LoginTapper + LogoutTapper (3 classes)
With: SimpleTapper (1 class)
"""

import time
from typing import Optional, Callable
from tappers_service.controller.tapper_service import TapperService
from tappers_service.command import sequences
from test_framework.utils import get_logger


class SimpleTapper:
    """
    Simple, unified tapper for login/logout operations.
    
    No duplication, clear purpose, easy to use.
    """
    
    def __init__(self, station_id: str, logger=None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"simple_tapper_{station_id}")
        
    def login_tap(self, max_attempts: int = 3, retry_delay: float = 1.0) -> bool:
        """Perform login tap - simple and clean."""
        return self._perform_tap("login", max_attempts, retry_delay)
        
    def logout_tap(self, max_attempts: int = 3, retry_delay: float = 2.0) -> bool:
        """Perform logout tap - simple and clean."""
        return self._perform_tap("logout", max_attempts, retry_delay)
        
    def _perform_tap(self, operation: str, max_attempts: int, retry_delay: float) -> bool:
        """Unified tap execution - no duplication."""
        self.logger.info(f"Starting {operation} tap (max attempts: {max_attempts})")
        
        for attempt in range(max_attempts):
            self.logger.info(f"{operation.title()} tap attempt {attempt + 1}/{max_attempts}")
            
            if self._execute_single_tap():
                self.logger.info(f"{operation.title()} tap completed successfully")
                return True
            else:
                self.logger.warning(f"{operation.title()} tap failed on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        self.logger.error(f"All {max_attempts} {operation} tap attempts failed")
        return False
        
    def _execute_single_tap(self) -> bool:
        """Execute single tap - unified for both login/logout."""
        try:
            tapper_service = TapperService(station_id=self.station_id)
            
            if not tapper_service.connect():
                self.logger.error("Failed to connect to tapper service")
                return False
            
            try:
                sequences.safe_simple_tap(tapper_service.protocol)
                self.logger.debug("Tap executed successfully")
                return True
            finally:
                tapper_service.disconnect()
                
        except Exception as e:
            self.logger.error(f"Tap execution failed: {e}")
            return False


class SimpleTappingManager:
    """
    Simplified manager - replaces complex TappingManager.
    
    Just coordinates tapping with enable/disable logic.
    """
    
    def __init__(self, station_id: str, enable_tapping: bool = True, logger=None):
        self.station_id = station_id
        self.enable_tapping = enable_tapping
        self.logger = logger or get_logger(f"tapping_manager_{station_id}")
        self.tapper = SimpleTapper(station_id, logger) if enable_tapping else None
        
    def perform_login_tap(self, verification_callback: Optional[Callable] = None) -> bool:
        """Perform login tap - simplified API."""
        if not self.enable_tapping:
            self.logger.info("Tapping disabled - skipping login tap")
            return True
            
        return self.tapper.login_tap()
        
    def perform_logoff_tap(self, expected_user: str, grpc_session_manager, **kwargs) -> bool:
        """Perform logout tap - simplified API."""
        if not self.enable_tapping:
            self.logger.info("Tapping disabled - skipping logout tap")
            return True
            
        # Perform tap
        tap_success = self.tapper.logout_tap()
        if not tap_success:
            return False
            
        # Verify logout (moved verification logic here)
        return self._verify_logout(expected_user, grpc_session_manager, kwargs.get('verification_timeout', 15))
        
    def _verify_logout(self, expected_user: str, grpc_session_manager, timeout: int) -> bool:
        """Verify logout occurred - unified verification."""
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