#!/usr/bin/env python3
"""
Adaptive timing system that learns from drift patterns and adjusts automatically.
Tracks position drift and compensates timing for next tap.
"""

import time
import sys
import requests
sys.path.append('/Users/admin/Tapper_Project')

from tappers_service.tapper_system.controller.tapper_service import TapperService

class AdaptiveTapper:
    def __init__(self, esp32_ip="10.0.0.149"):
        self.esp32_ip = esp32_ip
        self.base_url = f"http://{esp32_ip}"
        
        # Base timing values (starting point)
        self.retract_time = 1400  # To Card 2
        self.extend_time = 1395   # Back to middle
        
        # Drift tracking
        self.drift_history = []
        self.learning_rate = 0.1  # How quickly to adapt
        
    def wait_for_operation(self, duration_ms):
        """Wait for timed operation to complete."""
        wait_time = (duration_ms + 100) / 1000.0
        time.sleep(wait_time)
    
    def detect_drift(self, tapper):
        """Analyze current position vs expected middle position."""
        status = tapper.protocol.get_status()
        print(f"   Current status: {status}")
        
        # Simple drift detection based on status
        if "middle" in status.lower():
            return 0  # No drift detected
        elif "extended" in status.lower() or "card1" in status.lower():
            return +1  # Drifted toward extension (too far forward)
        elif "retracted" in status.lower() or "card2" in status.lower():
            return -1  # Drifted toward retraction (too far back)
        else:
            return 0  # Unknown, assume no drift
    
    def adapt_timing(self, drift_direction):
        """Adjust timing based on detected drift."""
        if drift_direction > 0:  # Drifted toward extension
            # We went too far forward, so reduce extend time
            self.extend_time = max(1350, self.extend_time - 5)
            print(f"   🔧 Adapted: extend_time → {self.extend_time}ms (reduced - went too far)")
        elif drift_direction < 0:  # Drifted toward retraction  
            # We didn't go far enough forward, so increase extend time
            self.extend_time = min(1420, self.extend_time + 5)
            print(f"   🔧 Adapted: extend_time → {self.extend_time}ms (increased - didn't go far enough)")
        
        # Track drift for learning
        self.drift_history.append(drift_direction)
        if len(self.drift_history) > 5:
            self.drift_history.pop(0)  # Keep only last 5
    
    def single_adaptive_tap(self, tapper, tap_num):
        """Perform single tap with adaptive timing."""
        print(f"\n🔴 Adaptive Tap #{tap_num}")
        print(f"   Using timings: retract={self.retract_time}ms, extend={self.extend_time}ms")
        
        # Step 1: Retract to Card 2
        requests.post(f"{self.base_url}/retract_for_time?duration={self.retract_time}")
        self.wait_for_operation(self.retract_time)
        
        # Step 2: Return to middle  
        requests.post(f"{self.base_url}/extend_for_time?duration={self.extend_time}")
        self.wait_for_operation(self.extend_time)
        
        # Step 3: Detect and adapt
        drift = self.detect_drift(tapper)
        if drift != 0:
            self.adapt_timing(drift)
        else:
            print("   ✅ No drift detected")

def test_adaptive_tapping():
    """Test adaptive timing system."""
    
    print("🧠 Adaptive Timing Test")
    print("======================")
    print("System will learn from drift and adjust timing automatically")
    
    tapper_service = TapperService("station1")
    tapper_service.connect()
    
    adaptive_tapper = AdaptiveTapper()
    
    # Check starting position
    print(f"\n🔍 Starting position: {tapper_service.protocol.get_status()}")
    
    # Perform 8 adaptive taps
    for i in range(1, 9):
        adaptive_tapper.single_adaptive_tap(tapper_service, i)
        time.sleep(0.2)  # Brief pause between taps
    
    print(f"\n🎯 Final position: {tapper_service.protocol.get_status()}")
    print(f"📊 Final timings: retract={adaptive_tapper.retract_time}ms, extend={adaptive_tapper.extend_time}ms")
    print(f"📈 Drift history: {adaptive_tapper.drift_history}")
    
    tapper_service.disconnect()

if __name__ == "__main__":
    try:
        test_adaptive_tapping()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        sys.exit(0)