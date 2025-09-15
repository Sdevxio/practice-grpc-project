from typing import Optional

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from tappers_service.tapper_system.registry.tapper_registry import TapperRegistry
from tappers_service.tapper_system.utils import TapperError
from test_framework.utils import get_logger


class TapperService:
    """
    High-level interface to tapper device based on station ID.
    This service provides connection management and basic device operations.
    For sequences, use the functions in the sequences module.

    Example:
        from tappers_service import sequences

        tapper = TapperService(station_id="station1")
        tapper.connect()

        # Use sequence functions
        sequences.simple_tap(tapper.protocol)
        sequences.double_tap(tapper.protocol, delay_ms=300)

        tapper.disconnect()

    Attributes:
        station_id (str): Logical ID of the test station.
        logger: Logger instance for this service.
    """

    def __init__(self, station_id: str, logger: Optional[object] = None):
        """
        Initialize the tapper service for the given station.

        :param station_id: Logical ID of the test station (e.g., "station1").
        :param logger: Optional logger instance (creates default if not provided).
        """

        self.station_id = station_id
        self.logger = logger or get_logger(f"TapperService[{station_id}]")
        self.protocol: Optional[BaseProtocol] = None
        self._registry = TapperRegistry()

    def connect(self) -> bool:
        """
        Load station config and establish connection to tapper device.

        :return bool: True if connection succeeded, False otherwise.
        :raise Exception: If connection fails after all retry attempts.
        """
        try:
            self.logger.debug(f"Connecting to tapper on station: {self.station_id}")
            self.protocol = self._registry.get_tapper(self.station_id)

            if self.protocol.is_connected():
                # Clean summary showing what's actually connected
                active_protocols = getattr(self.protocol, 'get_active_protocols',
                                           lambda: [self.protocol.protocol_name])()
                self.logger.info(f"Tapper connected via {','.join(active_protocols)}")
                return True
            else:
                self.logger.warning(f"Protocol created but not connected for station '{self.station_id}'")
                return False

        except Exception as e:
            self._registry.invalidate(self.station_id)
            self.logger.error(f"Failed to connect to tapper for station '{self.station_id}': {e}")
            raise

    def disconnect(self) -> None:
        """
        Disconnect from the tapper device and clean up resources.
        """
        try:
            if self.protocol:
                self.protocol.disconnect()
                self.logger.debug(f"Disconnected from tapper for station '{self.station_id}'")

            self._registry.invalidate(self.station_id)
            self.protocol = None

        except Exception as e:
            self.logger.warning(f"Error during disconnect for station '{self.station_id}': {e}")

    def is_connected(self) -> bool:
        """
        Check if the service is currently connected to a tapper device.

        :return bool: True if connected and protocol is available, False otherwise.
        """
        return self.protocol is not None and self.protocol.is_connected()

    def get_status(self) -> str:
        """
        Get the current status of the tapper device.

        :return str: Current tapper status (e.g., "idle", "extended", "retracted").
        :raise TapperError: If not connected or status retrieval fails.
        """
        self._ensure_connected()

        try:
            status = self.protocol.get_status()
            self.logger.debug(f"Tapper status for station '{self.station_id}': {status}")
            return status
        except Exception as e:
            self.logger.error(f"Failed to get status for station '{self.station_id}': {e}")
            raise

    def send_command(self, command: str, params: Optional[dict] = None) -> any:
        """
        Send a raw command directly to the tapper device.

        :param command: Command name (e.g., "tap", "extend", "retract").
        :param params: Optional command parameters.
        :return any: Response from the tapper device.
        :raise TapperError: If not connected or command execution fails.
        """
        self._ensure_connected()

        try:
            self.logger.debug(f"Sending command '{command}' to station '{self.station_id}'")
            result = self.protocol.send_command(command, params)
            self.logger.debug(f"Command '{command}' completed for station '{self.station_id}'")
            return result

        except Exception as e:
            self.logger.error(f"Failed to send command '{command}' to station '{self.station_id}': {e}")
            raise

    def health_check(self) -> dict:
        """
        Perform a comprehensive health check of the tapper service.

        :return dict: Health check results with connection status, device info, etc.
        """
        health_info = {
            "station_id": self.station_id,
            "service_connected": self.is_connected(),
            "protocol_type": None,
            "device_status": "unknown",
            "last_error": None
        }

        try:
            if self.protocol:
                health_info["protocol_type"] = self.protocol.protocol_name

                if self.is_connected():
                    health_info["device_status"] = self.get_status()
                else:
                    health_info["device_status"] = "disconnected"

        except Exception as e:
            health_info["last_error"] = str(e)
            health_info["device_status"] = "error"

        return health_info

    def _ensure_connected(self) -> None:
        """
        Internal helper to ensure the service is connected before operations.

        :raise TapperError: If not connected to a tapper device.
        """
        if not self.is_connected():
            raise TapperError(
                "Tapper not connected. Call connect() first.",
                device_id=getattr(self.protocol, 'device_id', 'unknown'),
                protocol=getattr(self.protocol, 'protocol_name', 'none')
            )

    def __enter__(self):
        """Context manager entry - automatically connect."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically disconnect."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation of the tapper service."""
        status = "connected" if self.is_connected() else "disconnected"
        protocol_name = getattr(self.protocol, 'protocol_name', 'none')
        return f"<TapperService[{self.station_id}] - {status} ({protocol_name})>"
