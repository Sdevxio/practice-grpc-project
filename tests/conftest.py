
# Import the centralized login_tester fixture
pytest_plugins = [
    "test_framework.fixture.session_fixtures",
    "test_framework.fixture.login_state_fixtures",
    "test_framework.fixture.config_fixtures",
    "test_framework.fixture.logging_fixtures"
]
