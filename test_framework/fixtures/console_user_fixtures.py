import pytest
from typing import Optional, Dict, Any
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger


@pytest.fixture(scope="function")
def console_user_tracker(test_config, request):
    """
    Console user tracking fixture for getting current login state.
    
    This fixture provides methods to query the current console user state
    without interfering with login/logout operations.
    
    Usage:
        def test_example(console_user_tracker):
            current_user = console_user_tracker.get_current_user()
            is_logged_out = console_user_tracker.is_console_root()
    """
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.console_tracker")
    station_id = test_config.get("station_id", "station1")
    
    class ConsoleUserTracker:
        def __init__(self):
            self.logger = logger
            self.station_id = station_id
            self._grpc_manager = None
        
        def _get_grpc_manager(self) -> GrpcSessionManager:
            """Get or create GrpcSessionManager for queries."""
            if self._grpc_manager is None:
                self._grpc_manager = GrpcSessionManager(
                    station_id=self.station_id, 
                    logger=self.logger,
                    test_context=test_name
                )
            return self._grpc_manager
        
        def get_console_user_info(self) -> Dict[str, Any]:
            """
            Get full console user information.
            
            Returns:
                Dict with 'console_user' and 'logged_in_users' keys
                Example: {'console_user': 'admin', 'logged_in_users': ['admin']}
                When logged out: {'console_user': 'root', 'logged_in_users': ['admin']}
            """
            try:
                grpc_manager = self._get_grpc_manager()
                result = grpc_manager.get_logged_in_users()
                self.logger.debug(f"Console user info: {result}")
                return result
            except Exception as e:
                self.logger.warning(f"Failed to get console user info: {e}")
                return {"console_user": "", "logged_in_users": []}
        
        def get_current_user(self) -> Optional[str]:
            """
            Get currently logged in user from console.
            
            Returns:
                Username if user is logged in, None if logged out (console_user == 'root')
            """
            user_info = self.get_console_user_info()
            console_user = user_info.get("console_user", "")
            
            # If console_user is 'root', it means no user is logged in
            if console_user == "root" or not console_user:
                return None
            
            return console_user
        
        def is_console_root(self) -> bool:
            """
            Check if console user is 'root' (indicates logged out state).
            
            Returns:
                True if console_user is 'root', False otherwise
            """
            user_info = self.get_console_user_info()
            console_user = user_info.get("console_user", "")
            return console_user == "root"
        
        def verify_user_logged_in(self, expected_user: str) -> bool:
            """
            Verify specific user is logged in.
            
            Args:
                expected_user: Username to verify
                
            Returns:
                True if expected_user is currently the console user, False otherwise
            """
            current_user = self.get_current_user()
            is_logged_in = current_user == expected_user
            self.logger.debug(f"User verification: expected={expected_user}, current={current_user}, match={is_logged_in}")
            return is_logged_in
        
        def verify_user_logged_out(self, expected_logged_out_user: str) -> bool:
            """
            Verify specific user is logged out.
            
            Args:
                expected_logged_out_user: Username that should be logged out
                
            Returns:
                True if console_user is 'root' or different from expected_logged_out_user
            """
            if self.is_console_root():
                self.logger.debug(f"User {expected_logged_out_user} logged out - console is root")
                return True
            
            current_user = self.get_current_user()
            is_logged_out = current_user != expected_logged_out_user
            self.logger.debug(f"Logout verification: expected_logged_out={expected_logged_out_user}, current={current_user}, logged_out={is_logged_out}")
            return is_logged_out
        
        def get_logged_in_users_list(self) -> list:
            """
            Get list of all logged in users.
            
            Returns:
                List of usernames that have logged in sessions
            """
            user_info = self.get_console_user_info()
            return user_info.get("logged_in_users", [])
    
    return ConsoleUserTracker()