"""
Test the new domain-specific fixture architecture.
"""

import datetime
import pytest


def test_config_fixture(test_config):
    """Test that test_config fixture works."""
    assert "station_id" in test_config
    assert "expected_user" in test_config
    assert "log_file_path" in test_config


def test_session_manager_fixture(session_manager, test_config):
    """Test that session_manager fixture works."""
    assert session_manager is not None
    assert session_manager.station_id == test_config["station_id"]


def test_authenticated_session_fixture(authenticated_session, test_config):
    """Test that authenticated_session fixture works."""
    assert authenticated_session is not None
    assert hasattr(authenticated_session, 'station_id')


def test_monitoring_workflow(monitoring_ready_workflow, test_logger):
    """Test monitoring_ready_workflow fixture."""
    workflow = monitoring_ready_workflow()
    
    assert "event_monitor_factory" in workflow
    assert "log_file_path" in workflow
    assert "config" in workflow
    assert "session_factory" in workflow
    
    test_logger.info("Monitoring workflow test completed")


def test_session_first_workflow(session_first_workflow, test_logger):
    """Test session_first_workflow fixture."""
    workflow = session_first_workflow()
    
    assert "session_manager" in workflow
    assert "config" in workflow
    assert "event_monitor_factory" in workflow
    assert "hardware_factory" in workflow
    
    test_logger.info("Session first workflow test completed")


def test_clean_state_workflow(clean_state_workflow, test_logger):
    """Test clean_state_workflow fixture."""
    workflow = clean_state_workflow()
    
    assert workflow["clean_state_confirmed"] is True
    assert "config" in workflow
    assert "session_manager" in workflow
    assert "event_monitor_factory" in workflow
    
    test_logger.info("Clean state workflow test completed")