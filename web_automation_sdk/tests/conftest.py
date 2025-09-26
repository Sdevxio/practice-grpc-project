import pytest
from unittest.mock import Mock, MagicMock

from web_automation_sdk.client.web_automation_client import WebAutomationClient
from web_automation_sdk.helpers.web_automation_helper import WebAutomationHelper
from web_automation_sdk.registry.web_automation_registry import WebAutomationRegistry


@pytest.fixture
def mock_client():
    """Mock WebAutomationClient for testing."""
    client = Mock(spec=WebAutomationClient)
    client.client_name = "test"
    client.target_user = "test_user"
    client.is_connected.return_value = True
    
    # Mock successful responses for core methods
    client.execute_script.return_value = {
        "success": True,
        "message": "Script executed successfully",
        "result_value": "test result",
        "execution_time_ms": 100,
        "console_output": [],
        "metadata": {}
    }
    
    client.take_screenshot.return_value = {
        "success": True,
        "message": "Screenshot captured successfully",
        "image_data": b"fake_image_data",
        "width": 1920,
        "height": 1080,
        "format": "png",
        "file_size": 1024,
        "timestamp": 1640995200,
        "execution_time_ms": 200
    }
    
    client.get_page_info.return_value = {
        "success": True,
        "message": "Page info retrieved successfully",
        "page_info": {
            "url": "https://example.com",
            "title": "Test Page"
        },
        "structured_data": {
            "viewport_size": {
                "json_data": '{"width": 1920, "height": 1080}',
                "data_type": "viewport",
                "metadata": {"width": "1920", "height": "1080"}
            }
        },
        "execution_time_ms": 50
    }
    
    client.get_client_info.return_value = {
        "client_name": "test",
        "target_user": "test_user", 
        "connected": "True"
    }
    
    return client


@pytest.fixture
def web_automation_client():
    """Create a real WebAutomationClient instance for integration testing."""
    client = WebAutomationClient(client_name="test", target_user="test_user")
    # Note: connect() should be called manually in tests that need it
    return client


@pytest.fixture
def web_automation_helper(mock_client):
    """Create WebAutomationHelper with mocked client."""
    return WebAutomationHelper(mock_client)


@pytest.fixture
def web_automation_registry():
    """Create WebAutomationRegistry for testing."""
    return WebAutomationRegistry()


@pytest.fixture
def sample_session_config():
    """Sample session configuration for testing."""
    return {
        "browser": "chromium",
        "headless": True,
        "viewport": {"width": 1920, "height": 1080},
        "timeout": 30000
    }


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        "#username": "test_user",
        "#password": "test_password",
        "#email": "test@example.com"
    }