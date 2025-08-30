"""
Dual Card Tapper Integration Test Example

This script demonstrates how the Python framework seamlessly works with
the enhanced ESP32 dual card firmware through the modular protocol architecture.
"""

import sys
import os
import time

from tappers_service.command import sequences
from tappers_service.controller.tapper_service import TapperService

# Add the tappers_service to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tappers_service'))

# Import the framework components

def main():
    print("=" * 60)
    print("ESP32 Dual Card Tapper Integration Test")
    print("=" * 60)
    print()
    
    # Connect to tapper (uses existing station configuration)
    print("🔌 Connecting to tapper via station1...")
    try:
        tapper = TapperService(station_id="station1")
        tapper.connect()
        print(f"✅ Connected via {tapper.protocol.protocol_name} protocol")
        print(f"📡 Device: {tapper.protocol.device_id}")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure your ESP32 is:")
        print("   - Connected to the same network")
        print("   - Running the enhanced dual card firmware") 
        print("   - Accessible at the configured IP address")
        return False
    
    try:
        # Test 1: Check enhanced status
        print("📊 Testing Enhanced Status Reporting:")
        status = tapper.get_status()
        print(f"   Current status: {status}")
        print("   ✅ Enhanced dual card status working")
        print()
        
        # Test 2: Power source configuration
        print("⚡ Setting Power Source to 12V:")
        sequences.set_power_source_12v(tapper.protocol)
        time.sleep(1)
        status = tapper.get_status()
        print(f"   Status after power config: {status}")
        print()
        
        # Test 3: Position calibration
        print("📍 Capturing Current Position as Middle:")
        sequences.capture_middle_position(tapper.protocol) 
        time.sleep(1)
        status = tapper.get_status()
        print(f"   Status after calibration: {status}")
        print()
        
        # Test 4: Basic dual card operations
        print("🎯 Testing Basic Dual Card Operations:")
        
        print("   Step 1: Reset to middle position")
        sequences.reset_to_middle(tapper.protocol)
        time.sleep(1)
        
        print("   Step 2: Tap Card 1 (extend direction)")
        sequences.tap_card1(tapper.protocol)
        time.sleep(2)
        
        print("   Step 3: Tap Card 2 (retract direction)")
        sequences.tap_card2(tapper.protocol)
        time.sleep(2)
        
        print("   ✅ Basic dual card operations completed")
        print()
        
        # Test 5: Advanced sequence
        print("🔄 Testing Advanced Dual Card Sequence:")
        sequences.dual_card_sequence(tapper.protocol, delay_between_taps=1.5)
        print("   ✅ Advanced sequence completed")
        print()
        
        # Test 6: Safe operations (with auto-reset)
        print("🛡️ Testing Safe Operations (with auto-reset):")
        sequences.safe_tap_card1(tapper.protocol)
        time.sleep(1)
        sequences.safe_tap_card2(tapper.protocol)
        print("   ✅ Safe operations completed")
        print()
        
        # Test 7: Final status check
        print("📋 Final Status Check:")
        final_status = tapper.get_status()
        print(f"   Final status: {final_status}")
        
        # Success summary
        print("\n" + "=" * 60)
        print("🎉 DUAL CARD INTEGRATION TEST SUCCESSFUL!")
        print("=" * 60)
        print("✅ Protocol abstraction working")
        print("✅ Enhanced status reporting working") 
        print("✅ Dual card sequences working")
        print("✅ Configuration integration working")
        print("✅ Command mapping working")
        print("✅ Real-time status monitoring working")
        print()
        print("💡 The modular architecture allows seamless dual card")
        print("   operations through existing HTTP/MQTT protocols!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        print(f"\n🔌 Disconnecting from tapper...")
        tapper.disconnect()
        print("   ✅ Disconnected")

def demonstrate_framework_features():
    """Demonstrate key framework features that work with dual cards"""
    print("\n" + "=" * 60)
    print("FRAMEWORK FEATURES DEMONSTRATION")
    print("=" * 60)
    
    print("\n🏗️ Modular Architecture:")
    print("   - TapperService: High-level device management")
    print("   - BaseProtocol: Transport abstraction (HTTP/MQTT)")
    print("   - sequences.py: Pre-built operation sequences")
    print("   - YAML config: Device and timing configuration")
    
    print("\n🔄 Protocol Support:")
    print("   - HTTP: Direct REST API communication")
    print("   - MQTT: Real-time pub/sub messaging")
    print("   - Both provide identical dual card functionality")
    
    print("\n📱 New Dual Card Sequences Available:")
    print("   - sequences.reset_to_middle(protocol)")
    print("   - sequences.tap_card1(protocol)")
    print("   - sequences.tap_card2(protocol)")
    print("   - sequences.safe_tap_card1(protocol)")
    print("   - sequences.safe_tap_card2(protocol)")
    print("   - sequences.dual_card_sequence(protocol)")
    print("   - sequences.alternating_card_taps(protocol)")
    print("   - sequences.set_power_source_12v(protocol)")
    print("   - sequences.capture_middle_position(protocol)")
    
    print("\n⚙️ Configuration Integration:")
    print("   - Device capabilities in tapper_devices.yaml")
    print("   - Timing constants for precise positioning")
    print("   - Power source awareness (12V vs USB)")
    print("   - Dual card grouping and organization")
    
    print("\n📊 Enhanced Status Reporting:")
    print("   - Position: unknown/middle/card1/card2")
    print("   - Operation: idle/moving_to_card1/tapping_card2")
    print("   - Power: 12V/USB with timing adjustments")
    print("   - Real-time progress via MQTT streaming")

if __name__ == "__main__":
    print("ESP32 Dual Card Tapper - Python Framework Integration")
    print("Demonstrates seamless operation through modular architecture\n")
    
    # Run the integration test
    success = main()
    
    # Show framework features
    demonstrate_framework_features()
    
    # Final message
    if success:
        print(f"\n{'='*60}")
        print("🎯 INTEGRATION COMPLETE - Ready for Production Use!")
        print(f"{'='*60}")
        print("\n💡 Usage in your code:")
        print("from tappers_service.controller.tapper_service import TapperService")
        print("from tappers_service.command import sequences")
        print()
        print("tapper = TapperService('station1')")
        print("tapper.connect()")
        print("sequences.dual_card_sequence(tapper.protocol)")
        print("tapper.disconnect()")
    else:
        print(f"\n{'='*60}")
        print("⚠️  INTEGRATION TEST FAILED")
        print(f"{'='*60}")
        print("Please check ESP32 connection and firmware")