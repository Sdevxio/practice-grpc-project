"""
Session management fixtures.

Provides gRPC session management with clean single-source-of-truth pattern.
"""

import pytest
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger


@pytest.fixture(scope="function")
def session_manager(test_config, request):
    """Single source of truth for gRPC session management."""
    logger = get_logger(f"session_manager-{request.node.name}")
    
    manager = GrpcSessionManager(
        station_id=test_config["station_id"],
        logger=logger
    )
    logger.info(f"Session manager created for station: {test_config['station_id']}")
    
    yield manager
    
    try:
        logger.info("Cleaning up session manager")
    except Exception as e:
        logger.warning(f"Session cleanup warning: {e}")


@pytest.fixture(scope="function")
def authenticated_session(session_manager, test_config):
    """Session manager with user already authenticated."""
    logger = get_logger("authenticated_session")
    
    expected_user = test_config["expected_user"]
    logger.info(f"Setting up authenticated session for user: {expected_user}")
    
    session_manager.create_session(
        expected_user=expected_user,
        timeout=test_config["login_timeout"]
    )
    
    logger.info(f"User {expected_user} authenticated and ready")
    yield session_manager