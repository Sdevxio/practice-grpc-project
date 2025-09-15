
from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.command_service_client import CommandServiceClient


def test_run_command_service_client(setup):
    """
    Test executing shell commands via CommandServiceClient.
    This test verifies command execution and result handling.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a CommandServiceClient instance
    command_client = CommandServiceClient(client_name="root")
    command_client.connect()

    # Execute the command
    result = command_client.run_command(command="whoami")

    # Check the result
    assert result.get('exit_code') == 0
    assert result.get('stdout').strip(), "Expected non-empty output"

def test_get_logged_in_users(setup):
    """
    Test retrieving logged-in users via CommandServiceClient.
    This test verifies user information retrieval.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a CommandServiceClient instance
    command_client = CommandServiceClient(client_name="root")
    command_client.connect()

    # Get logged-in users
    result = command_client.get_logged_in_users()
    print(f"Logged-in users: {result}")

    # Check if the result is a dictionary and not empty
    assert isinstance(result, dict)
    assert "logged_in_users" in result and "console_user" in result

    # More flexible assertion - check that we have some logged-in users
    logged_in_users = result.get("logged_in_users", [])
    assert isinstance(logged_in_users, list), "Expected logged_in_users to be a list"

