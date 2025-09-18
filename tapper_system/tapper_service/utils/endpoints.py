"""
Simple tapper endpoint definitions.
"""

from typing import Dict
from test_framework.utils import get_logger

logger = get_logger("TapperEndpoints")

# Basic tapper endpoints - keep only what we actually use
TAPPER_ENDPOINTS = {
    'extend': '/extend',
    'retract': '/retract',
    'stop': '/stop',
    'tap': '/tap',
    'status': '/status',
    'health': '/health',
    'ping': '/ping',
    'tap_card1': '/tap_card1',
    'tap_card2': '/tap_card2',
    'reset_to_middle': '/reset_to_middle'
}


class EndpointBuilder:
    """Simple URL builder for tapper endpoints."""
    
    def __init__(self, base_url: str = None, device_id: str = None):
        self.base_url = base_url
        self.device_id = device_id
    
    def build_url(self, endpoint_name: str) -> str:
        """Build complete URL for an endpoint."""
        if not self.base_url:
            raise ValueError("Base URL not set")
        
        if endpoint_name not in TAPPER_ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        path = TAPPER_ENDPOINTS[endpoint_name]
        return f"{self.base_url.rstrip('/')}{path}"
    
    def build_mqtt_topic(self, endpoint_name: str) -> str:
        """Build MQTT topic for an endpoint."""
        if not self.device_id:
            raise ValueError("Device ID not set")
        
        return f"tappers/{self.device_id}/command"