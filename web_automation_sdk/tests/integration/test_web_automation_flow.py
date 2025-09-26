"""
Integration tests for WebAutomation SDK complete workflows.

These tests verify the complete integration between the WebAutomation SDK
components and the EAM gRPC server's WebAutomationService. They test
real-world scenarios that combine multiple operations.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

class TestWebAutomationIntegration:
    """Test complete web automation workflows."""
    
    def test_basic_navigation_workflow(self, web_automation_helper):
        """Test basic navigation and page interaction workflow."""
        helper = web_automation_helper
        
        # Mock the underlying client methods to return expected values
        helper.client.execute_script.side_effect = [
            # navigate_to_url call
            {"success": True, "result_value": "", "execution_time_ms": 100, "console_output": [], "metadata": {}},
            # wait_for_page_load call  
            {"success": True, "result_value": "true", "execution_time_ms": 50, "console_output": [], "metadata": {}},
        ]
        
        # Navigate to URL
        result = helper.navigate_to_url("https://google.com")
        assert result is True
        
        # Verify client calls were made correctly
        assert helper.client.execute_script.call_count == 2
        
        # Check navigation call
        nav_call = helper.client.execute_script.call_args_list[0]
        assert "window.location.href = 'https://google.com'" in nav_call[0][0]

        # Check wait for page load call
        load_call = helper.client.execute_script.call_args_list[1]
        assert "document.readyState === 'complete'" in load_call[0][0]

    def test_form_filling_workflow(self, web_automation_helper, sample_form_data):
        """Test form filling and submission workflow."""
        helper = web_automation_helper
        
        # Mock element exists and form filling
        helper.client.execute_script.side_effect = [
            # element_exists calls for each field
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # type_text calls for each field  
            {"success": True, "result_value": "true", "execution_time_ms": 50, "console_output": [], "metadata": {}},
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            {"success": True, "result_value": "true", "execution_time_ms": 50, "console_output": [], "metadata": {}},
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            {"success": True, "result_value": "true", "execution_time_ms": 50, "console_output": [], "metadata": {}},
            # element_exists for submit button
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # click submit button
            {"success": True, "result_value": "true", "execution_time_ms": 100, "console_output": [], "metadata": {}},
        ]
        
        # Fill form with submission
        result = helper.fill_form(sample_form_data, submit=True)
        assert result is True
        
        # Verify all fields were processed
        script_calls = helper.client.execute_script.call_args_list
        
        # Should have calls for: wait_for_element + type_text for each field + submit button interaction
        assert len(script_calls) >= len(sample_form_data) * 2
        
        # Verify username field was filled
        username_calls = [call for call in script_calls if "#username" in str(call)]
        assert len(username_calls) >= 2  # wait_for_element + type_text
    
    def test_element_interaction_workflow(self, web_automation_helper):
        """Test element interaction workflow (click, type, verify)."""
        helper = web_automation_helper
        
        # Mock element interactions
        helper.client.execute_script.side_effect = [
            # wait_for_element (element exists)
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # click_element
            {"success": True, "result_value": "true", "execution_time_ms": 100, "console_output": [], "metadata": {}},
            # wait_for_element for input
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # type_text
            {"success": True, "result_value": "true", "execution_time_ms": 80, "console_output": [], "metadata": {}},
            # get_element_text
            {"success": True, "result_value": "test_text", "execution_time_ms": 20, "console_output": [], "metadata": {}},
        ]
        
        # Perform element interactions
        click_result = helper.click_element(".login-button")
        assert click_result is True
        
        type_result = helper.type_text("#search-input", "test query")
        assert type_result is True
        
        text_result = helper.get_element_text(".result-text")
        assert text_result == "test_text"
        
        # Verify interaction calls
        assert helper.client.execute_script.call_count == 5
    
    def test_screenshot_and_verification_workflow(self, web_automation_helper):
        """Test screenshot capture and visual verification workflow."""
        helper = web_automation_helper
        
        # Mock page info and screenshot
        helper.client.get_page_info.return_value = {
            "success": True,
            "message": "Page info retrieved",
            "page_info": {"title": "Dashboard", "url": "https://google.com"},
            "structured_data": {},
            "execution_time_ms": 50
        }
        
        helper.client.take_screenshot.return_value = {
            "success": True,
            "message": "Screenshot captured",
            "image_data": b"fake_screenshot_data",
            "width": 1920,
            "height": 1080,
            "format": "png",
            "file_size": 2048,
            "timestamp": 1640995200,
            "execution_time_ms": 200
        }
        
        # Get page title for verification
        title = helper.get_page_title()
        assert title == "Dashboard"
        
        # Take screenshot
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            success = helper.client.save_screenshot_to_file("/tmp/test.png")
            assert success is True
            
            # Verify file was written
            mock_file.write.assert_called_once_with(b"fake_screenshot_data")
        
        # Verify page title matches expected
        title_match = helper.compare_page_title("Dashboard", exact_match=True)
        assert title_match is True
    
    def test_waiting_and_synchronization_workflow(self, web_automation_helper):
        """Test waiting and synchronization operations."""
        helper = web_automation_helper
        
        # Mock waiting operations with progressive responses
        helper.client.execute_script.side_effect = [
            # First wait_for_element call - element not found
            {"success": True, "result_value": "false", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # Second wait_for_element call - element found
            {"success": True, "result_value": "true", "execution_time_ms": 10, "console_output": [], "metadata": {}},
            # get_element_text - initial text
            {"success": True, "result_value": "Loading...", "execution_time_ms": 15, "console_output": [], "metadata": {}},
            # get_element_text - final text
            {"success": True, "result_value": "Welcome to Dashboard", "execution_time_ms": 15, "console_output": [], "metadata": {}},
        ]
        
        # Patch time.sleep to speed up tests
        with patch('time.sleep'):
            # Wait for element to appear (should succeed on second try)
            element_appeared = helper.wait_for_element(".dynamic-content", timeout=2000)
            assert element_appeared is True
            
            # Wait for specific text (should succeed on second try)
            text_appeared = helper.wait_for_text(".status", "Welcome", timeout=2000)
            assert text_appeared is True
        
        # Verify multiple attempts were made
        assert helper.client.execute_script.call_count == 4


class TestWebAutomationRegistry:
    """Test WebAutomationRegistry functionality."""
    
    def test_session_lifecycle(self, web_automation_registry, sample_session_config):
        """Test complete session lifecycle management."""
        registry = web_automation_registry
        
        # Register session
        session_id = registry.register_session(
            "test_session", 
            sample_session_config,
            user="test_user",
            metadata={"test": "data"}
        )
        assert session_id == "test_session"
        
        # Get session
        session = registry.get_session(session_id)
        assert session is not None
        assert session["user"] == "test_user"
        assert session["config"]["browser"] == "chromium"
        assert session["metadata"]["test"] == "data"
        
        # Record operations
        registry.record_operation(session_id, "script", 100, success=True)
        registry.record_operation(session_id, "screenshot", 200, success=True)
        registry.record_operation(session_id, "page_info", 50, success=True)
        
        # Get session metrics
        metrics = registry.get_session_metrics(session_id)
        assert metrics["script_executions"] == 1
        assert metrics["screenshots_taken"] == 1
        assert metrics["page_info_requests"] == 1
        assert metrics["total_execution_time"] == 350
        
        # Clean up session
        cleanup_result = registry.cleanup_session(session_id)
        assert cleanup_result is True
        
        # Verify session is removed
        session_after_cleanup = registry.get_session(session_id)
        assert session_after_cleanup is None
    
    def test_configuration_templates(self, web_automation_registry):
        """Test configuration template system."""
        registry = web_automation_registry
        
        # Get default template
        default_config = registry.get_configuration_template("default")
        assert default_config is not None
        assert default_config["browser"] == "chromium"
        assert default_config["headless"] is True
        
        # Get mobile template
        mobile_config = registry.get_configuration_template("mobile")
        assert mobile_config is not None
        assert mobile_config["viewport"]["width"] == 375
        
        # Create session from template
        session_id = registry.create_session_from_template(
            "mobile_session",
            "mobile", 
            user="mobile_user",
            config_overrides={"headless": False}
        )
        assert session_id == "mobile_session"
        
        # Verify session uses template with overrides
        session = registry.get_session(session_id)
        assert session["config"]["viewport"]["width"] == 375  # From template
        assert session["config"]["headless"] is False  # Override applied
        assert session["metadata"]["template"] == "mobile"
    
    def test_metrics_and_reporting(self, web_automation_registry):
        """Test metrics collection and reporting."""
        registry = web_automation_registry
        
        # Create multiple sessions
        registry.register_session("session1", {"browser": "chromium"}, user="user1")
        registry.register_session("session2", {"browser": "chromium"}, user="user2")
        
        # Record various operations
        registry.record_operation("session1", "script", 150, success=True)
        registry.record_operation("session1", "screenshot", 300, success=False)
        registry.record_operation("session2", "page_info", 75, success=True)
        
        # Test global metrics
        global_metrics = registry.get_global_metrics()
        assert global_metrics["total_sessions"] == 2
        assert global_metrics["active_sessions"] == 2
        assert global_metrics["average_execution_time"] == (150 + 300 + 75) / 3
        assert global_metrics["success_rate"] == 2/3  # 2 success out of 3 operations
        
        # Test session listing
        active_sessions = registry.list_active_sessions()
        assert len(active_sessions) == 2
        assert any(s["user"] == "user1" for s in active_sessions)
        assert any(s["user"] == "user2" for s in active_sessions)
        
        # Test metrics export
        export_data = registry.export_metrics()
        assert isinstance(export_data, str)
        
        # Parse and verify exported data
        exported = json.loads(export_data)
        assert "global_metrics" in exported
        assert "active_sessions" in exported
        assert "session_metrics" in exported


class TestWebAutomationClientIntegration:
    """Test WebAutomationClient integration scenarios."""
    
    @pytest.mark.integration
    def test_client_connection_workflow(self, web_automation_client):
        """Test client connection and basic operations."""
        client = web_automation_client
        
        # Note: This test would require actual gRPC server running
        # For now, we'll mock the connection
        with patch.object(client, 'stub') as mock_stub:
            # Mock connection
            client.stub = mock_stub
            
            # Test connection check
            assert client.is_connected() is True
            
            # Test client info
            info = client.get_client_info()
            assert info["client_name"] == "test"
            assert info["target_user"] == "test_user"
            assert info["connected"] == "True"
    
    def test_error_handling_workflow(self, web_automation_helper):
        """Test error handling in helper workflows."""
        helper = web_automation_helper
        
        # Mock client to return errors
        helper.client.execute_script.side_effect = [
            {"success": False, "message": "Script execution failed", "result_value": "", "execution_time_ms": 0, "console_output": [], "metadata": {}},
            {"success": False, "message": "Element not found", "result_value": "", "execution_time_ms": 0, "console_output": [], "metadata": {}}
        ]
        
        # Test failed navigation
        nav_result = helper.navigate_to_url("https://invalid-url.com", wait_for_load=False)
        assert nav_result is False
        
        # Test failed element interaction
        click_result = helper.click_element(".non-existent-button")
        assert click_result is False
        
        # Verify error scenarios were handled gracefully
        assert helper.client.execute_script.call_count == 2


@pytest.mark.integration
class TestCompleteAutomationScenario:
    """Test complete automation scenarios that would be used in real testing."""
    
    def test_login_form_automation_scenario(self, web_automation_helper):
        """Test complete login form automation scenario."""
        helper = web_automation_helper
        
        # Mock successful login flow
        helper.client.execute_script.side_effect = [
            # navigate_to_url
            {"success": True, "result_value": "", "execution_time_ms": 200, "console_output": [], "metadata": {}},
            # wait_for_page_load
            {"success": True, "result_value": "true", "execution_time_ms": 100, "console_output": [], "metadata": {}},
            # wait_for_element username field
            {"success": True, "result_value": "true", "execution_time_ms": 50, "console_output": [], "metadata": {}},
            # type_text username
            {"success": True, "result_value": "true", "execution_time_ms": 80, "console_output": [], "metadata": {}},
            # wait_for_element password field  
            {"success": True, "result_value": "true", "execution_time_ms": 30, "console_output": [], "metadata": {}},
            # type_text password
            {"success": True, "result_value": "true", "execution_time_ms": 70, "console_output": [], "metadata": {}},
            # element_exists submit button
            {"success": True, "result_value": "true", "execution_time_ms": 20, "console_output": [], "metadata": {}},
            # click submit button
            {"success": True, "result_value": "true", "execution_time_ms": 120, "console_output": [], "metadata": {}},
            # wait_for_page_load after submit
            {"success": True, "result_value": "true", "execution_time_ms": 300, "console_output": [], "metadata": {}},
        ]
        
        # Mock page info for title verification
        helper.client.get_page_info.return_value = {
            "success": True,
            "page_info": {"title": "Dashboard - Welcome"},
            "structured_data": {},
            "execution_time_ms": 40
        }
        
        # Execute complete login scenario
        # 1. Navigate to login page
        nav_success = helper.navigate_to_url("https://google.com", wait_for_load=True)
        assert nav_success is True
        
        # 2. Fill login form
        login_data = {
            "#username": "test_user",
            "#password": "secure_password"
        }
        form_success = helper.fill_form(login_data, submit=True)
        assert form_success is True
        
        # 3. Wait for page load after login
        load_success = helper.wait_for_page_load()
        assert load_success is True
        
        # 4. Verify successful login by checking page title
        page_title = helper.get_page_title()
        assert "Dashboard" in page_title
        
        # Verify all expected operations were performed
        assert helper.client.execute_script.call_count == 9
        assert helper.client.get_page_info.call_count == 1

