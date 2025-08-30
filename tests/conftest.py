"""
Clean conftest.py using domain-specific fixture architecture.

Pure pytest infrastructure only - all fixtures moved to domain-specific modules.
"""

import os
import pytest

# Load domain-specific fixtures
pytest_plugins = [
    "test_framework.fixtures.logging_fixtures",
    "test_framework.fixtures.config_fixtures",
    "test_framework.fixtures.session_fixtures",
    "test_framework.fixtures.hardware_fixtures", 
    "test_framework.fixtures.workflow_fixtures",
    "test_framework.fixtures.user_state_fixtures",
]


# Command line options for hardware control
def pytest_addoption(parser):
    """Add command line options for hardware control."""
    options = [
        ("--no-tapping", "store_true", False, "Disable all tapping operations for local testing"),
        ("--tapping-debug", "store_true", False, "Enable debug logging for tapping operations")
    ]

    for option, action, default, help_text in options:
        parser.addoption(option, action=action, default=default, help=help_text)


@pytest.fixture(autouse=True)
def apply_hardware_options(request):
    """Apply hardware-specific command line options."""
    if request.config.getoption("--no-tapping"):
        os.environ["ENABLE_TAPPING"] = "false"

    if request.config.getoption("--tapping-debug"):
        _enable_tapping_debug_logging()


def _enable_tapping_debug_logging():
    """Enable debug logging for tapping-related loggers."""
    import logging
    tapping_loggers = ["login_tapper", "logoff_tapper", "tapping_manager"]
    for logger_name in tapping_loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Hook to capture test outcomes."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)