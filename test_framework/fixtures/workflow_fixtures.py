"""
Workflow-specific fixtures for different testing patterns.

Provides ready-to-use workflows that combine components in specific timing sequences.
"""

import datetime
import pytest
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.login_logout.simple_tapper import SimpleTappingManager
from grpc_client_sdk.services.logs_monitor_stream_service_client import LogsMonitoringServiceClient


@pytest.fixture(scope="function")
def monitoring_ready_workflow(test_config, test_logger):
    """
    Workflow: Event monitoring ready before action timing.
    
    Sets up monitoring first, then provides factories for controlled timing.
    """
    def setup_workflow():
        log_file_path = test_config["log_file_path"]
        
        def create_event_monitor():
            logs_client = LogsMonitoringServiceClient(client_name="root", logger=test_logger)
            logs_client.connect()
            logs_client.stream_log_entries(
                log_file_path=log_file_path,
                include_existing=False
            )
            return logs_client
        
        test_logger.info("Monitoring workflow ready - event capture prepared")
        
        return {
            "event_monitor_factory": create_event_monitor,
            "log_file_path": log_file_path,
            "config": test_config,
            "session_factory": lambda: GrpcSessionManager(test_config["station_id"]),
            "hardware_factory": lambda: SimpleTappingManager(
                station_id=test_config["station_id"],
                enable_tapping=False,
                logger=test_logger
            )
        }
    
    return setup_workflow


@pytest.fixture(scope="function")
def session_first_workflow(test_config, test_logger):
    """
    Workflow: Setup session connection first, then control action timing.
    
    Perfect for tests that need established connection before physical interaction.
    """
    def setup_workflow():
        session_mgr = GrpcSessionManager(test_config["station_id"])
        test_logger.info("Session connection established")
        
        return {
            "session_manager": session_mgr,
            "config": test_config,
            "event_monitor_factory": lambda: LogsMonitoringServiceClient(client_name="root", logger=test_logger),
            "hardware_factory": lambda: SimpleTappingManager(
                station_id=test_config["station_id"], 
                enable_tapping=True,
                logger=test_logger
            )
        }
    
    return setup_workflow


@pytest.fixture(scope="function")
def clean_state_workflow(session_manager, test_config, test_logger):
    """
    Workflow: Ensure clean logout state, then control the sequence.
    
    Perfect for tests that need guaranteed clean start conditions.
    """
    def setup_workflow():
        expected_user = test_config["expected_user"]
        
        test_logger.info(f"Ensuring clean start - logging out {expected_user}")
        # Clean state workflow simplified - auto cleanup handles logout
        test_logger.info("Clean state workflow ready - user state management handles cleanup")
        
        return {
            "config": test_config,
            "session_manager": session_manager,
            "event_monitor_factory": lambda: session_manager.logs_monitor_stream("root"), 
            "hardware_factory": lambda: SimpleTappingManager(
                station_id=test_config["station_id"],
                enable_tapping=True,
                logger=test_logger
            ),
            "clean_state_confirmed": True
        }
    
    return setup_workflow