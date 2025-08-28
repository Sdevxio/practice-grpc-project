from typing import Optional

from generated import commands_service_pb2
from generated.commands_service_pb2_grpc import CommandServiceStub
from grpc import RpcError

from grpc_client_sdk.core.base_service_client import BaseServiceClient


class CommandServiceClient(BaseServiceClient):
    """
    CommandServiceClient is a gRPC client for executing shell commands and retrieving logged-in user information on macOS endpoint.
    It provides methods to run commands synchronously and fetch the list of users currently logged in.

    Supported operations:
    - run_command: Executes shell commands and returns the exit code, stdout, and stderr.
    - get_logged_in_users: Fetches the list of users currently logged in to the system.

    Typical use cases:
    - Running shell commands for diagnostics or configuration.
    - Fetching the list of logged-in users for session management.

    Attributes:
        client_name (str): Logical client context ('root' or username).
        logger (Logger): Logger instance.
        stub (CommandServiceStub): gRPC stub.

    Usage:
        client = CommandServiceClient(client_name="root")
        client.connect()
        result = client.run_command('ls', ['-l'])
        print(result['stdout'])  # Should print the output of the 'ls -l' command
    """

    @property
    def stub_class(self) -> type:
        return CommandServiceStub
    
    @property
    def service_name(self) -> str:
        return "CommandService"
    
    def __init__(self, client_name: str = "root", logger: Optional[object] = None):
        """
        Initializes the CommandServiceClient.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If None, a default logger is created.
        """
        super().__init__(client_name, "root", logger)

    def run_command(self, command: str, arguments: Optional[list] = None, target_user: str = "") -> dict:
        """
        Executes a shell command and returns its result.

        :param command: Command to execute (e.g., 'ls').
        :param arguments: Arguments to pass to the command.
        :param target_user: User to target if needed.
        :return: Dictionary containing 'exit_code', 'stdout', and 'stderr'.

        Example:
            result = client.run_command('ls', ['-l'], target_user='username')
            print(result['stdout'])  # Should print the output of the 'ls -l' command
        """
        self.ensure_connected()

        request = commands_service_pb2.CommandRequest(
            command=command,
            arguments=arguments or [],
            target_user=target_user
        )

        try:
            response = self.stub.RunCommand(request)
            self.logger.info(f"Command executed: {command} {' '.join(arguments or [])}")
            return response
        except RpcError as e:
            self.logger.error(f"gRPC error while executing command: {str(e.details())}")
            raise

    def get_logged_in_users(self) -> dict:
        """
        Retrieves the currently logged-in users on the system.
        :return: Dictionary containing the list of logged-in users.

        Example:
            result = client.get_logged_in_users()
            print(result)
        """
        self.ensure_connected()

        try:
            response = self.stub.GetLoggedInUsers(commands_service_pb2.GetLoggedInUsersRequest())
            self.logger.info("Retrieved logged-in user info.")
            return {
                "console_user": response.console_user,
                "logged_in_users": list(response.logged_in_users)
            }
        except RpcError as e:
            self.logger.error(f"gRPC error while fetching logged-in users: {e.details()}")
            raise