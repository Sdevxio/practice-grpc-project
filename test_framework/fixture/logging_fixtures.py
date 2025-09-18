import datetime
import os
import pytest
from test_framework.utils import set_test_case, get_logger, LoggerManager
from test_framework.utils.logger_settings.logger_config import LoggerConfig

# Global run ID for the test session
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging with run ID and environment information."""
    LoggerConfig.initialize()
    log_manager = LoggerManager()
    environment = os.environ.get("TEST_ENVIRONMENT", "test")
    log_manager.set_environment(environment)
    pytest.run_id = RUN_ID
    return log_manager


@pytest.fixture(scope="function")
def test_logger(request, setup_logging):
    """Fixture that provides a logger configured with the test name."""
    test_name = request.node.name
    set_test_case(test_name)
    logger = get_logger(f"test.{test_name}")

    # Generate unique correlation ID per test execution
    import uuid
    correlation_id = f"{RUN_ID[:8]}-{str(uuid.uuid4())[:8]}"
    setup_logging.set_correlation_id(correlation_id)

    # Store correlation ID on request node for other fixtures to access
    request.node.correlation_id = correlation_id
    logger.debug(f"Test correlation ID: {correlation_id}")

    yield logger

    passed = True
    if hasattr(request.node, 'rep_call'):
        passed = not request.node.rep_call.failed
    if passed:
        logger.info(f"Test passed: {test_name}")
    else:
        logger.error(f"Test failed: {test_name}")