"""
Tapper protocol implementations.

This package contains protocol implementations for communicating with tapper devices:

- BaseProtocol: Abstract base class defining the protocol interface
- HTTPTapperProtocol: HTTP-based communication
- MQTTTapperProtocol: MQTT-based communication
- FallbackTapperProtocol: Composite protocol with automatic failover
"""

from .base_protocol import BaseProtocol
from .http_protocol import HTTPTapperProtocol
from .mqtt_protocol import MQTTTapperProtocol
from .fallback_protocol import FallbackTapperProtocol

__all__ = [
    'BaseProtocol',
    'HTTPTapperProtocol',
    'MQTTTapperProtocol',
    'FallbackTapperProtocol'
]