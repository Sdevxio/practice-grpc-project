"""
Simplified AppleScript Logout - Clean and focused.
"""

import time
from typing import Optional
from test_framework.utils import get_logger


class AppleScriptLogoutManager:
    """
    Simple, focused AppleScript logout manager.
    
    Matches the simplified tapping approach.
    """
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger("applescript_logout")
        
    def logout_user(self, session_context, grpc_manager, expected_user: str,
                   max_attempts: int = 3, retry_delay: float = 2.0, 
                   verification_timeout: int = 15) -> bool:
        """Perform AppleScript logout - simple and clean."""
        self.logger.info(f"Starting AppleScript logout for user '{expected_user}' (max attempts: {max_attempts})")
        
        for attempt in range(max_attempts):
            self.logger.info(f"AppleScript logout attempt {attempt + 1}/{max_attempts}")
            
            if self._execute_applescript_logout(session_context, expected_user):
                if self._verify_logout(grpc_manager, expected_user, verification_timeout):
                    self.logger.info(f"AppleScript logout completed successfully for user '{expected_user}'")
                    return True
                else:
                    self.logger.warning(f"AppleScript logout verification failed on attempt {attempt + 1}")
            else:
                self.logger.warning(f"AppleScript logout execution failed on attempt {attempt + 1}")
                
            if attempt < max_attempts - 1:
                self.logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        self.logger.error(f"All {max_attempts} AppleScript logout attempts failed")
        return False
        
    def _execute_applescript_logout(self, session_context, expected_user: str) -> bool:
        """Execute AppleScript logout - unified logic."""
        try:
            script_result = session_context.user_context.apple_script.logout_user(expected_user)
            self.logger.info(f"AppleScript execution result: {script_result}")
            
            if script_result.get("success", False):
                self.logger.debug(f"AppleScript logout executed: {script_result.get('output', 'No output')}")
                return True
            else:
                self.logger.error(f"AppleScript logout failed: {script_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"AppleScript execution failed: {e}")
            return False
            
    def _verify_logout(self, grpc_manager, expected_user: str, timeout: int) -> bool:
        """Verify logout occurred - unified verification."""
        self.logger.info(f"Verifying logout for user: {expected_user}...")
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                current_state = grpc_manager.get_logged_in_users()
                console_user = current_state.get("console_user", "")
                
                if console_user != expected_user:
                    self.logger.info(f"Logout verified - user changed from '{expected_user}' to '{console_user}'")
                    return True
                    
                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Logout verification failed: {e}")
                return False
                
        self.logger.warning(f"Logout verification timed out - user may still be '{expected_user}'")
        return False
