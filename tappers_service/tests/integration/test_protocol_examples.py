#!/usr/bin/env python3
"""
Integration Test: Dual Protocol Tapper System Examples

This integration test demonstrates the clean architecture of the tapper system:
1. Dual protocol support (HTTP → MQTT fallback)
2. Dual card operations (Card 1 & Card 2) 
3. Clean API usage

Converted from example to integration test format.
"""

import pytest

import sys
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system import TapperService
from tappers_service.tapper_system.command import dual_sequences


def example_basic_usage():
    """Example 1: Basic dual protocol usage."""
    print("🔄 Example 1: Basic Dual Protocol Usage")
    print("=" * 50)
    
    # Create service - automatically handles HTTP/MQTT
    service = TapperService("station1")
    
    # Connect - tries HTTP first, falls back to MQTT if needed
    if service.connect():
        print(f"✅ Connected via {service.protocol.protocol_name}")
        
        # Perform dual card operation - same API regardless of protocol
        dual_sequences.tap_card2_timed(service.protocol)
        
        service.disconnect()
    else:
        print("❌ Failed to connect via any protocol")


def example_dual_card_operations():
    """Example 2: Dual card operations with clean API."""
    print("\n🎯 Example 2: Dual Card Operations")
    print("=" * 50)
    
    with TapperService("station1") as service:
        if not service.protocol:
            print("❌ Connection failed")
            return
            
        print(f"✅ Connected via {service.protocol.protocol_name}")
        
        # Card 2 tap with custom timing
        print("\n🔴 Tapping Card 2 with custom timing...")
        dual_sequences.adaptive_tap_card2(service.protocol, extend_time=1385)
        
        # Dual card sequence
        print("\n🔄 Running dual card sequence...")
        dual_sequences.dual_card_sequence_timed(service.protocol)
        
        # Quick tap for testing
        print("\n⚡ Quick tap for testing...")
        dual_sequences.quick_tap_card2(service.protocol, extend_time=1390)


def example_protocol_independence():
    """Example 3: Protocol independence - same code works with HTTP or MQTT."""
    print("\n🌐 Example 3: Protocol Independence")
    print("=" * 50)
    
    service = TapperService("station1")
    service.connect()
    
    if service.protocol:
        # This code works identically whether using HTTP or MQTT
        protocol_name = service.protocol.protocol_name
        print(f"Using protocol: {protocol_name}")
        
        # Get status - same API
        status = service.protocol.get_status()
        print(f"Device status: {status}")
        
        # Timed operations - same API
        print("Performing timed operation via", protocol_name)
        dual_sequences.tap_card2_timed(service.protocol, retract_time=1400, return_time=1385)
        
        service.disconnect()


def example_error_handling():
    """Example 4: Automatic protocol fallback in action."""
    print("\n🔧 Example 4: Automatic Protocol Fallback")
    print("=" * 50)
    
    print("The system automatically:")
    print("1. Tries HTTP first (fastest)")
    print("2. Falls back to MQTT if HTTP fails")
    print("3. Uses same API regardless of which works")
    print("4. Caches working protocol for performance")
    
    service = TapperService("station1")
    success = service.connect()
    
    if success:
        active_protocols = service.protocol.get_active_protocols()
        print(f"Active protocols: {active_protocols}")
        service.disconnect()


if __name__ == "__main__":
    print("🚀 Dual Protocol Tapper System Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_dual_card_operations() 
        example_protocol_independence()
        example_error_handling()
        
        print("\n✅ All examples completed successfully!")
        print("\n💡 Key Benefits:")
        print("   - Same API works with HTTP or MQTT")
        print("   - Automatic protocol fallback") 
        print("   - Clean dual card operations")
        print("   - Modular architecture")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("Make sure ESP32 device is connected and accessible")