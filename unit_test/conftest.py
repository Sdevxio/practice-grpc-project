import pytest

# Clean unified fixture architecture - replaces multiple fixture files
pytest_plugins = [
    "test_framework.fixtures.config_fixtures",      # test_config
    "test_framework.fixtures.logging_fixtures",     # test_logger, setup_logging  
    "test_framework.fixtures.clean_fixtures",       # All unified fixtures
]

@pytest.fixture(scope="function")
def services(grpc_with_user, login_manager_with_session, test_config, test_logger):
    """
    Simplified services fixture using the unified clean architecture.
    
    Uses clean fixtures with single source of truth:
    - grpc_with_user: gRPC session with user already setup (from clean_fixtures)
    - login_manager_with_session: Factory for login manager (from clean_fixtures)  
    - Zero duplicate session creation

    Provides simple API:
        services.command("root").run_command("whoami")  # root-grpc-server
        services.command("admin").run_command("whoami") # user-agent server
        services.apple_script("admin").run_applescript("...")
        services.login_manager.ensure_logged_out("admin")
    """
    test_logger.info("✅ Unit test services using unified clean architecture")
    
    # Create login manager using the shared session
    login_mgr = login_manager_with_session(grpc_with_user, test_config.get("enable_tapping", True))

    # Create simplified services object using clean fixtures
    class Services:
        def __init__(self, session_manager, login_mgr):
            self.session_manager = session_manager
            self.login_manager = login_mgr
            self.expected_user = test_config["expected_user"]

        def command(self, context: str):
            """Get command service - routes to correct server"""
            return self.session_manager.command(context)

        def apple_script(self, context: str):
            """Get AppleScript service - routes to correct server"""
            return self.session_manager.apple_script(context)

        def file_transfer(self, context: str):
            """Get file transfer service - routes to correct server"""
            return self.session_manager.file_transfer(context)

        def screen_capture(self, context: str):
            """Get screen capture service - routes to correct server"""
            return self.session_manager.screen_capture(context)

        def logs_monitor_stream(self, context: str):
            """Get logs monitoring service - routes to correct server"""
            return self.session_manager.logs_monitor_stream(context)

        def grpc_connection(self, context: str):
            """Get connection service - routes to correct server"""
            return self.session_manager.grpc_connection(context)

        def health_check(self, context: str) -> bool:
            """Perform health check for context"""
            return self.session_manager.health_check(context)

        def get_current_user(self):
            """Get current logged in user"""
            return self.session_manager.get_current_user()

    services_obj = Services(grpc_with_user, login_mgr)
    test_logger.info(f"✅ Unit test services ready using clean architecture")
    
    yield services_obj
    
    # Cleanup handled by individual fixtures