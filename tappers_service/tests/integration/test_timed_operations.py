#!/usr/bin/env python3
"""
Test using ESP32 timed operations for full Python timing control.
This mimics the relay approach - Python controls all timing.
"""

import time
import sys
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system.controller.tapper_service import TapperService

def test_timed_operations():
    """Test card tapping using extend_for_time and retract_for_time."""
    
    print("⏰ Timed Operations Test (Python-Controlled Timing)")
    print("===================================================")
    
    # Connect to tapper
    tapper = TapperService("station1")
    tapper.connect()

    import requests
    
    def wait_for_timed_operation(duration_ms):
        """Wait for timed operation to complete."""
        wait_time = (duration_ms + 100) / 1000.0  # Add 100ms buffer, convert to seconds
        print(f"   Waiting {wait_time:.1f}s for operation to complete...")
        time.sleep(wait_time)
    
    # Check initial status
    print(f"🔍 Initial status: {tapper.protocol.get_status()}")
    
    # Step 1: Retract to Card 2 position 
    print("🔴 Retracting to Card 2...")
    response = requests.post(f"http://10.0.0.149/retract_for_time?duration=1400")
    print(f"   Response: {response.status_code}")
    wait_for_timed_operation(1400)
    print(f"   Status after retract: {tapper.protocol.get_status()}")
    
    # Step 2: Extend back to middle (instant return)
    print("🏠 Extending back to middle...")
    response = requests.post(f"http://10.0.0.149/extend_for_time?duration=1385")
    print(f"   Response: {response.status_code}")
    wait_for_timed_operation(1385)
    print(f"   Status after extend: {tapper.protocol.get_status()}")
    
    print("✅ Timed tap sequence complete!")
    
    tapper.disconnect()

if __name__ == "__main__":
    try:
        test_timed_operations()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.exit(1)