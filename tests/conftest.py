"""
Clean Test Framework Configuration

Single, simple conftest.py that loads clean fixtures with no duplication or conflicts.

Architecture:
- Layer 1: Foundation (config, logging, timing)
- Layer 2: Core (single grpc_session)  
- Layer 3: Services (logs_client, login_manager)
- Layer 4: Convenience (grpc_with_user, sugar)
"""

import pytest

# Load clean fixture modules - no duplication, clear hierarchy
pytest_plugins = [
    "test_framework.fixtures.config_fixtures",      # test_config
    "test_framework.fixtures.logging_fixtures",     # test_logger, setup_logging  
    "test_framework.fixtures.clean_fixtures",       # All clean fixtures
]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Hook to capture test outcomes for logging fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)