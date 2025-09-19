import time

from test_framework.utils import get_logger
from test_framework.utils.scripts.applescripts import AppleScripts


class AppleScriptLogoutManager:
    """
    AppleScript logout manager for macOS user logout operations.
    This class provides methods for performing user logout using AppleScript commands
    with retry logic and verification. It handles logout execution and verification
    through console user state checking.
    
    Attributes:
        logger (Logger): Logger instance for logout operations.
    """

    def __init__(self, logger=None):
        """
        Initialize the AppleScript logout manager.
        
        :param logger: Optional logger instance, creates default if None
        """
        self.logger = logger or get_logger("applescript_logout")

    def logout_user(self, session_context, grpc_manager, expected_user: str,
                    max_attempts: int = 3, retry_delay: float = 2.0,
                    verification_timeout: int = 15) -> bool:
        """
        Perform user logout using AppleScript with retry logic and verification.
        This method executes AppleScript logout commands and verifies the operation
        completed successfully by checking console user state.
        
        :param session_context: Session context for AppleScript execution
        :param grpc_manager: gRPC manager for logout verification
        :param expected_user: Username that should be logged out
        :param max_attempts: Maximum number of retry attempts
        :param retry_delay: Delay in seconds between retry attempts
        :param verification_timeout: Timeout in seconds for logout verification
        :return: True if logout completed and verified successfully
        """
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
        """
        Execute AppleScript logout command for specified user.
        Uses a smart fallback strategy: simple logout first, then with confirmation handling.
        
        :param session_context: Session context for AppleScript execution
        :param expected_user: Username to logout
        :return: True if AppleScript execution was successful
        """
        # Try simple logout first (works if confirmation prompt is disabled)
        if self._try_simple_logout(session_context):
            return True
            
        # If simple logout didn't work, try with confirmation handling
        self.logger.info("Simple logout failed, trying logout with confirmation handling")
        return self._try_logout_with_confirmation(session_context)
    
    def _try_simple_logout(self, session_context) -> bool:
        """
        Try the simple logout approach (works when confirmation prompt is disabled).
        
        :param session_context: Session context for AppleScript execution
        :return: True if simple logout was successful
        """
        try:
            self.logger.info("Attempting simple logout (no confirmation dialog expected)")
            script_result = session_context.user_context.apple_script.run_applescript(
                AppleScripts.APPLESCRIPT_LOG_OUT_SIMPLE
            )
            
            self.logger.debug(f"Simple logout result: {script_result}")
            
            if script_result and script_result.get("success", False):
                self.logger.info("✅ Simple logout executed successfully")
                return True
            else:
                error_msg = script_result.get('error', 'Unknown error') if script_result else 'No result'
                self.logger.debug(f"Simple logout failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.debug(f"Simple logout exception: {e}")
            return False
    
    def _try_logout_with_confirmation(self, session_context) -> bool:
        """
        Try logout with confirmation dialog handling.
        
        :param session_context: Session context for AppleScript execution
        :return: True if logout with confirmation was successful
        """
        try:
            self.logger.info("Attempting logout with confirmation dialog handling")
            script_result = session_context.user_context.apple_script.run_applescript(
                AppleScripts.APPLESCRIPT_LOG_OUT_WITH_CONFIRM
            )
            
            self.logger.info(f"Logout with confirmation result: {script_result}")
            
            if script_result and script_result.get("success", False):
                self.logger.info("✅ Logout with confirmation executed successfully")
                return True
            else:
                error_msg = script_result.get('error', 'Unknown error') if script_result else 'No result'
                self.logger.error(f"Logout with confirmation failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Logout with confirmation exception: {e}")
            return False

    def _verify_logout(self, grpc_manager, expected_user: str, timeout: int) -> bool:
        """
        Verify logout operation completed by checking console user state.
        This method polls the console user state to confirm the expected user
        is no longer the active console user.
        
        :param grpc_manager: gRPC manager for console state queries
        :param expected_user: Username that should be logged out
        :param timeout: Verification timeout in seconds
        :return: True if logout verified successfully
        """
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