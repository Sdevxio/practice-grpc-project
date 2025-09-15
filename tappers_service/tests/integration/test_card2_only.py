#!/usr/bin/env python3
"""
Simple test for Card 2 tap only using relay-matching approach.
"""

import time
import sys
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system.controller.tapper_service import TapperService

def test_card2_only():
    """Test Card 2 multiple times to check for drift (relay style)."""
    
    print("🔴 Card 2 Drift Test (Relay Style with 3s settle)")
    print("================================================")
    
    # Connect to tapper
    tapper = TapperService("station1")
    tapper.connect()
    
    print(f"✅ Connected via {tapper.protocol.protocol_name}")
    print(f"Status: {tapper.protocol.get_status()}")
    
    # Test 5 consecutive Card 2 taps to check for drift

    # # # Step 1: Full reset to home (relay style)
    # print("🔄 Step 1: Full reset to home")
    # tapper.protocol.send_command("retract")  # Full retract
    # time.sleep(3.0)
    # tapper.protocol.send_command("stop")
    # time.sleep(3.0)  # RELAY SECRET: 3-second settle time
    #
    # tapper.protocol.send_command("extend")   # Extend to middle/home
    # time.sleep(1.49)  # pen_to_home_time from relay
    # tapper.protocol.send_command("stop")
    # time.sleep(3.0)  # RELAY SECRET: 3-second settle time
    #
    # Step 2: Move to Card 2
    print("🔴 Step 2: Move to Card 2")
    tapper.protocol.send_command("retract")  # Move to Card 2
    time.sleep(0.9)  # c2_direct_to_rdr2_time from relay
    tapper.protocol.send_command("stop")
    time.sleep(3.0)  # RELAY SECRET: 3-second settle time

    # Step 3: Pause at Card 2
    print("⏸️  Step 3: Pause at Card 2 (3 seconds)")
    time.sleep(0.10)  # Contact time for login

    # Step 4: Return to home with drift compensation
    print("🔄 Step 4: Return to home (with offset)")
    tapper.protocol.send_command("extend")   # Return to home
    time.sleep(0.85)  # 0.9 - 0.05 reverse offset (line 567)
    tapper.protocol.send_command("stop")
    time.sleep(3.0)  # RELAY SECRET: 3-second settle time


    print(f"\n🎯 Final status: {tapper.protocol.get_status()}")
    print("Check if position drifted after 5 consecutive taps!")

    tapper.disconnect()

if __name__ == "__main__":
    try:
        test_card2_only()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)