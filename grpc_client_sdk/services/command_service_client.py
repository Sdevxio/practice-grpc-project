from typing import Optional, Generator, Dict, Any

from generated import commands_service_pb2
from generated.commands_service_pb2_grpc import CommandServiceStub
from grpc import RpcError

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class CommandServiceClient:
    """
    CommandServiceClient is a gRPC client for executing shell commands and retrieving logged-in user information on macOS endpoint.
    It provides methods to run commands synchronously, stream commands output in real-time, and fetch the list of users currently logged in.

    Supported operations:
    - run_command: Executes shell commands and returns the exit code, stdout, and stderr.
    - stream_command: Executes shell commands and streams output in real-time.
    - get_logged_in_users: Fetches the list of users currently logged in to the system.

    Typical use cases:
    - Running shell commands for diagnostics or configuration.
    - Streaming output from long-running commands (tail, top, etc.).
    - Fetching the list of logged-in users for session management.

    Attributes:
        client_name (str): Logical client context ('root' or username).
        logger (Logger): Logger instance.
        stub (CommandServiceStub): gRPC stub.

    Usage:
        client = CommandServiceClient(client_name="root")
        client.connect()

        # Synchronous execution
        result = client.run_command('ls', ['-l'])
        print(result['stdout'])

        # Streaming execution
        for output in client.stream_command('tail', ['-f', '/var/log/system.log']):
            print(output['output'], end='')
    """

    def __init__(self, client_name: str = "root", logger: Optional[object] = None):
        """
        Initializes the CommandServiceClient.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"service.commands.{client_name}")
        self.stub: Optional[CommandServiceStub] = None

    def connect(self) -> None:
        """
        Establishes the gRPC connection and stub for CommandService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, CommandServiceStub)

    def run_command(self, command: str, arguments: Optional[list] = None, target_user: str = "") -> dict:
        """
        Executes a shell commands and returns its result.

        :param command: Command to execute (e.g., 'ls').
        :param arguments: Arguments to pass to the commands.
        :param target_user: User to target if needed.
        :return: Dictionary containing 'exit_code', 'stdout', and 'stderr'.

        Example:
            result = client.run_command('ls', ['-l'], target_user='username')
            print(result['stdout'])  # Should print the output of the 'ls -l' commands
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing commands.")

        request = commands_service_pb2.CommandRequest(
            command=command,
            arguments=arguments or [],
            target_user=target_user
        )

        try:
            response = self.stub.RunCommand(request)
            self.logger.info(f"Command executed: {command} {' '.join(arguments or [])}")
            return {
                "exit_code": response.exit_code,
                "stdout": response.stdout,
                "stderr": response.stderr
            }
        except RpcError as e:
            self.logger.error(f"gRPC error while executing commands: {str(e.details())}")
            raise

    def stream_command(
            self,
            command: str,
            arguments: Optional[list] = None,
            target_user: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a shell commands and streams its output in real-time.
        This method is useful for long-running commands like 'tail -f', 'top', or build processes
        where you want to see output as it's generated.

        :param command: Command to execute (e.g., 'tail').
        :param arguments: Arguments to pass to the commands (e.g., ['-f', '/var/log/system.log']).
        :param target_user: User to target if needed.
        :return: Generator yielding dictionaries with 'output' and 'is_error' fields.

        Example:
            # Stream a log file
            for output in client.stream_command('tail', ['-f', '/var/log/system.log']):
                if output['is_error']:
                    print(f"ERROR: {output['output']}")
                else:
                    print(f"LOG: {output['output']}", end='')

            # Stream a build process
            for output in client.stream_command('make', ['all']):
                print(output['output'], end='')
                if output['is_error']:
                    print("Build encountered errors")
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing commands.")

        request = commands_service_pb2.CommandRequest(
            command=command,
            arguments=arguments or [],
            target_user=target_user
        )

        try:
            self.logger.info(f"Streaming commands: {command} {' '.join(arguments or [])}")

            # Get the streaming response from the server
            stream = self.stub.StreamCommand(request)

            for response in stream:
                yield {
                    "output": response.output,
                    "is_error": response.is_error
                }

        except RpcError as e:
            self.logger.error(f"gRPC error while streaming commands: {str(e.details())}")
            # Yield error information instead of raising to allow graceful handling
            yield {
                "output": f"gRPC Error: {str(e.details())}\n",
                "is_error": True
            }
        except Exception as e:
            self.logger.error(f"Unexpected error while streaming commands: {str(e)}")
            yield {
                "output": f"Unexpected Error: {str(e)}\n",
                "is_error": True
            }

    def get_logged_in_users(self) -> dict:
        """
        Retrieves the currently logged-in users on the system.

        :return: Dictionary containing the list of logged-in users.

        Example:
            result = client.get_logged_in_users()
            print(f"Console user: {result['console_user']}")
            print(f"Logged-in users: {result['logged_in_users']}")
        """
        if not self.stub:
            raise RuntimeError("CommandServiceClient not connected.")

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