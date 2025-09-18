import pytest
from test_framework.login_state.applescript_logout import AppleScriptLogoutManager
from test_framework.utils import get_logger

@pytest.fixture(scope="function")
def applescript_logout_manager(request):
    """Fixture to provide an AppleScriptLogoutManager instance with a test-specific logger."""
    test_name = request.node.name
    logger = get_logger(f"test.{test_name}.applescript_logout")
    return AppleScriptLogoutManager(logger=logger)

