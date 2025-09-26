import json
import time
from typing import Optional, Dict, Any

from generated import web_automation_service_pb2

from test_framework.utils import get_logger
from web_automation_sdk.client.web_automation_client import WebAutomationClient


def escape_js_string(value: str) -> str:
    """
    Escape a string for safe use in JavaScript code.
    
    :param value: String to escape
    :return: Escaped string safe for JavaScript
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Escape backslashes first, then quotes and other special characters
    return (value.replace('\\', '\\\\')
                 .replace("'", "\\'")
                 .replace('"', '\\"')
                 .replace('\n', '\\n')
                 .replace('\r', '\\r')
                 .replace('\t', '\\t'))


class WebAutomationHelper:
    """
    High-level convenience methods for web automation built on top of WebAutomationClient.
    
    This helper class provides rich, developer-friendly methods that combine the 3 core
    gRPC methods (ExecuteScript, TakeScreenshot, GetPageInfo) to perform complex web
    automation tasks. It follows the same patterns as other helper classes in the framework.
    
    The helper provides methods for:
    - Navigation and page management
    - Element interaction (clicking, typing, etc.)
    - Form handling and data entry
    - Waiting and synchronization
    - Visual testing and verification
    - Session and context management
    
    Attributes:
        client: WebAutomationClient instance for gRPC communication
        logger: Logger instance for structured output
        default_timeout: Default timeout for operations in milliseconds
        default_wait_time: Default wait time between operations in milliseconds
    
    Usage:
        client = WebAutomationClient("user", target_user="test_user")
        client.connect()
        
        helper = WebAutomationHelper(client)
        
        # Navigation
        helper.navigate_to_url("https://example.com")
        helper.wait_for_page_load()
        
        # Element interaction
        helper.click_element(".login-button")
        helper.type_text("#username", "test_user")
        
        # Form handling
        helper.fill_form({
            "#username": "test_user",
            "#password": "secret"
        })
        
        # Verification
        assert helper.get_page_title() == "Dashboard"
        assert helper.element_exists(".welcome-message")
    """
    
    def __init__(self, client: WebAutomationClient, logger: Optional[object] = None):
        """
        Initialize WebAutomationHelper with a client instance.
        
        :param client: WebAutomationClient instance for gRPC communication
        :param logger: Optional logger instance
        """
        self.client = client
        self.logger = logger or get_logger(f"helper.web_automation.{client.client_name}")
        self.default_timeout = 30000  # 30 seconds
        self.default_wait_time = 1000  # 1 second
        
        if not client.is_connected():
            raise RuntimeError("WebAutomationClient must be connected before creating helper")
    
    def _ensure_connected(self) -> bool:
        """
        Ensure the underlying client is connected to the gRPC service.

        :return: True if connected, False otherwise
        """
        if not self.client.is_connected():
            self.logger.error("WebAutomationClient is not connected. Call connect() before using helper methods.")
            return False
        return True

    # Navigation Methods
    def navigate_to_url(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navigate to a URL and optionally wait for page load.
        
        :param url: URL to navigate to
        :param wait_for_load: Whether to wait for page load completion
        :return: True if navigation succeeded, False otherwise
        """
        if not self._ensure_connected():
            return False
        script = f"window.location.href = '{escape_js_string(url)}'"
        result = self.client.execute_script(script, return_value=False)
        
        if not result or not result["success"]:
            self.logger.error(f"Failed to navigate to {url}")
            return False
        
        if wait_for_load:
            return self.wait_for_page_load()
        
        return True
    
    def reload_page(self, wait_for_load: bool = True) -> bool:
        """
        Reload the current page.
        
        :param wait_for_load: Whether to wait for page load completion
        :return: True if reload succeeded, False otherwise
        """
        result = self.client.execute_script("window.location.reload()", return_value=False)
        
        if not result or not result["success"]:
            self.logger.error("Failed to reload page")
            return False
        
        if wait_for_load:
            return self.wait_for_page_load()
        
        return True
    
    def go_back(self) -> bool:
        """
        Navigate back in browser history.
        
        :return: True if navigation succeeded, False otherwise
        """
        result = self.client.execute_script("window.history.back()", return_value=False)
        return result and result["success"]
    
    def go_forward(self) -> bool:
        """
        Navigate forward in browser history.
        
        :return: True if navigation succeeded, False otherwise
        """
        result = self.client.execute_script("window.history.forward()", return_value=False)
        return result and result["success"]
    
    # Element Interaction Methods
    def click_element(self, selector: str, wait_timeout: int = None) -> bool:
        """
        Click an element identified by CSS selector.
        
        :param selector: CSS selector for the element
        :param wait_timeout: Timeout to wait for element (uses default if None)
        :return: True if click succeeded, False otherwise
        """
        timeout = wait_timeout or self.default_timeout
        
        # Wait for element to exist and be clickable
        if not self.wait_for_element(selector, timeout):
            return False
        
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    if (element) {{
        element.click();
        return true;
    }}
    return false;
}})()
"""

        result = self.client.execute_script(script)
        if result and result["success"] and result["result_value"] == "true":
            self.logger.debug(f"Successfully clicked element: {selector}")
            return True
        
        self.logger.error(f"Failed to click element: {selector}")
        return False
    
    def type_text(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """
        Type text into an input element.
        
        :param selector: CSS selector for the input element
        :param text: Text to type
        :param clear_first: Whether to clear the input before typing
        :return: True if typing succeeded, False otherwise
        """
        if not self.wait_for_element(selector):
            return False
        
        clear_script = "element.value = '';" if clear_first else ""
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    if (element) {{
        element.focus();
        {clear_script}
        element.value = '{escape_js_string(text)}';
        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return true;
    }}
    return false;
}})()
"""

        result = self.client.execute_script(script)
        if result and result["success"] and result["result_value"] == "true":
            self.logger.debug(f"Successfully typed text into {selector}")
            return True
        
        self.logger.error(f"Failed to type text into {selector}")
        return False
    
    def get_element_text(self, selector: str) -> Optional[str]:
        """
        Get the text content of an element.
        
        :param selector: CSS selector for the element
        :return: Element text or None if not found
        """
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    return element ? element.textContent.trim() : null;
}})()
"""

        result = self.client.execute_script(script)
        if result and result["success"]:
            return result["result_value"] if result["result_value"] != "null" else None
        
        return None
    
    def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get an attribute value from an element.
        
        :param selector: CSS selector for the element
        :param attribute: Attribute name to retrieve
        :return: Attribute value or None if not found
        """
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    return element ? element.getAttribute('{escape_js_string(attribute)}') : null;
}})()
"""

        result = self.client.execute_script(script)
        if result and result["success"]:
            return result["result_value"] if result["result_value"] != "null" else None
        
        return None
    
    def element_exists(self, selector: str) -> bool:
        """
        Check if an element exists on the page.
        
        :param selector: CSS selector for the element
        :return: True if element exists, False otherwise
        """
        script = f"document.querySelector('{escape_js_string(selector)}') !== null"
        result = self.client.execute_script(script)
        return result and result["success"] and result["result_value"] == "true"
    
    def element_is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible on the page.
        
        :param selector: CSS selector for the element
        :return: True if element is visible, False otherwise
        """
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    if (!element) return false;
    const style = window.getComputedStyle(element);
    return style.display !== 'none' && \
           style.visibility !== 'hidden' && \
           element.offsetParent !== null;
}})()
"""

        result = self.client.execute_script(script)
        return result and result["success"] and result["result_value"] == "true"
    
    # Form Handling Methods
    def fill_form(self, form_data: Dict[str, str], submit: bool = False) -> bool:
        """
        Fill multiple form fields at once.
        
        :param form_data: Dictionary mapping selectors to values
        :param submit: Whether to submit the form after filling
        :return: True if all fields filled successfully, False otherwise
        """
        success = True
        
        for selector, value in form_data.items():
            if not self.type_text(selector, value):
                self.logger.error(f"Failed to fill field: {selector}")
                success = False
        
        if success and submit:
            # Try to find and click a submit button
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]', 
                '.submit-button',
                '.btn-submit',
                'button:contains("Submit")',
                'button:contains("Login")'
            ]
            
            for submit_selector in submit_selectors:
                if self.element_exists(submit_selector):
                    return self.click_element(submit_selector)
            
            self.logger.warning("Could not find submit button to click")
        
        return success
    
    def select_dropdown_option(self, selector: str, option_value: str) -> bool:
        """
        Select an option from a dropdown/select element.
        
        :param selector: CSS selector for the select element
        :param option_value: Value of the option to select
        :return: True if selection succeeded, False otherwise
        """
        script = f"""
