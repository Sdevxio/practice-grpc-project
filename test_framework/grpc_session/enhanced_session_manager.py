"""
Enhanced Session Manager with Rapid Agent Deployment
For dynamic authentication testing with card-tap workflows
"""
import time
import logging
from typing import Optional

from grpc_client_sdk.services.registry_service_client import RegistryServiceClient
from grpc_client_sdk.services.command_service_client import CommandServiceClient
from test_framework.grpc_session.context_builder import SessionContextBuilder
from test_framework.grpc_session.session_context import SessionContext
from test_framework.utils.loaders.station_loader import StationLoader
from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class EnhancedSessionManager:
    """
    Enhanced Session Manager with rapid agent deployment for dynamic authentication testing.
    
    This version adds the ability to trigger immediate agent deployment for users,
    perfect for card-tap authentication workflows where agents need to be ready
    within seconds of user login.
    
    New capabilities:
    - deploy_agent(): Trigger immediate agent deployment
    - Enhanced wait logic: Tries deployment if agent not found
    - Better timeout handling for dynamic user creation scenarios
    """

    def __init__(self, station_id: str, logger: Optional[logging.Logger] = None, test_context: str = None):
        self.station_id = station_id
        self.test_context = test_context
        
        # Create correlated logger name based on context
        if test_context:
            logger_name = f"test.{test_context}.session.{station_id}"
        else:
            logger_name = f"session.{station_id}.manager"
            
        self.logger = logger or get_logger(logger_name)
        self.root_target = StationLoader().get_grpc_target(station_id)
        GrpcClientManager.register_clients(name="root", target=self.root_target)
        self.root_registry = RegistryServiceClient(client_name="root", logger=self.logger)
        self.root_command = CommandServiceClient(client_name="root", logger=self.logger)
        self._session_context: Optional[SessionContext] = None

    def create_session_with_deployment(self, expected_user: str, timeout: int = 60, deploy_if_needed: bool = True) -> SessionContext:
        """
        Create a gRPC session with enhanced agent deployment for dynamic authentication testing.
        
        :param expected_user: Username expected to log in
        :param timeout: Time in seconds to wait for login and deployment
        :param deploy_if_needed: Whether to trigger agent deployment if not found
        :return: Fully initialized SessionContext
        
        Perfect for card-tap authentication workflows:
        1. User taps card -> Application authenticates -> User logs in
        2. Test calls this method immediately
        3. If agent doesn't exist, automatically deploys it
        4. Returns ready SessionContext within seconds
        """
        self.logger.info(f"Creating enhanced gRPC session for user '{expected_user}' (deploy_if_needed={deploy_if_needed})")

        # Step 1: Connect to root registry and command service
        self._connect_to_root_services()

        # Step 2: Enhanced wait with deployment capability
        agent_port = self._wait_for_agent_with_deployment(expected_user, timeout, deploy_if_needed)

        # Step 3: Build session context
        session_context = self._build_session_context(expected_user, agent_port)
        self._session_context = session_context

        self.logger.info(f"Enhanced gRPC session established for '{expected_user}' on port {agent_port}")
        return session_context

    def deploy_agent(self, username: str, timeout: int = 30) -> Optional[dict]:
        """
        Deploy agent immediately for specified user.
        
        :param username: macOS username to deploy agent for
        :param timeout: Timeout for deployment operation
        :return: Agent info dict if successful, None if failed
        
        Example usage:
            # After card tap authentication
            session_manager = EnhancedSessionManager("mac-endpoint-01")
            agent_info = session_manager.deploy_agent("testuser1")
            if agent_info:
                print(f"Agent ready on port {agent_info['port']}")
        """
        self.logger.info(f"Requesting rapid agent deployment for user: {username}")
        
        # Ensure connection to registry
        if not hasattr(self, '_registry_connected'):
            self._connect_to_root_services()
        
        # Call the new deploy_agent method
        agent_info = self.root_registry.deploy_agent(username, timeout=timeout)
        
        if agent_info:
            self.logger.info(f"✅ Agent deployed for {username} on port {agent_info['port']}")
        else:
            self.logger.error(f"❌ Failed to deploy agent for {username}")
            
        return agent_info

    def _connect_to_root_services(self):
        """Connect to root registry and command services."""
        self.root_registry.connect()
        self.root_command.connect()
        self.logger.info(f"Connected to root services: {self.root_target}")
        self._registry_connected = True

    def _wait_for_agent_with_deployment(self, username: str, timeout: int, deploy_if_needed: bool, poll_interval: float = 1.0) -> int:
        """
        Enhanced wait logic with automatic agent deployment capability.
        
        Strategy:
        1. First, check if agent already exists (fast path)
        2. If not found and deploy_if_needed=True, trigger deployment
        3. Continue polling for agent registration
        4. Handle both existing users and newly created users
        """
        self.logger.info(f"Waiting for user '{username}' agent (timeout={timeout}s, deploy_if_needed={deploy_if_needed})")
        deadline = time.time() + timeout
        deployment_attempted = False

        while time.time() < deadline:
            try:
                # Check if agent is already registered
                agent_info = self.root_registry.get_agent(username)
                if agent_info and "port" in agent_info:
                    self.logger.info(f"✅ User '{username}' agent found on port {agent_info['port']}")
                    return agent_info["port"]

                # If agent not found and we haven't tried deployment yet
                if deploy_if_needed and not deployment_attempted:
                    self.logger.info(f"Agent not found for '{username}' - attempting deployment...")
                    
                    # Try to deploy agent immediately
                    deployed_agent = self.root_registry.deploy_agent(username, timeout=min(30, int(deadline - time.time())))
                    deployment_attempted = True
                    
                    if deployed_agent and deployed_agent.get("port", 0) > 0:
                        self.logger.info(f"✅ Agent deployed for '{username}' on port {deployed_agent['port']}")
                        return deployed_agent["port"]
                    else:
                        self.logger.warning(f"Deployment initiated for '{username}', continuing to poll...")

                # Continue polling
                remaining = deadline - time.time()
                if remaining > 0:
                    self.logger.debug(f"Polling for '{username}' agent... ({remaining:.1f}s remaining)")
                    time.sleep(min(poll_interval, remaining))

            except Exception as e:
                self.logger.warning(f"Error during agent wait/deployment for '{username}': {e}")
                time.sleep(poll_interval)

        raise RuntimeError(f"Timeout: Agent for user '{username}' not ready within {timeout}s (deployment_attempted={deployment_attempted})")

    def _build_session_context(self, username: str, agent_port: int) -> SessionContext:
        """Build and return the session context."""
        self.logger.info(f"Building session context for '{username}' on port {agent_port}")

        session_context = SessionContextBuilder.build(
            username=username,
            agent_port=agent_port,
            host=self.root_target.split(":")[0],
            logger=self.logger,
            test_context=self.test_context
        )

        return session_context

    def get_logged_in_users(self) -> list:
        """Get list of currently logged-in users with agents."""
        if not hasattr(self, '_registry_connected'):
            self._connect_to_root_services()
            
        try:
            agents = self.root_registry.list_agents()
            return [agent["username"] for agent in agents]
        except Exception as e:
            self.logger.warning(f"Error getting logged-in users: {e}")
            return []

    # Backward compatibility with original SessionManager
    def create_session(self, expected_user: str, timeout: int = 30) -> SessionContext:
        """Original method for backward compatibility."""
        return self.create_session_with_deployment(expected_user, timeout, deploy_if_needed=False)