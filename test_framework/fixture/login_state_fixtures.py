"""
Login state fixtures for tapper testing with rapid agent deployment.
"""

import pytest
import time
from test_framework.login_state.login_manager import LoginManager
from test_framework.grpc_session.enhanced_session_manager import EnhancedSessionManager
from test_framework.utils import get_logger


@pytest.fixture
def login_state(session_manager, request):
    """All-in-one login testing fixture."""
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.login_state")
    login_manager = LoginManager(station_id="station1", logger=logger)
    manager, session_context = session_manager
    
    def get_console_user():
        try:
            user_info = manager.get_logged_in_users()
            return user_info.get("console_user", "")
        except Exception as e:
            logger.error(f"Failed to get console user: {e}")
            return ""
    
    # Check if auto-management is enabled
    marker = request.node.get_closest_marker("auto_manage")
    if marker and marker.args:
        auto_manage = marker.args[0]
    else:
        auto_manage = True
    
    class LoginTester:
        def __init__(self):
            self.manager = login_manager
            self.get_user = get_console_user
            self.logger = logger
            # Initialize enhanced session manager for rapid agent deployment
            self.enhanced_session = EnhancedSessionManager(
                station_id="mac-endpoint-01",  # Use appropriate station ID
                logger=logger,
                test_context=f"fixture.{test_name}"
            )
            self.agent_deployed = False
            
        def ensure_logged_out(self):
            """Ensure logged out state - call if needed."""
            current = self.get_user()
            if current and current != "root":
                self.logger.info(f"Logging out '{current}' to ensure logged-out state")
                self.manager.logout_tap()
                self.agent_deployed = False  # Reset agent status
                
        def ensure_logged_in(self):
            """Ensure logged in state with immediate agent deployment."""
            current = self.get_user()
            if not current or current == "root":
                self.logger.info("=== FIXTURE: Performing login tap + agent deployment ===")
                
                # Step 1: Perform the tap
                tap_success = self.manager.login_tap()
                if not tap_success:
                    self.logger.error("Login tap failed")
                    return
                
                # Step 2: Get the logged-in user (might be different from current)
                time.sleep(2)  # Brief pause for login to settle
                logged_in_user = self.get_user()
                
                if logged_in_user and logged_in_user != "root":
                    self.logger.info(f"User '{logged_in_user}' logged in - deploying agent immediately")
                    
                    # Step 3: Deploy agent immediately after successful login
                    try:
                        deployment_start = time.time()
                        agent_info = self.enhanced_session.deploy_agent(logged_in_user, timeout=30)
                        deployment_time = time.time() - deployment_start
                        
                        if agent_info:
                            self.logger.info(f"FIXTURE: Agent deployed for '{logged_in_user}' in {deployment_time:.2f}s on port {agent_info['port']}")
                            self.agent_deployed = True
                        else:
                            self.logger.error(f"FIXTURE: Agent deployment failed for '{logged_in_user}'")
                            self.agent_deployed = False
                            
                    except Exception as e:
                        deployment_time = time.time() - deployment_start
                        self.logger.error(f"FIXTURE: Agent deployment error after {deployment_time:.2f}s: {e}")
                        self.agent_deployed = False
                else:
                    self.logger.warning("No valid user logged in after tap")
                    self.agent_deployed = False
            else:
                # User already logged in, check if agent is deployed
                self.logger.info(f"User '{current}' already logged in - checking agent status")
                self._ensure_agent_deployed(current)
        
        def _ensure_agent_deployed(self, username):
            """Ensure agent is deployed for the specified user."""
            try:
                # Ensure connection to registry
                if not hasattr(self.enhanced_session, '_registry_connected'):
                    self.enhanced_session._connect_to_root_services()
                
                # Check if agent already exists
                agent_info = self.enhanced_session.root_registry.get_agent(username)
                if agent_info:
                    self.logger.info(f"FIXTURE: Agent already running for '{username}' on port {agent_info['port']}")
                    self.agent_deployed = True
                else:
                    self.logger.info(f"Agent not found for '{username}' - deploying now")
                    # Deploy agent
                    deployment_start = time.time()
                    agent_info = self.enhanced_session.deploy_agent(username, timeout=30)
                    deployment_time = time.time() - deployment_start
                    
                    if agent_info:
                        self.logger.info(f"FIXTURE: Agent deployed for '{username}' in {deployment_time:.2f}s on port {agent_info['port']}")
                        self.agent_deployed = True
                    else:
                        self.logger.error(f"FIXTURE: Agent deployment failed for '{username}'")
                        self.agent_deployed = False
            except Exception as e:
                self.logger.error(f"Error ensuring agent deployment for '{username}': {e}")
                self.agent_deployed = False
        
        def get_agent_info(self, username=None):
            """Get agent information for user (or current user if not specified)."""
            if not username:
                username = self.get_user()
            
            if not username or username == "root":
                return None
                
            try:
                # Ensure connection to registry
                if not hasattr(self.enhanced_session, '_registry_connected'):
                    self.enhanced_session._connect_to_root_services()
                
                return self.enhanced_session.root_registry.get_agent(username)
            except Exception as e:
                self.logger.error(f"Error getting agent info for '{username}': {e}")
                return None
                
        def cleanup(self):
            """Cleanup - logout user."""
            current = self.get_user()
            if current and current != "root":
                self.logger.info(f"FIXTURE: Cleanup - logging out '{current}'")
                self.manager.logout_tap()
            self.agent_deployed = False
    
    login_state = LoginTester()
    if auto_manage:
        login_state.ensure_logged_in() # Ensure clean start

    
    yield login_state
    
    # Auto cleanup if enabled
    if auto_manage:
        login_state.cleanup()