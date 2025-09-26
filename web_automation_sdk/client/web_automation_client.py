from typing import Optional, Dict, Any, List

from generated import web_automation_service_pb2_grpc, web_automation_service_pb2
from generated.web_automation_service_pb2_grpc import WebAutomationServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class WebAutomationClient:
    """
    Core gRPC client for Web Automation Service using the thin server approach.
    
    This client provides direct access to the 3 core methods:
    - ExecuteScript: Execute JavaScript in browser contexts
    - TakeScreenshot: Capture browser screenshots 
    - GetPageInfo: Retrieve page information and metadata
    
    The client follows the same patterns as other SDK clients in the framework,
    providing a clean interface to the underlying gRPC service while handling
    connection management, error handling, and response parsing.
    
    Attributes:
        client_name (str): gRPC context identifier (e.g., "user", "root")
        target_user (str): Target user for multi-user routing
        logger: Logger instance for structured output
        stub: gRPC stub for WebAutomation service communication
    
    Usage:
        client = WebAutomationClient(client_name="user", target_user="test_user")
        client.connect()
        
        # Execute JavaScript
        result = client.execute_script("return document.title")
        print(result["result_value"])  # Page title
        
        # Take screenshot
        screenshot = client.take_screenshot(format="png")
        with open("page.png", "wb") as f:
            f.write(screenshot["image_data"])
        
        # Get page info
        page_info = client.get_page_info([PageInfoType.URL, PageInfoType.TITLE])
        print(page_info["page_info"]["url"])
    """

    def __init__(self, client_name: str = "user", target_user: str = "", logger: Optional[object] = None):
        """
        Initialize WebAutomationClient.
        
        :param client_name: Name of the gRPC client in GrpcClientManager
        :param target_user: Target user for multi-user agent routing
        :param logger: Custom logger instance. If None, a default logger is created
        """
        self.client_name = client_name
        self.target_user = target_user
        self.logger = logger or get_logger(f"service.web_automation.{client_name}")
        self.stub: Optional[WebAutomationServiceStub] = None

    def connect(self):
        """
        Establishes the gRPC connection and stub for WebAutomationService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, WebAutomationServiceStub)
        self.logger.debug(f"WebAutomation client connected for {self.client_name}")

    def execute_script(
            self,
            script: str,
            context_id: str = "",
            return_value: bool = True,
            timeout_ms: int = 30000,
            context_options: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute JavaScript in browser context.
        
        :param script: JavaScript code to execute
        :param context_id: Browser context ID (defaults to target_user or 'default')
        :param return_value: Whether to return the result of the script execution
        :param timeout_ms: Timeout for script execution in milliseconds
        :param context_options: Additional context options
        :return: Dictionary containing execution result, console output, etc.
        
        Example:
            # Get page title
            result = client.execute_script("return document.title")
            title = result["result_value"]
            
            # Click an element
            client.execute_script(
                "document.querySelector('.login-button').click()",
                return_value=False
            )
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing scripts.")

        try:
            # Use target_user as default context_id if not specified
            if not context_id:
                context_id = self.target_user or "default"

            # Prepare context options
            options = context_options or {}
            options["context_id"] = context_id

            request = web_automation_service_pb2.ScriptRequest(
                script=script,
                target_user=self.target_user,
                return_value=return_value,
                timeout_ms=timeout_ms,
                context_options=options
            )

            response = self.stub.ExecuteScript(request)

            result = {
                "success": response.success,
                "message": response.message,
                "result_value": response.result_value,
                "execution_time_ms": response.execution_time_ms,
                "console_output": list(response.console_output),
                "metadata": dict(response.metadata)
            }

            if not response.success:
                self.logger.warning(f"Script execution failed: {response.message}")
            else:
                self.logger.debug(f"Script executed successfully in {response.execution_time_ms}ms")

            return result

        except Exception as e:
            self.logger.error(f"Script execution failed: {str(e)}")
            return None

    def take_screenshot(
            self,
            format: str = "png",
            quality: int = 90,
            region: Optional[Dict[str, int]] = None,
            full_page: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Take screenshot of browser page or specific region.
        
        :param format: Image format ('png' or 'jpeg')
        :param quality: JPEG quality (1-100, only for jpeg format)
        :param region: Screenshot region as dict with x, y, width, height
        :param full_page: Whether to capture full page (vs. viewport only)
        :return: Dictionary containing image data and metadata
        
        Example:
            # Full page screenshot
            screenshot = client.take_screenshot()
            with open("page.png", "wb") as f:
                f.write(screenshot["image_data"])
            
            # Region screenshot
            region_screenshot = client.take_screenshot(
                region={"x": 0, "y": 0, "width": 800, "height": 600}
            )
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before taking screenshots.")

        try:
            request = web_automation_service_pb2.ScreenshotRequest(
                target_user=self.target_user,
                format=format,
                quality=quality,
                full_page=full_page
            )

            # Add region if specified
            if region:
                request.region.x = region["x"]
                request.region.y = region["y"]
                request.region.width = region["width"]
                request.region.height = region["height"]

            response = self.stub.TakeScreenshot(request)

            result = {
                "success": response.success,
                "message": response.message,
                "image_data": response.image_data,
                "width": response.width,
                "height": response.height,
                "format": response.format,
                "file_size": response.file_size,
                "timestamp": response.timestamp,
                "execution_time_ms": response.execution_time_ms
            }

            if not response.success:
                self.logger.warning(f"Screenshot failed: {response.message}")
            else:
                self.logger.debug(f"Screenshot captured: {response.width}x{response.height} {response.format}")

            return result

        except Exception as e:
            self.logger.error(f"Screenshot failed: {str(e)}")
            return None

    def get_page_info(
            self,
            info_types: Optional[List[web_automation_service_pb2.PageInfoType]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get page information and metadata.
        
        :param info_types: List of PageInfoType enums to retrieve
        :return: Dictionary containing page info and structured data
        
        Example:
            # Get basic page info
            page_info = client.get_page_info([
                PageInfoType.URL, 
                PageInfoType.TITLE,
                PageInfoType.VIEWPORT_SIZE
            ])
            
            url = page_info["page_info"]["url"]
            title = page_info["page_info"]["title"]
            viewport = json.loads(page_info["structured_data"]["viewport_size"]["json_data"])
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before getting page info.")

        try:
            # Default info types if none specified
            if info_types is None:
                info_types = [web_automation_service_pb2.PageInfoType.URL,
                              web_automation_service_pb2.PageInfoType.TITLE, web_automation_service_pb2.PageInfoType.VIEWPORT_SIZE]

            request = web_automation_service_pb2.PageInfoRequest(
                target_user=self.target_user,
                info_types=info_types
            )

            response = self.stub.GetPageInfo(request)

            # Convert structured data to regular dict for easier access
            structured_data = {}
            for key, data_obj in response.structured_data.items():
                structured_data[key] = {
                    "json_data": data_obj.json_data,
                    "data_type": data_obj.data_type,
                    "metadata": dict(data_obj.metadata)
                }

            result = {
                "success": response.success,
                "message": response.message,
                "page_info": dict(response.page_info),
                "structured_data": structured_data,
                "execution_time_ms": response.execution_time_ms
            }

            if not response.success:
                self.logger.warning(f"Get page info failed: {response.message}")
            else:
                self.logger.debug(f"Page info retrieved in {response.execution_time_ms}ms")

            return result

        except Exception as e:
            self.logger.error(f"Get page info failed: {str(e)}")
            return None

    def save_screenshot_to_file(
            self,
            filepath: str,
            format: str = "png",
            quality: int = 90,
            region: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Take screenshot and save directly to file.
        
        :param filepath: Path where to save the screenshot
        :param format: Image format ('png' or 'jpeg')
        :param quality: JPEG quality (1-100, only for jpeg format)
        :param region: Screenshot region as dict with x, y, width, height
        :return: True if saved successfully, False otherwise
        """
        screenshot = self.take_screenshot(format=format, quality=quality, region=region)

        if not screenshot or not screenshot["success"]:
            return False

        try:
            with open(filepath, "wb") as f:
                f.write(screenshot["image_data"])

            self.logger.info(f"Screenshot saved to: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save screenshot to {filepath}: {e}")
            return False

    def execute_script_from_file(
            self,
            script_file: str,
            context_id: str = "",
            return_value: bool = True,
            timeout_ms: int = 30000,
            context_options: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute JavaScript from a file.
        
        :param script_file: Path to JavaScript file
        :param context_id: Browser context ID
        :param return_value: Whether to return the result of the script execution
        :param timeout_ms: Timeout for script execution in milliseconds
        :param context_options: Additional context options
        :return: Dictionary containing execution result
        """
        try:
            with open(script_file, 'r') as f:
                script = f.read()

            return self.execute_script(
                script=script,
                context_id=context_id,
                return_value=return_value,
                timeout_ms=timeout_ms,
                context_options=context_options
            )

        except Exception as e:
            self.logger.error(f"Failed to execute script from file {script_file}: {e}")
            return None

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the gRPC service.
        
        :return: True if connected, False otherwise
        """
        return self.stub is not None

    def get_client_info(self) -> Dict[str, str]:
        """
        Get client configuration information.
        
        :return: Dictionary with client configuration details
        """
        return {
            "client_name": self.client_name,
            "target_user": self.target_user,
            "connected": str(self.is_connected())
        }
