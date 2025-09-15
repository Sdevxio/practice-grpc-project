from typing import Optional, Dict, Any

import requests

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from tappers_service.tapper_system.utils import (
    TapperConnectionError,
    TapperTimeoutError,
    TapperProtocolError
)


class HTTPTapperProtocol(BaseProtocol):
    """
    HTTP-based tapper communication protocol.

    Communicates with ESP32 tapper devices via REST API.
    Supports:
      - Stateless command execution (GET or POST)
      - Status polling (/status)
      - Optional health checks (/ping)

    Attributes:
        base_url (str): Device's HTTP endpoint.
        timeout (int): Request timeout in seconds.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize from config (requires 'base_url').

        :param config: Configuration dictionary for the device.
        """
        super().__init__(device_id=config.get("device_id", "http_device"), config=config)
        self.base_url = config.get("base_url")
        if not self.base_url:
            raise ValueError("Missing 'base_url' in HTTP protocol config.")
        self.timeout = config.get("timeout", 2)
        self._connected = True  # Always considered connected

    def connect(self) -> bool:
        """No-op for HTTP (always connected)."""
        self.logger.debug("HTTP protocol is stateless - connect() is a no-op.")
        self._connected = True
        return True

    def disconnect(self) -> None:
        """No-op for HTTP (stateless)."""
        self._connected = False
        self.logger.debug("HTTP protocol is stateless - disconnect() is a no-op.")

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send command via GET or POST.

        :param command: Action to execute (e.g., 'tap').
        :param params: Optional parameters (used with POST).
        :return: Parsed response content or raises exception.
        """
        try:
            if params:
                payload = {"action": command}
                payload.update(params)
                self.logger.debug(f"Sending POST to /command with: {payload}")  # Changed from INFO to DEBUG
                response = requests.post(f"{self.base_url}/command", json=payload, timeout=self.timeout)
            else:
                self.logger.debug(f"Sending GET to /{command}")  # Changed from INFO to DEBUG
                response = requests.get(f"{self.base_url}/{command}", timeout=self.timeout)

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            result = response.json() if "application/json" in content_type else response.text
            self.logger.debug(f"Command '{command}' response: {result}")
            return result

        except requests.exceptions.ConnectTimeout as e:
            raise TapperTimeoutError(
                f"Command '{command}' timed out",
                timeout_duration=self.timeout,
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

        except requests.exceptions.ReadTimeout as e:
            raise TapperTimeoutError(
                f"Command '{command}' read timeout",
                timeout_duration=self.timeout,
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

        except requests.exceptions.ConnectionError as e:
            error_str = str(e).lower()
            if "refused" in error_str:
                error_type = "Connection refused - device reachable but HTTP server not running"
            elif "timeout" in error_str:
                error_type = "Connection timeout - device not responding"
            else:
                error_type = "Connection error"

            raise TapperConnectionError(
                f"Cannot connect to send command '{command}': {error_type}",
                device_id=self.device_id,
                protocol="HTTP",
                connection_details={"base_url": self.base_url, "error": str(e)}
            ) from e

        except requests.exceptions.HTTPError as e:
            raise TapperProtocolError(
                f"HTTP error for command '{command}': {e.response.status_code} {e.response.reason}",
                command=command,
                response=f"{e.response.status_code} {e.response.reason}",
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

        except Exception as e:
            self.logger.error(f"HTTP error sending command '{command}': {e}")
            raise TapperProtocolError(
                f"Unexpected error sending command '{command}'",
                command=command,
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

    def get_status(self) -> str:
        """
        Retrieve the current state of the tapper from /status.

        :return str: Status text or 'unknown' on failure.
        """
        try:
            self.logger.debug(f"Getting status from {self.base_url}/status")  # Added debug logging
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            response.raise_for_status()
            status = response.text.strip()
            self.logger.debug(f"Tapper status: {status}")
            return status

        except requests.exceptions.ConnectTimeout as e:
            raise TapperTimeoutError(
                "Status request timed out",
                timeout_duration=self.timeout,
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

        except requests.exceptions.ConnectionError as e:
            raise TapperConnectionError(
                "Cannot connect to get status",
                device_id=self.device_id,
                protocol="HTTP",
                connection_details={"base_url": self.base_url, "error": str(e)}
            ) from e

        except requests.exceptions.HTTPError as e:
            raise TapperProtocolError(
                f"HTTP error getting status: {e.response.status_code} {e.response.reason}",
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

        except Exception as e:
            self.logger.warning(f"Failed to get status from tapper: {e}")
            return "unknown"

    def extend_for_time(self, duration_ms: int) -> Any:
        """
        Override for direct HTTP POST to timed operation endpoint.
        
        :param duration_ms: Duration in milliseconds
        :return: Response text or raises exception
        """
        try:
            self.logger.debug(f"Extending for {duration_ms}ms via direct endpoint")
            response = requests.post(f"{self.base_url}/extend_for_time?duration={duration_ms}", timeout=self.timeout)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extend for time: {e}")
            raise TapperProtocolError(
                f"Extend for time operation failed",
                command="extend_for_time", 
                device_id=self.device_id,
                protocol="HTTP"
            ) from e
    
    def retract_for_time(self, duration_ms: int) -> Any:
        """
        Override for direct HTTP POST to timed operation endpoint.
        
        :param duration_ms: Duration in milliseconds
        :return: Response text or raises exception
        """
        try:
            self.logger.debug(f"Retracting for {duration_ms}ms via direct endpoint")
            response = requests.post(f"{self.base_url}/retract_for_time?duration={duration_ms}", timeout=self.timeout)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Failed to retract for time: {e}")
            raise TapperProtocolError(
                f"Retract for time operation failed",
                command="retract_for_time",
                device_id=self.device_id,
                protocol="HTTP"
            ) from e

    def __repr__(self) -> str:
        return f"<HTTPTapperProtocol[{self.device_id}] url={self.base_url}>"

