
import pytest
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger

@pytest.fixture(scope="function")
def session_manager(test_config, request, test_logger):
    """Single source of truth for gRPC session management."""
    test_name = request.node.name
    correlation_id = getattr(request.node, 'correlation_id', None)
    
    logger = get_logger(f"test.{test_name}.session")
    if correlation_id:
        logger.info(f"Session manager using correlation ID: {correlation_id}")
        
    expected_user = test_config.get("expected_user")
    login_timeout = test_config.get("login_timeout", 30)
    manager = GrpcSessionManager(
        station_id=test_config["station_id"],
        logger=logger,
        test_context=test_name
    )
    logger.info(f"Creating session for user: {expected_user} on station: {test_config['station_id']}")
    session_context = None

    try:
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