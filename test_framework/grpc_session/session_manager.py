"""
Pure gRPC session management without tapping concerns.
"""
import logging
import time
from typing import Optional, Dict, Any

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.registry_service_client import RegistryServiceClient
from grpc_client_sdk.services.command_service_client import CommandServiceClient
from test_framework.grpc_session.context_builder import SessionContextBuilder
from test_framework.grpc_session.session_context import SessionContext
from test_framework.utils import get_logger
from test_framework.utils.loaders.station_loader import StationLoader


class GrpcSessionManager:
    """
    Pure gRPC session management without any tapping logic.

    Responsibilities:
    - Register root gRPC client based on station configs
    - Wait for expected user to log in
    - Discover the agent's gRPC port via RegistryService
    - Construct and return a fully connected SessionContext
    - Provide logged-in user information via command service
    """

    def __init__(self, station_id: str, logger: Optional[logging.Logger] = None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"grpc_session_manager [{station_id}]")
        self.root_target = StationLoader().get_grpc_target(station_id)
        GrpcClientManager.register_clients(name="root", target=self.root_target)
        self.root_registry = RegistryServiceClient(client_name="root", logger=self.logger)
        self.root_command = CommandServiceClient(client_name="root", logger=self.logger)
        self._session_context: Optional[SessionContext] = None

    def create_session(self, expected_user: str, timeout: int = 30) -> SessionContext:
        """
        Create a gRPC session for the expected user.

        :param expected_user: Username expected to log in
        :param timeout: Time in seconds to wait for login
        :return: Fully initialized SessionContext
        """
        self.logger.info(f"Creating gRPC session for user '{expected_user}'")

        # Step 1: Connect to root registry and command service
        self._connect_to_root_services()

        # Step 2: Wait for user login
        agent_port = self._wait_for_agent_login(expected_user, timeout)

        # Step 3: Build session context
        session_context = self._build_session_context(expected_user, agent_port)
        self._session_context = session_context

        self.logger.info(f"gRPC session established for '{expected_user}'")
        return session_context

    def get_logged_in_users(self) -> Dict[str, Any]:
        """
        Get current logged-in users via root context command service.

        This is the correct way to get actual console user and logged-in users.
        """
        try:
            if self._session_context and self._session_context.root_context:
                # Use the session's root context if available
                result = self._session_context.root_context.command.get_logged_in_users()
                return result
            else:
                # Fallback to direct command service
                if not self.root_command.stub:
                    self.root_command.connect()
                result = self.root_command.get_logged_in_users()
                return result
        except Exception as e:
            self.logger.error(f"Failed to get logged in users: {e}")
            # Return empty result to avoid breaking verification
            return {"console_user": "", "logged_in_users": []}

    def _connect_to_root_services(self):
        """Connect to the root registry and command service."""
        self.logger.info("Connecting to root services...")
        self.root_registry.connect()
        self.root_command.connect()
        self.logger.info(f"Connected to root services: {self.root_target}")

    def _wait_for_agent_login(self, username: str, timeout: int, poll_interval: float = 1.0) -> int:
        """Wait for user login and return agent port."""
        self.logger.info(f"Waiting for user '{username}' to log in...")
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                agents = self.root_registry.list_agents()
                usernames = [agent["username"] for agent in agents]

                if username in usernames:
                    agent_info = self.root_registry.get_agent(username)
                    if agent_info and "port" in agent_info:
                        self.logger.info(f"User '{username}' logged in on port {agent_info['port']}")
                        return agent_info["port"]

            except Exception as e:
                self.logger.warning(f"Error checking agent login: {e}")

            time.sleep(poll_interval)

        raise RuntimeError(f"Timeout: User '{username}' did not log in within {timeout}s")

    def _build_session_context(self, username: str, agent_port: int) -> SessionContext:
        """Build and return the session context."""
        self.logger.info(f"Building session context for '{username}'")

        session_context = SessionContextBuilder.build(
            username=username,
            agent_port=agent_port,
            host=self.root_target.split(":")[0],
            logger=self.logger
        )

        return session_context