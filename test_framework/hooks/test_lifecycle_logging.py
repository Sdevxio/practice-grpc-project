import pytest
import traceback
from test_framework.utils import set_test_case, get_logger, LoggerManager


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Set test case name and mark start of test.
    """
    set_test_case(item.name)
    logger = get_logger("framework.test_hook.setup")
    logger.info(f"{'=' * 20} START TEST: {item.name} {'=' * 20}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    """
    Hook wrapper to capture full unhandled exceptions and write detailed failure logs.

    IMPORTANT: Uses hookwrapper=True to wrap the test execution rather than
    calling item.runtest() directly, which would cause double execution.
    """
    logger = get_logger("framework.test_hook.exception")

    # Let pytest run the test and capture the outcome
    outcome = yield

    try:
        # Get the result - this will raise if the test failed
        outcome.get_result()
    except Exception as e:
        # Test failed - log details
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"UNHANDLED TEST EXCEPTION:\n{tb}")

        # Write detailed failure file
        log_manager = LoggerManager()
        log_manager.failed_test_handler.create_failure_log_with_details(item.name, tb)

        # Don't suppress the exception - let it propagate
        raise


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """
    Hook to only track test phase outcomes (no failure file creation here anymore).
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "call" and rep.failed:
        logger = get_logger("framework.test_hook.failure")
        logger.error(f"Test '{item.name}' failed during {rep.when} phase.")


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item):
    """
    Marks test end in logs. No failure file creation.
    """
    logger = get_logger("framework.test_hook.teardown")
    logger.info(f"{'=' * 20} END TEST: {item.name} {'=' * 20}")