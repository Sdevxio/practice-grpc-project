from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.command_service_client import CommandServiceClient


def test_run_command_service_client(setup):
    """
    Test the CommandServiceClient for executing shell commands and retrieving logged-in user information.
    This test verifies the connection to the gRPC server and the execution of a simple shell commands.
    It checks if the client is registered and connected, and if the commands executes
    successfully.

    :param setup: Fixture that sets up the gRPC server and client.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a CommandServiceClient instance
    command_client = CommandServiceClient(client_name="root")
    # Connect to the gRPC server
    command_client.connect()

    # Run a simple shell commands
    result = command_client.run_command(command="whoami")

    # Check the result
    assert result.exit_code == 0
    assert result.stdout.strip(), "Expected non-empty output"


def test_get_logged_in_users(setup):
    """
    Test the CommandServiceClient for retrieving logged-in users.
    This test verifies the connection to the gRPC server and the retrieval of logged-in users.

    :param setup: Fixture that sets up the gRPC server and client.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a CommandServiceClient instance
    command_client = CommandServiceClient(client_name="root")
    # Connect to the gRPC server
    command_client.connect()

    # Get logged-in users
    username = "macos_lab_1"
    result = command_client.get_logged_in_users()
    print(f"Logged-in users: {result}")

    # Check if the result is a dictionary and not empty
    assert isinstance(result, dict)
    assert "logged_in_users", "console_user" in result
    assert username in result["logged_in_users"], f"Expected {username} to be in logged-in users"

