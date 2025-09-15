"""
Simple tapper exceptions.
"""

class TapperError(Exception):
    """Base class for all tapper-related errors."""
    def __init__(self, message: str, device_id: str = None):
        self.message = message
        self.device_id = device_id
        if device_id:
            message = f"{message} (Device: {device_id})"
        super().__init__(message)


class TapperConnectionError(TapperError):
    """Raised when cannot connect to a tapper device."""
    pass


class TapperProtocolError(TapperError):
    """Raised when protocol communication fails."""
    pass


class TapperTimeoutError(TapperError):
    """Raised when tapper operation times out."""
    pass


class TapperConfigurationError(TapperError):
    """Raised when tapper configuration is invalid."""
    pass