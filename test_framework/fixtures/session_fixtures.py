import pytest
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger
import time


@pytest.fixture(scope="function")
def session_manager(test_config, request):
    """
    Session manager fixtures that provides a GrpcSessionManager and SessionContext.

    This fixtures assumes login has already happened via the login_state fixtures.
    It only handles gRPC session creation and management.
    """
    test_name = request.node.name
    correlation_id = getattr(request.node, 'correlation_id', None)

    logger = get_logger(f"test.{test_name}.session")
    if correlation_id:
        logger.info(f"Session manager using correlation ID: {correlation_id}")

    expected_user = test_config.get("expected_user")
    login_timeout = test_config.get("session_timeout", 10)
    manager = GrpcSessionManager(
        station_id=test_config["station_id"],
        logger=logger,
        test_context=test_name
    )
    logger.info(f"Creating session for user: {expected_user} on station: {test_config['station_id']}")
    session_context = None

    try:
        # Wait for login to be fully processed before creating session
        logger.info("Waiting for login to be fully processed before creating session...")
        time.sleep(3.0)

        session_context = manager.create_session(
            expected_user=expected_user,
            timeout=login_timeout
        )
        logger.info(f"Session established for user: {session_context.username}")
        yield manager, session_context
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        pytest.fail(f"Session creation failed: {e}")
    finally:
        try:
            if session_context:
                logger.info(f"Cleaning up session for user: {session_context.username}")
            else:
                logger.info("Cleaning up session manager without active session")
        except Exception as e:
            logger.warning(f"Session cleanup warning: {e}")


@pytest.fixture(scope="function")
def lightweight_session(test_config, request):
    """
    Lightweight session manager fixture for quick session creation without delays.
    
    This fixture creates a GrpcSessionManager and SessionContext immediately
    without the timing delays of the legacy session_manager fixture.
    Ideal for AppleScript tests and other scenarios where timing is critical.
    """
    test_name = request.node.name
    correlation_id = getattr(request.node, 'correlation_id', None)

    logger = get_logger(f"test.{test_name}.lightweight_session")
    if correlation_id:
        logger.info(f"Lightweight session using correlation ID: {correlation_id}")

    expected_user = test_config.get("expected_user")
    login_timeout = test_config.get("session_timeout", 10)
    manager = GrpcSessionManager(
        station_id=test_config["station_id"],
        logger=logger,
        test_context=test_name
    )
    logger.info(f"Creating lightweight session for user: {expected_user} on station: {test_config['station_id']}")
    session_context = None

    try:
        # No delay - create session immediately for timing-sensitive tests
        session_context = manager.create_session(
            expected_user=expected_user,
            timeout=login_timeout
        )
        logger.info(f"Lightweight session established for user: {session_context.username}")
        yield manager, session_context
    except Exception as e:
        logger.error(f"Failed to create lightweight session: {e}")
        pytest.fail(f"Lightweight session creation failed: {e}")
    finally:
        try:
            if session_context:
                logger.info(f"Cleaning up lightweight session for user: {session_context.username}")
            else:
                logger.info("Cleaning up lightweight session manager without active session")
        except Exception as e:
            logger.warning(f"Lightweight session cleanup warning: {e}")