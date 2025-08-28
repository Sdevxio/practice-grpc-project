"""
Clean Test Fixtures Architecture

Single responsibility, clear hierarchy, no duplication.

Layer 1: Foundation (no dependencies)
Layer 2: Core (single source of truth) 
Layer 3: Services (depend on core)
Layer 4: Convenience (sugar for common patterns)
"""

import pytest
from datetime import datetime
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils.ui_timing_calculator.timing_calculator import TimingCalculator
from test_framework.utils import get_logger


# =============================================================================
# LAYER 1: FOUNDATION (No dependencies)
# =============================================================================

@pytest.fixture(scope="function")
def timing_calc():
    """Independent timing calculator - no dependencies."""
    return TimingCalculator()


# =============================================================================  
# LAYER 2: CORE (Single source of truth)
# =============================================================================

@pytest.fixture(scope="function")
def grpc_session(test_config, request):
    """
    THE single gRPC session manager.
    
    This is the ONLY place that creates GrpcSessionManager.
    All other components use this session.
    """
    logger = get_logger(f"grpc_session-{request.node.name}")
    
    session_mgr = GrpcSessionManager(test_config["station_id"])
    logger.info(f"✅ gRPC session created for station: {test_config['station_id']}")
    
    yield session_mgr
    
    # Simple cleanup
    try:
        logger.info("🧹 Cleaning up gRPC session")
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")


# =============================================================================
# LAYER 3: SERVICES (Depend on core)  
# =============================================================================

@pytest.fixture(scope="function")
def logs_client(grpc_with_user, test_config):
    """Log streaming client using the shared gRPC session with user setup."""
    logger = get_logger("logs_client")
    
    expected_user = test_config.get("expected_user", "admin")
    
    # Get logs service from the session (grpc_with_user ensures user is setup)
    logs_service = grpc_with_user.logs_monitor_stream(expected_user)
    
    logger.info(f"✅ Logs client ready for user: {expected_user}")
    
    yield logs_service
    
    # Cleanup
    try:
        logs_service.stop_all_streams()
        logger.info("🧹 Stopped all log streams")
    except Exception as e:
        logger.warning(f"Logs cleanup warning: {e}")


@pytest.fixture(scope="function")
def login_manager_factory():
    """
    Factory function that creates login managers using YOUR session.
    
    Returns a function that takes a GrpcSessionManager and returns LoginManager.
    """
    def create_login_manager_with_session(grpc_session_manager, enable_tapping=True):
        from test_framework.logging_manager.grpc_session_login_adapter import create_login_adapter
        from test_framework.logging_manager.login_manager import create_login_manager
        
        logger = get_logger("login_manager_factory")
        
        # Create adapter using the provided session
        adapter = create_login_adapter(grpc_session_manager)
        
        # Create login manager with the adapter
        login_mgr = create_login_manager(
            service_manager=adapter,
            station_id=grpc_session_manager.station_id,
            enable_tapping=enable_tapping
        )
        
        logger.info("✅ LoginManager created using provided gRPC session")
        return login_mgr
    
    return create_login_manager_with_session


# =============================================================================
# LAYER 4: CONVENIENCE (Sugar for common patterns)
# =============================================================================

@pytest.fixture(scope="function")
def grpc_with_user(grpc_session, test_config):
    """
    Convenience: gRPC session with user already setup.
    
    Uses the shared session and sets up the expected user.
    """
    logger = get_logger("grpc_with_user")
    
    expected_user = test_config["expected_user"]
    logger.info(f"Setting up user: {expected_user}")
    
    # Setup user on the shared session
    grpc_session.setup_user(expected_user, timeout=test_config.get("login_timeout", 30))
    logger.info(f"✅ User {expected_user} ready on shared session")
    
    yield grpc_session
    # Session cleanup handled by grpc_session fixture


@pytest.fixture(scope="function") 
def login_manager_with_session(login_manager_factory):
    """
    Convenience: Nice naming for the login manager factory.
    
    Returns the factory function with a user-friendly name.
    """
    return login_manager_factory


# =============================================================================
# HELPER: Get all needed fixtures for your test pattern
# =============================================================================

def get_test_fixtures():
    """
    Helper to show what fixtures are available for your test pattern:
    
    def test_login_timing(grpc_with_user, login_manager_with_session, 
                         logs_client, timing_calc, test_config, test_logger):
        # Your test here
    """
    return [
        "grpc_with_user",           # gRPC session with user setup
        "login_manager_with_session",  # Factory for login manager
        "logs_client",              # Log streaming client  
        "timing_calc",              # Timing calculator
        "test_config",              # Configuration (from config_fixtures)
        "test_logger"               # Logger (from logging_fixtures)
    ]