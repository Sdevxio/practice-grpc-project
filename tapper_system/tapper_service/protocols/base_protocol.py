from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from test_framework.utils import get_logger


class BaseProtocol(ABC):
    """
    Abstract base class for all tapper communication protocols.

    Defines the unified transport-agnostic interface used by all concrete protocol implementations,
    such as HTTP and MQTT. Provides built-in logging and protocol metadata access.

    Attributes:
        device_id (str): Identifier of the tapper device (used for topic routing or logging).
        config (Dict[str, Any]): Protocol-specific configuration dictionary.
        logger: Logger instance scoped to the protocol and device.
        _connected (bool): Connection state tracking flag.
    """

    def __init__(self, device_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base protocol.

        :param device_id (str): Unique device identifier (used in MQTT and logging).
        :param config: Protocol-specific settings.
        """
        self.device_id = device_id
        self.config = config or {}
        self._connected = False
        self.logger = get_logger(f"Protocol[{self.protocol_name}][{self.device_id}]")

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the protocol layer.

        :return bool: True if connection succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send a commands to the tapper.

        :param command: Action name (e.g., "tap", "extend").
        :param params: Optional parameters for the commands (e.g., speed, duration).
        :return Any: Protocol-specific response.
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """
        Retrieve the current tapper status.

        :return str: Tapper status string (e.g., "idle", "extended").
        """
        pass


    def extend_for_time(self, duration_ms: int) -> Any:
        """
        Extend the tapper for a specified duration.

        :param duration_ms: Duration in milliseconds to extend.
        """
        return self.send_command("extend_for_time", {"duration_ms": duration_ms})


    def retract_for_time(self, duration_ms: int) -> Any:
        """
        Retract the tapper for a specified duration.

        :param duration_ms: Duration in milliseconds to retract.
        """
        return self.send_command("retract_for_time", {"duration_ms": duration_ms})

    def disconnect(self) -> None:
        """
        Optional cleanup for protocols that maintain state (e.g., MQTT).
        Stateless protocols (e.g., HTTP) can override as a no-op.
        """
        self._connected = False  # Default reset
        self.logger.debug("Protocol disconnected.")

    @property
    def protocol_name(self) -> str:
        """
        Get the protocol name for this implementation.

        :return str: Clean protocol identifier (e.g., "HTTP", "MQTT")
        """
        return self.__class__.__name__.replace("TapperProtocol", "").replace("Protocol", "")

    def is_connected(self) -> bool:
        """
        Return whether the protocol is currently connected.

        :return bool: True if connected, False otherwise.
        """
        return self._connected

    def get_active_protocols(self) -> List[str]:
        """
        Get list of currently active protocol names.

        For single protocols, returns a list with just this protocol.
        For fallback protocols, this is overridden to return multiple protocols.

        :return List[str]: List of active protocol names.
        """
        return [self.protocol_name] if self.is_connected() else []

    def __repr__(self) -> str:
        """String representation of the protocol instance."""
        status = "connected" if self.is_connected() else "disconnected"
        return f"<{self.protocol_name}Protocol[{self.device_id}] - {status}>"