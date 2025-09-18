import json
import threading
from typing import Optional, Dict, Any

import paho.mqtt.client as mqtt

from tappers_service.tapper_system.protocols.base_protocol import BaseProtocol
from tappers_service.tapper_system.utils import TapperConnectionError, TapperProtocolError


class MQTTTapperProtocol(BaseProtocol):
    """
    MQTT-based tapper communication protocol.

    Communicates with ESP32 tapper devices using topic-based messaging.
    Handles:
      - Command publishing
      - Status updates via subscription
      - Graceful reconnect/disconnect

    Topics:
      - tappers/<device_id>/commands
      - tappers/<device_id>/status
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize MQTT protocol handler.

        :param device_id: Device ID for topic routing.
        :param config: Dictionary with keys like 'broker', 'port'.
        """
        super().__init__(device_id=device_id, config=config)
        self.broker = config.get("broker", "localhost")
        self.port = config.get("port", 1883)
        self.timeout = config.get("timeout", 2)

        self.topic_prefix = f"tappers/{self.device_id}"
        self.command_topic = f"{self.topic_prefix}/commands"
        self.status_topic = f"{self.topic_prefix}/status"

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._status = "unknown"
        self._lock = threading.Lock()
        self._connected = False

    def connect(self) -> bool:
        """
        Connect to the MQTT broker and subscribe to status updates.

        :return bool: True if connection succeeded.
        """
        try:
            self._client.on_message = self._on_message
            self._client.connect(self.broker, self.port)
            self._client.loop_start()
            self._client.subscribe(self.status_topic)
            self._connected = True
            self.logger.debug(f"Connected to MQTT broker at {self.broker}:{self.port}")  # Changed from INFO to DEBUG
            return True
        except Exception as e:
            self._connected = False
            self.logger.debug(f"MQTT connection failed: {e}")  # Changed from ERROR to DEBUG
            raise TapperConnectionError(
                f"Cannot connect to MQTT broker at {self.broker}:{self.port}",
                device_id=self.device_id,
                protocol="MQTT",
                connection_details={
                    "broker": self.broker,
                    "port": self.port,
                    "error": str(e)
                }
            ) from e

    def _on_message(self, msg):
        """Handle status messages received via subscription."""
        try:
            payload = msg.payload.decode()
            with self._lock:
                self._status = payload.strip()
            self.logger.debug(f"Received status on {msg.topic}: {self._status}")
        except Exception as e:
            self.logger.warning(f"Failed to decode MQTT message: {e}")

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish a commands to the tapper.

        :param command: Command name (e.g., 'tap', 'extend').
        :param params: Optional parameters for the commands.
        :return bool: True if publish succeeded.
        """
        if not self._connected:
            raise TapperConnectionError(
                "Not connected to MQTT broker",
                device_id=self.device_id,
                protocol="MQTT"
            )

        try:
            message = {"action": command}
            if params:
                message.update(params)

            payload = json.dumps(message)
            result = self._client.publish(self.command_topic, payload)
            self.logger.debug(f"Published to {self.command_topic}: {payload}")  # Changed from INFO to DEBUG
            return result.rc == mqtt.MQTT_ERR_SUCCESS

        except TypeError as e:
            raise TapperProtocolError(
                f"Failed to encode commands '{command}' as JSON",
                command=command,
                device_id=self.device_id,
                protocol="MQTT"
            ) from e

        except Exception as e:
            self.logger.error(f"MQTT send_command failed: {e}")
            raise TapperProtocolError(
                f"Failed to send commands '{command}'",
                command=command,
                device_id=self.device_id,
                protocol="MQTT"
            ) from e

    def get_status(self) -> str:
        """
        Return the last known status from MQTT.

        :return str: Status value.
        """
        if not self._connected:
            raise TapperConnectionError(
                "Cannot get status - not connected to MQTT broker",
                device_id=self.device_id,
                protocol="MQTT"
            )

        with self._lock:
            status = self._status
        self.logger.debug(f"Returning cached status: {status}")
        return status

    def disconnect(self) -> None:
        """Cleanly disconnect from MQTT broker."""
        try:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            self.logger.debug("Disconnected from MQTT broker.")  # Changed from INFO to DEBUG
        except Exception as e:
            self.logger.warning(f"Error during MQTT disconnect: {e}")
            self._connected = False

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<MQTTTapperProtocol[{self.device_id}] {self.broker}:{self.port} - {status}>"