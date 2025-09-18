"""
Main conftest.py - Orchestrates modular fixtures architecture.

This file imports and registers all fixtures modules, providing a single entry point
for the test framework while maintaining clear separation of concerns.
"""
import pytest

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Hook to capture test outcomes for logging fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
