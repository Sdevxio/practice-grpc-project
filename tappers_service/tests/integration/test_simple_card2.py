#!/usr/bin/env python3
"""
Simple Card 2 test - just tap without reset to middle.
Based on discovery that tapping is stable without full reset.
"""

import time
import sys
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system.controller.tapper_service import TapperService

def test_simple_card2_test():
    """Simple Card 2 tap test - no reset to middle."""
    
    print("🔴 Simple Card 2 Test (No Reset)")
    print("================================")
    
    # Connect to tapper
    tapper = TapperService("station1")
    tapper.connect()
    
    print(f"✅ Connected via {tapper.protocol.protocol_name}")
    print(f"Status: {tapper.protocol.get_status()}")
    
    # print("\n🔵 Card 1 Tap (using calibrated middle)")
    # tapper.protocol.send_command("tap_card1")
    # time.sleep(5.0)  # Wait for complete sequence
    #
    # print(f"Status after Card 1: {tapper.protocol.get_status()}")
    #
    # print("\n🔄 Test reset to captured middle")
    # tapper.protocol.send_command("reset_to_middle")
    # time.sleep(3.0)  # Wait for reset
    #
    # print(f"Status after reset: {tapper.protocol.get_status()}")
    
    print("\n🔴 Card 2 Tap (using calibrated middle)")
    tapper.protocol.send_command("tap_card2")
    max_wait: int = 10
    for _ in range(max_wait * 10):  # Check every 100ms for max_wait seconds
        status = tapper.protocol.get_status()
        if status in ["idle", "retracted"] or "Operation: idle" in status:
            return
        time.sleep(0.1)
    # time.sleep(5.0)  # Wait for complete sequence

    print(f"\n🎯 Final status: {tapper.protocol.get_status()}")
    tapper.disconnect()
