#!/usr/bin/env python3
"""
Tapper System - Unified dual protocol tapper framework.

This module provides a complete tapper system with:
- Dual protocol support (HTTP/MQTT seamless operation)
- Dual card tapper operations (Card 1 & Card 2)
- Clean service orchestration
- Modular architecture

Main Components:
    TapperService: Main service orchestrator (controller/)
    Protocols: HTTP and MQTT protocol implementations (protocols/)
    Commands: Modern dual card sequences and legacy operations (commands/)
    Registry: Device and station management (registry/)

Example Usage:
    from tappers_service.tapper_system import TapperService
    from tappers_service.tapper_system.commands import dual_sequences
    from tappers_service.tapper_system.commands import legacy_sequences  # For backward compatibility
    
    # Create service with dual protocol support
    service = TapperService("station1")
    service.connect()  # Auto-selects best protocol (HTTP/MQTT)
    
    # Modern dual card operations (recommended)
    dual_sequences.tap_card2_timed(service.protocol)
    dual_sequences.dual_card_sequence_timed(service.protocol)
    
    # Legacy operations (for backward compatibility)
    legacy_sequences.simple_tap(service.protocol)  # Original function names preserved
"""

# Main exports
from .controller.tapper_service import TapperService
from .protocols.base_protocol import BaseProtocol
from .protocols.http_protocol import HTTPTapperProtocol  
from .protocols.mqtt_protocol import MQTTTapperProtocol
from .registry.tapper_registry import TapperRegistry

# Command modules available for import
from . import commands

__all__ = [
    'TapperService',
    'BaseProtocol',
    'HTTPTapperProtocol', 
    'MQTTTapperProtocol',
    'TapperRegistry',
    'command'
]

__version__ = '2.0.0'
__author__ = 'Dual Tapper System Team'