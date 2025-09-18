"""
Station configuration loader with backward compatibility.
This module provides a StationLoader class that loads station configurations
from a new configuration system while maintaining backward compatibility
with legacy configuration formats.
It includes methods to retrieve station details, user assignments,
test users, and other related configurations.
"""
import warnings
from typing import Dict, Any, List

from test_framework.utils import get_logger
from test_framework.utils.loaders.config_manager import ConfigManager


class StationLoader:
    """Station configuration loader with backward compatibility."""

    def __init__(self):
        """Initialize the StationLoader."""
        self.logger = get_logger("StationLoader")
        # Use singleton instance instead of creating new one
        try:
            self.config_manager = ConfigManager.get_instance()
            self._use_new_system = True
            self.logger.debug("Using singleton configuration manager")
        except Exception as e:
            self.logger.error(f"Failed to get configuration manager instance: {e}")
            raise FileNotFoundError(
                "Configuration system failed to initialize. "
                "Please ensure the new config files exist in test_framework/configs/"
            ) from e

    def get_station_config(self, station_name: str, protocol: str = None) -> Dict[str, Any]:
        """
        Get station configuration in legacy format for backward compatibility.

        :param station_name: Name of the station.
        :param protocol: Optional protocol filter ('http', 'mqtt', 'grpc').
        :return: Station configuration dictionary.
        Example:
            loader = StationLoader()
            config = loader.get_station_config('station1', protocol='http')
            print(config)
        """
        try:
            # Get config in legacy format for backward compatibility
            config = self.config_manager.get_legacy_station_config(station_name)

            # Return specific protocol if requested
            if protocol:
                if protocol not in config:
                    raise KeyError(f"Protocol '{protocol}' not found for station '{station_name}'")
                return {protocol: config[protocol]}

            return config

        except Exception as e:
            self.logger.error(f"Failed to get station config for '{station_name}': {e}")
            raise

    def get_station_endpoint(self, station_name: str, protocol: str) -> str:
        """
        Get station endpoint URL based on protocol.

        :param station_name: Name of the station.
        :param protocol: Protocol type ('http', 'mqtt', 'grpc').
        :return: Endpoint URL as a string.
        Example:
            loader = StationLoader()
            http_url = loader.get_station_endpoint('station1', 'http')
            mqtt_url = loader.get_station_endpoint('station1', 'mqtt')
            grpc_target = loader.get_station_endpoint('station1', 'grpc')
            print(f"HTTP URL: {http_url}, MQTT URL: {mqtt_url}, gRPC Target: {grpc_target}")
        """
        config = self.get_station_config(station_name, protocol)

        if protocol == 'http':
            return config[protocol].get('base_url', '')
        elif protocol == 'mqtt':
            mqtt = config[protocol]
            broker = mqtt.get('broker', '')
            port = mqtt.get('port', 1883)
            return f"mqtt://{broker}:{port}"
        elif protocol == 'grpc':
            grpc = config[protocol]
            host = grpc.get('host', 'localhost')
            port = grpc.get('port', 50051)
            return f"{host}:{port}"

        return ""

    def get_grpc_target(self, station_name: str) -> str:
        """Get gRPC target for station (backwards compatibility)."""
        return self.get_station_endpoint(station_name, 'grpc')

    def get_grpc_host(self, station_name: str) -> str:
        """Get gRPC host for station."""
        grpc_config = self.get_station_config(station_name, 'grpc')
        return grpc_config['grpc'].get('host', 'localhost')

    def get_grpc_port(self, station_name: str) -> str:
        """Get gRPC port for station."""
        grpc_config = self.get_station_config(station_name, 'grpc')
        return grpc_config['grpc'].get('port', '50051')

    def get_grpc_fallback_ports(self, station_name: str) -> List[int]:
        """Get gRPC fallback ports for station."""
        grpc_config = self.get_station_config(station_name, 'grpc')
        return grpc_config['grpc'].get('fallback_ports', [])

    def list_stations(self) -> List[str]:
        """Get all station names."""
        return self.config_manager.list_stations()

    # New methods that leverage the enhanced configuration system
    def get_test_users(self) -> Dict[str, Any]:
        """Get test user configurations (new method)."""
        return self.config_manager.get_test_users()

    def get_test_cards(self) -> Dict[str, Any]:
        """Get test card configurations (new method)."""
        return self.config_manager.get_test_cards()

    def get_user_assignments(self) -> Dict[str, Any]:
        """Get user-to-station assignments (new method)."""
        # For backward compatibility, return empty dict since we removed assignments
        return {}

    def get_e2e_defaults(self) -> Dict[str, Any]:
        """Get E2E test defaults (new method)."""
        return self.config_manager.get_e2e_defaults()

    def get_domain(self) -> Dict[str, Any]:
        """Get domain configuration (new method)."""
        return self.config_manager.get_domain()

    def get_station_groups(self) -> Dict[str, Any]:
        """Get station group configurations (new method)."""
        return self.config_manager.get_station_groups()

    def get_complete_station_config(self, station_name: str):
        """
        Get complete station configuration object (new method).

        This method provides access to the enhanced StationConfig object.
        """
        return self.config_manager.get_station_config(station_name)

    def invalidate_cache(self, station_name: str = None):
        """Invalidate configuration cache (new method)."""
        self.config_manager.invalidate_cache(station_name)

    def reload_configurations(self):
        """Reload all configuration files (new method)."""
        self.config_manager.reload_configurations()


class LegacyStationLoader(StationLoader):
    """Alias for backward compatibility."""

    def __init__(self, config_name="stations"):
        """Initialize with deprecation warning."""
        warnings.warn(
            "LegacyStationLoader is deprecated. Use StationLoader directly.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(config_name)