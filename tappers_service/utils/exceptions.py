"""
Exceptions class for tapper service.

This module defines custom exceptions for the tapper service, which
are used to handle various error conditions that may arise during
communication with tapper devices. Each exception class provides
specific context about the error, such as the device ID, protocol used,
and additional details relevant to the error condition.
"""

class TapperError(Exception):
    """Base class for all tapper-related errors."""
    def __init__(self, message: str = "", device_id: str = None, protocol: str = None):
        self.message = message
        self.device_id = device_id
        self.protocol = protocol
        error_parts = [message]
        if device_id:
            error_parts.append(f"Device: {device_id}")
        if protocol:
            error_parts.append(f"Protocol: {protocol}")
        super().__init__(" | ".join(error_parts))

    def __str__(self):
        return f"[{self.protocol or 'Unknown'}] {self.message} (Device: {self.device_id or 'N/A'})"

class TapperConnectionError(TapperError):
    """
    Raised when cannot connect to a tapper device.

    This indicates a failure to establish communication with the tapper
    hardware. Common causes include network issues, wrong configuration,
    or hardware being offline.
    """
    def __init__(self, message: str, device_id: str = None, protocol: str = None, connection_details: dict = None):
        super().__init__(message, device_id, protocol)
        self.connection_details = connection_details or {}


class TapperTimeoutError(TapperError):
    """
    Rose when tapper operation times out.

    This indicates that a command or connection attempt took longer
    than the specified timeout. The device might be slow to respond
    or experiencing performance issues.
    """
    def __init__(self, message: str, timeout_duration: float = None, device_id: str = None, protocol: str = None):
        if timeout_duration:
            message = f"{message} (timeout after {timeout_duration}s)"
        super().__init__(message, device_id, protocol)
        self.timeout_duration = timeout_duration


class TapperProtocolError(TapperError):
    """
    Raised when protocol communication fails.

    This indicates a problem with the communication protocol itself,
    such as malformed messages, protocol violations, or transport
    layer failures after connection is established.
    """
    def __init__(self, message: str, command: str = None, response: str = None, device_id: str = None, protocol: str = None):
        super().__init__(message, device_id, protocol)
        self.command = command
        self.response = response


class TapperConfigurationError(TapperError):
    """
    Raised when tapper configuration is invalid or incomplete.

    This indicates problems with the tapper setup, such as missing
    required parameters, invalid protocol settings, or configuration
    conflicts.
    """
    def __init__(self, message: str, config_key: str = None, config_value: str = None, station_id: str = None):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value
        self.station_id = station_id