# ==================================================
# 3. UPDATE: tapper_registry.py
# ==================================================

"""
Updated TapperRegistry to use singleton pattern
"""

from typing import Dict

from tappers_service.protocols.fallback_protocol import FallbackTapperProtocol
from tappers_service.protocols.http_protocol import HTTPTapperProtocol
from tappers_service.protocols.mqtt_protocol import MQTTTapperProtocol
from test_framework.utils import get_logger
from test_framework.utils.loaders.config_manager import ConfigurationManager


class TapperRegistry:
    """
    Registry to manage and cache tapper instances per test station.
    Uses singleton ConfigurationManager to prevent duplicate loading.
    """

    def __init__(self):
        self._tapper_cache: Dict[str, FallbackTapperProtocol] = {}
        self.logger = get_logger(f"TapperRegistry")

        # Use singleton ConfigurationManager
        self.config_manager = ConfigurationManager.get_instance()

    def get_tapper(self, station_id: str) -> FallbackTapperProtocol:
        """
        Return a tapper instance for the given station using fallback strategy.
        Uses singleton ConfigurationManager to avoid duplicate config loading.
        """
        if station_id in self._tapper_cache:
            self.logger.debug(f"Using cached tapper for station: {station_id}")
            return self._tapper_cache[station_id]

        self.logger.debug(f"Creating new tapper for station: {station_id}")

        # Use singleton config manager - no duplicate loading
        station_config = self.config_manager.get_station_config(station_id)

        # Extract needed configs from station config
        tapper_config = station_config.tapper_config
        enabled_protocols = station_config.enabled_protocols
        protocol_configs = station_config.protocol_configs

        device_id = tapper_config.get("device_id", station_id)
        self.logger.debug(f"Station '{station_id}' maps to device_id '{device_id}'")

        protocols = []

        # Build protocols from resolved config
        if "mqtt" in enabled_protocols and "mqtt" in protocol_configs:
            mqtt_config = protocol_configs["mqtt"]
            self.logger.debug(f"Adding MQTT protocol for device_id '{device_id}'")
            protocols.append(MQTTTapperProtocol(device_id=device_id, config=mqtt_config))

        if "http" in enabled_protocols and "http" in protocol_configs:
            http_config = protocol_configs["http"]
            self.logger.debug(f"Adding HTTP protocol for device_id '{device_id}'")
            protocols.append(HTTPTapperProtocol(http_config))

        if not protocols:
            raise ValueError(f"No supported protocols found for station '{station_id}'")

        fallback_protocol = FallbackTapperProtocol(protocols)

        # Attempt to connect protocols
        try:
            fallback_protocol.connect()
            self.logger.debug(f"Connected fallback protocol for station '{station_id}'")
        except Exception as e:
            self.logger.warning(f"Initial connection failed for station '{station_id}': {e}")

        self._tapper_cache[station_id] = fallback_protocol

        # Single consolidated log message
        active_protocols = fallback_protocol.get_active_protocols()
        if active_protocols:
            self.logger.info(f"Station '{station_id}' connected via {','.join(active_protocols)}")
        else:
            self.logger.warning(f"Station '{station_id}' loaded but no protocols connected")

        return fallback_protocol

    def invalidate(self, station_id: str) -> None:
        """
        Remove the cached protocol for a given station if it exists.

        :param station_id: The station ID to remove from cache.
        """
        if station_id in self._tapper_cache:
            self.logger.debug(f"Invalidating tapper cache for station '{station_id}'")
            # Optionally disconnect before removing from cache
            try:
                self._tapper_cache[station_id].disconnect()
            except Exception as e:
                self.logger.warning(f"Error disconnecting cached tapper for '{station_id}': {e}")
            del self._tapper_cache[station_id]