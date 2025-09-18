from typing import List, Optional, Dict, Any

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from tappers_service.tapper_system.utils import TapperProtocolError


class FallbackTapperProtocol(BaseProtocol):
    """
    Composite tapper protocol that implements automatic fallback across multiple protocols.

    Tries each protocol in the provided order for both commands and status requests.
    If one protocol fails, automatically attempts the next protocol in the chain.
    Caches the working protocol to avoid repeated connection attempts on later commands.

    This enables resilient communication by providing multiple transport options
    (e.g., HTTP → MQTT fallback) without requiring changes to client code.

    Example:
        protocols = [HTTPTapperProtocol(...), MQTTTapperProtocol(...)]
        fallback = FallbackTapperProtocol(protocols)
        fallback.send_command("tap") # Tries HTTP first, then MQTT if HTTP fails

    Attributes:
        protocols (List[BaseProtocol]): Ordered list of protocols to try.
    """

    def __init__(self, protocols: List[BaseProtocol]):
        """
        Initialize the fallback protocol with a list of protocols to try.

        :param protocols: Ordered a list of protocols to attempt (first = highest priority).
        :raise ValueError: If no protocols are provided.
        """
        if not protocols:
            raise ValueError("At least one protocol is required for FallbackTapperProtocol.")

        self.protocols = protocols
        primary = protocols[0]

        # Initialize with primary protocol's device info
        super().__init__(
            device_id=primary.device_id,
            config=primary.config
        )

        # Use primary protocol's logger as fallback logger
        self.logger = primary.logger

        # Protocol caching for performance optimization
        self._working_protocol = None

    def connect(self) -> bool:
        """
        Attempt to connect all protocols in the fallback chain.

        Tries to connect each protocol independently. Succeeds if at least
        one protocol connects successfully.

        :return bool: True if any protocol connects successfully, False if all fail.
        """
        connected_protocols = []
        failed_protocols = []

        for protocol in self.protocols:
            try:
                if protocol.connect():
                    connected_protocols.append(protocol.protocol_name)
                    # Set ANY working protocol as our preferred one
                    if not self._working_protocol:
                        self._working_protocol = protocol
                        self.logger.info(f"Using {protocol.protocol_name} as primary protocol")
                else:
                    failed_protocols.append(protocol.protocol_name)
            except Exception as e:
                failed_protocols.append(protocol.protocol_name)
                self.logger.debug(f"{protocol.protocol_name} connection failed: {e}")

        # Ensure we have a working protocol if any connected successfully
        if not self._working_protocol and connected_protocols:
            # Find any connected protocol and use it
            for protocol in self.protocols:
                if protocol.is_connected():
                    self._working_protocol = protocol
                    self.logger.info(f"Set {protocol.protocol_name} as working protocol")
                    break

        success = len(connected_protocols) > 0
        self._connected = success

        if success:
            if failed_protocols:
                self.logger.info(
                    f"Connected via {','.join(connected_protocols)} (fallback from {','.join(failed_protocols)})")
            else:
                self.logger.debug(f"Connected via {','.join(connected_protocols)}")
        else:
            self.logger.error(f"All protocols failed to connect: {','.join(failed_protocols)}")

        return success

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send a commands using the cached working protocol with automatic fallback.

        :param command: Command name (e.g., "tap", "extend", "retract").
        :param params: Optional commands parameters.
        :return Any: Response from the successful protocol.
        :raise TapperProtocolError: If all protocols in the chain fail.
        """

        # Try the known working protocol first
        if self._working_protocol:
            try:
                if self._working_protocol.is_connected():
                    result = self._working_protocol.send_command(command, params)
                    self.logger.debug(f"Command '{command}' succeeded via {self._working_protocol.protocol_name}")
                    return result
                else:
                    self.logger.debug(f"{self._working_protocol.protocol_name} disconnected, trying fallback")
                    self._working_protocol = None
            except Exception as e:
                self.logger.debug(f"{self._working_protocol.protocol_name} failed: {e}")
                self._working_protocol = None

        # Try all connected protocols to find a working one
        for protocol in self.protocols:
            if protocol == self._working_protocol:
                continue

            try:
                if protocol.is_connected():
                    result = protocol.send_command(command, params)
                    self._working_protocol = protocol  # Cache this working protocol
                    self.logger.info(f"Switched to {protocol.protocol_name} as working protocol")
                    return result
            except Exception as e:
                self.logger.debug(f"{protocol.protocol_name} failed: {e}")
                continue

        # All protocols failed
        raise TapperProtocolError(
            f"No working protocols available for commands '{command}'",
            command=command,
            device_id=self.device_id,
            protocol="CachedFallback"
        )

    def get_status(self) -> str:
        """
        Retrieve status using the cached working protocol with automatic fallback.

        Attempts the cached working protocol first. If unavailable, try each protocol
        in order until one succeeds.

        :return str: Status string from the first working protocol.
        :raise TapperProtocolError: If all protocols fail to retrieve status.
        """
        if self._working_protocol and self._working_protocol.is_connected():
            try:
                return self._working_protocol.get_status()
            except Exception:
                self._working_protocol = None

        # Try other protocols
        for protocol in self.protocols:
            try:
                if protocol.is_connected():
                    status = protocol.get_status()
                    self._working_protocol = protocol
                    return status
            except Exception:
                continue

        raise TapperProtocolError("No working protocols available for status check")

    def disconnect(self) -> None:
        """
        Disconnect all protocols in the fallback chain.

        Attempts to disconnect each protocol gracefully, logging any errors
        but continuing to disconnect remaining protocols.
        """
        for protocol in self.protocols:
            try:
                protocol.disconnect()
            except Exception as e:
                self.logger.warning(f"{protocol.protocol_name} disconnect failed: {e}")
        self._connected = False
        self._working_protocol = None

    def is_connected(self) -> bool:
        """Check if any protocol is connected."""
        return any(protocol.is_connected() for protocol in self.protocols)

    def get_available_protocols(self) -> List[str]:
        """Get a list of all protocol names in the fallback chain."""
        return [protocol.protocol_name for protocol in self.protocols]

    def get_active_protocols(self) -> List[str]:
        """Get a list of currently connected protocol names."""
        return [protocol.protocol_name for protocol in self.protocols if protocol.is_connected()]

    def __repr__(self) -> str:
        """
        Enhanced string representation showing fallback chain status.

        Shows both available protocols and currently active (connected) protocols
        for better debugging and monitoring.

        :return str: Formatted representation string.
        """
        available = self.get_available_protocols()
        active = self.get_active_protocols()
        working = self._working_protocol.protocol_name if self._working_protocol else "none"

        if active:
            status_info = f"active:{','.join(active)},working:{working}"
        else:
            status_info = "disconnected"

        return f"<{self.protocol_name}Protocol[{self.device_id}] - {status_info} (fallback:{','.join(available)})>"