(() => {{
    const select = document.querySelector('{escape_js_string(selector)}');
    if (select) {{
        select.value = '{escape_js_string(option_value)}';
        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return true;
    }}
    return false;
}})()
"""

        result = self.client.execute_script(script)
        return result and result["success"] and result["result_value"] == "true"
    
    # Waiting and Synchronization Methods
    def wait_for_element(self, selector: str, timeout: int = None) -> bool:
        """
        Wait for an element to exist on the page.
        
        :param selector: CSS selector for the element
        :param timeout: Timeout in milliseconds (uses default if None)
        :return: True if element appeared, False if timeout
        """
        timeout = timeout or self.default_timeout
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout:
            if self.element_exists(selector):
                return True
            time.sleep(self.default_wait_time / 1000.0)
        
        self.logger.warning(f"Element not found within {timeout}ms: {selector}")
        return False
    
    def wait_for_element_visible(self, selector: str, timeout: int = None) -> bool:
        """
        Wait for an element to be visible on the page.
        
        :param selector: CSS selector for the element
        :param timeout: Timeout in milliseconds (uses default if None)
        :return: True if element became visible, False if timeout
        """
        timeout = timeout or self.default_timeout
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout:
            if self.element_is_visible(selector):
                return True
            time.sleep(self.default_wait_time / 1000.0)
        
        self.logger.warning(f"Element not visible within {timeout}ms: {selector}")
        return False
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """
        Wait for page to finish loading.
        
        :param timeout: Timeout in milliseconds (uses default if None)
        :return: True if page loaded, False if timeout
        """
        timeout = timeout or self.default_timeout
        
        script = "document.readyState === 'complete' && (!window.jQuery || jQuery.active === 0)"

        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout:
            result = self.client.execute_script(script)
            if result and result["success"] and result["result_value"] == "true":
                return True
            time.sleep(self.default_wait_time / 1000.0)
        
        self.logger.warning(f"Page did not finish loading within {timeout}ms")
        return False
    
    def wait_for_text(self, selector: str, expected_text: str, timeout: int = None) -> bool:
        """
        Wait for an element to contain specific text.
        
        :param selector: CSS selector for the element
        :param expected_text: Text to wait for
        :param timeout: Timeout in milliseconds (uses default if None)
        :return: True if text appeared, False if timeout
        """
        timeout = timeout or self.default_timeout
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout:
            current_text = self.get_element_text(selector)
            if current_text and expected_text in current_text:
                return True
            time.sleep(self.default_wait_time / 1000.0)
        
        self.logger.warning(f"Text '{expected_text}' not found in {selector} within {timeout}ms")
        return False
    
    # Page Information Methods
    def get_page_title(self) -> Optional[str]:
        """
        Get the current page title.
        
        :return: Page title or None if retrieval failed
        """
        page_info = self.client.get_page_info([web_automation_service_pb2.PageInfoType.TITLE])
        if page_info and page_info["success"]:
            return page_info["page_info"].get("title")
        return None

    def get_page_url(self) -> Optional[str]:
        """
        Get the current page URL.
        
        :return: Page URL or None if retrieval failed
        """
        page_info = self.client.get_page_info([web_automation_service_pb2.PageInfoType.URL])
        if page_info and page_info["success"]:
            return page_info["page_info"].get("url")
        return None

    def get_viewport_size(self) -> Optional[Dict[str, int]]:
        """
        Get the current viewport size.
        
        :return: Dictionary with width and height, or None if retrieval failed
        """
        page_info = self.client.get_page_info([web_automation_service_pb2.PageInfoType.VIEWPORT_SIZE])
        if page_info and page_info["success"]:
            viewport_data = page_info["structured_data"].get("viewport_size")
            if viewport_data:
                return json.loads(viewport_data["json_data"])
        return None
    
    # Visual Testing Methods
    def take_element_screenshot(self, selector: str, filepath: str = None) -> Optional[bytes]:
        """
        Take a screenshot of a specific element.
        
        :param selector: CSS selector for the element
        :param filepath: Optional path to save screenshot
        :return: Screenshot bytes or None if failed
        """
        # Get element bounds
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    if (element) {{
        const rect = element.getBoundingClientRect();
        return JSON.stringify({{
            x: Math.round(rect.x),
            y: Math.round(rect.y), 
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        }});
    }}
    return null;
}})()
"""

        result = self.client.execute_script(script)
        if not result or not result["success"] or result["result_value"] == "null":
            self.logger.error(f"Could not get bounds for element: {selector}")
            return None
        
        try:
            bounds = json.loads(result["result_value"])
            
            # Validate bounds to prevent Playwright errors
            if bounds.get("width", 0) <= 0 or bounds.get("height", 0) <= 0:
                self.logger.error(f"Invalid element bounds for {selector}: {bounds}")
                return None
            
            screenshot = self.client.take_screenshot(region=bounds)
            
            if screenshot and screenshot["success"]:
                image_data = screenshot["image_data"]
                
                if filepath:
                    with open(filepath, "wb") as f:
                        f.write(image_data)
                    self.logger.info(f"Element screenshot saved to: {filepath}")
                
                return image_data
                
        except Exception as e:
            self.logger.error(f"Failed to take element screenshot: {e}")
        
        return None
    
    def compare_page_title(self, expected_title: str, exact_match: bool = True) -> bool:
        """
        Compare the current page title with expected title.
        
        :param expected_title: Expected page title
        :param exact_match: Whether to do exact match or substring match
        :return: True if titles match, False otherwise
        """
        current_title = self.get_page_title()
        if not current_title:
            return False
        
        if exact_match:
            return current_title == expected_title
        else:
            return expected_title in current_title
    
    # Utility Methods
    def scroll_to_element(self, selector: str) -> bool:
        """
        Scroll to bring an element into view.
        
        :param selector: CSS selector for the element
        :return: True if scrolling succeeded, False otherwise
        """
        script = f"""
(() => {{
    const element = document.querySelector('{escape_js_string(selector)}');
    if (element) {{
        element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        return true;
    }}
    return false;
}})()
"""

        result = self.client.execute_script(script)
        return result and result["success"] and result["result_value"] == "true"
    
    def scroll_to_top(self) -> bool:
        """
        Scroll to the top of the page.
        
        :return: True if scrolling succeeded, False otherwise
        """
        result = self.client.execute_script("window.scrollTo(0, 0); true;")
        return result and result["success"]
    
    def scroll_to_bottom(self) -> bool:
        """
        Scroll to the bottom of the page.
        
        :return: True if scrolling succeeded, False otherwise
        """
        script = "window.scrollTo(0, document.body.scrollHeight); true;"
        result = self.client.execute_script(script)
        return result and result["success"]
    
    def execute_custom_script(self, script: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute custom JavaScript with helper context.
        
        :param script: JavaScript code to execute
        :param kwargs: Additional parameters for script execution
        :return: Script execution result
        """
        return self.client.execute_script(
            script=script,
            timeout_ms=kwargs.get('timeout_ms', self.default_timeout),
            context_id=kwargs.get('context_id', ''),
            return_value=kwargs.get('return_value', True),
            context_options=kwargs.get('context_options')
        )
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about the underlying client and helper configuration.
        
        :return: Dictionary with client and helper info
        """
        client_info = self.client.get_client_info()
        client_info.update({
            "helper_default_timeout": str(self.default_timeout),
            "helper_default_wait_time": str(self.default_wait_time)
        })
        return client_info
