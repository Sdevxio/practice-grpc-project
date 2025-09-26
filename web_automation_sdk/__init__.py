#!/usr/bin/env python3
"""
Web Automation SDK - Comprehensive browser automation framework using Playwright.

This module provides a complete web automation SDK with:
- Thin server, rich client architecture (3 core gRPC methods)
- Browser session management and user isolation
- High-level convenience methods for common web operations
- Playwright-powered browser automation
- Multi-user context support via gRPC routing

Main Components:
    WebAutomationClient: Core gRPC client for server communication (client/)
    WebAutomationHelper: Rich convenience methods for complex operations (helpers/) 
    WebAutomationRegistry: Configuration and session management (registry/)
    WebAutomationUtils: Utilities and common operations (utils/)

Example Usage:
    from web_automation_sdk import WebAutomationClient, WebAutomationHelper
    from web_automation_sdk.helpers import navigation, forms, testing
    
    # Basic client usage (direct gRPC calls)
    client = WebAutomationClient("user")
    client.connect()
    client.execute_script("window.open('https://example.com')")
    screenshot = client.take_screenshot()
    page_info = client.get_page_info()
    
    # Rich helper usage (high-level operations)
    helper = WebAutomationHelper(client)
    helper.navigate_to_url("https://example.com")
    helper.fill_form({"username": "test", "password": "secret"})
    helper.wait_for_element(".submit-button")
    helper.click_element(".submit-button")
    
    # Specialized modules
    navigation.smart_navigate(helper, "https://example.com", wait_for="networkidle")
    forms.smart_fill_form(helper, form_data, submit=True)
    testing.assert_page_title(helper, "Expected Title")
"""

# Core client and helper exports
from .client.web_automation_client import WebAutomationClient
from .helpers.web_automation_helper import WebAutomationHelper
from .registry.web_automation_registry import WebAutomationRegistry

# Specialized helper modules available for import
from . import helpers

__all__ = [
    'WebAutomationClient',
    'WebAutomationHelper', 
    'WebAutomationRegistry',
    'helpers'
]
