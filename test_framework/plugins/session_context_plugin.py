import pytest

from test_framework.grpc_session.session_manager import GrpcSessionManager


def pytest_configure(config):
    config.addinivalue_line("markers", "user(username): override expected user for session")

@pytest.fixture(scope="function")
def full_session_context(request, station_loader):
    """
    Provides a connected SessionContext.
    Uses @pytest.mark.user(...) to override login user.

    :param request: The pytest request object.
    :param station_loader: The station loader object.
    :return: A connected SessionContext.

    Example usage:
        @pytest.mark.user("test_user")
        def test_example(full_session_context):
            assert full_session_context.username == "test_user"
    """
    marker = request.node.get_closest_marker("station1")
    expected_user = marker.args[0] if marker else "default_user"
    station_id = station_loader()
    manager = GrpcSessionManager(station_id)
    return manager.start(expected_user=expected_user)


@pytest.fixture(scope="function")
def root_context(full_session_context):
    """
    Provides the root context of the session.

    :param full_session_context: The full session context.
    :return: The root context of the session.

    Example usage:
        def test_example(root_context):
            assert root_context is not None
    """
    return full_session_context.root_context

@pytest.fixture(scope="function")
def agent_context(full_session_context):
    """
    Provides the agent context of the session.

    :param full_session_context: The full session context.
    :return: The agent context of the session.

    Example usage:
        def test_example(agent_context):
            assert agent_context is not None
    """
    return full_session_context.user_context