#!/usr/bin/env python3
"""
Custom timing test script for dual card tapping.
Controls ESP32 directly with custom timing parameters without config file changes.
"""

import time
import sys
import requests
from typing import Optional

class DirectTapperControl:
    """Direct control of ESP32 tapper with custom timing."""
    
    def __init__(self, esp32_ip: str = "10.0.0.149"):
        self.base_url = f"http://{esp32_ip}"
        self.session = requests.Session()
        
    def send_command(self, command: str, duration_ms: Optional[int] = None) -> bool:
        """Send command to ESP32 via HTTP."""
        try:
            if duration_ms:
                url = f"{self.base_url}/{command}?duration={duration_ms}"
                response = self.session.post(url, timeout=10)
            else:
                url = f"{self.base_url}/{command}"
                response = self.session.get(url, timeout=10)
            
            print(f"✅ {command}" + (f" ({duration_ms}ms)" if duration_ms else ""))
            return response.status_code == 200
        except Exception as e:
            print(f"❌ {command}: {e}")
            return False
    
    def get_status(self) -> str:
        """Get current ESP32 status."""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=5)
            return response.text.strip()
        except:
            return "unknown"
    
    def wait_for_idle(self, max_wait: int = 10) -> bool:
        """Wait for ESP32 to return to idle state."""
        print("Waiting for operation to complete...")
        for i in range(max_wait * 10):
            status = self.get_status()
            if "idle" in status.lower():
                print(f"✅ Operation completed after {(i+1)*0.1:.1f}s")
                return True
            time.sleep(0.1)
        
        print(f"⚠️ Operation did not complete within {max_wait}s")
        return False
    
    def custom_tap_card1(self, 
                        extend_ms: int = 1100, 
                        pause_ms: int = 3000, 
                        retract_ms: int = 1100,
                        reverse_offset_ms: int = 50):
        """
        Custom Card 1 tap with relay-style control and drift compensation.
        
        :param extend_ms: Time to extend to card (default 1100ms)
        :param pause_ms: Time to pause at card (default 3000ms) 
        :param retract_ms: Time to retract back to middle (default 1100ms)
        :param reverse_offset_ms: Compensation for return movement (default 50ms)
        """
        print(f"\n🔵 CARD 1 TAP (RELAY STYLE): extend {extend_ms}ms → pause {pause_ms}ms → retract {retract_ms-reverse_offset_ms}ms")
        
        # Step 1: Reset to middle (relay-style full reset)
        print("Step 1: Full reset to middle (relay style)")
        self.send_command("retract")  # Start full retract
        time.sleep(3.0)               # Full retract time
        self.send_command("stop")     # Stop motor
        
        self.send_command("extend")   # Start extend to middle  
        time.sleep(1.284)             # Half of full extend time
        self.send_command("stop")     # Stop at middle
        
        # Step 2: Extend to Card 1 (relay style)
        print(f"Step 2: Extending to Card 1 ({extend_ms}ms)")
        self.send_command("extend")
        time.sleep(extend_ms / 1000.0)
        self.send_command("stop")
        
        # Step 3: Pause at Card 1 (contact time)
        print(f"Step 3: Pausing at Card 1 for {pause_ms}ms (CONTACT TIME)")
        time.sleep(pause_ms / 1000.0)
        
        # Step 4: Retract back to middle (with drift compensation)
        compensated_retract = retract_ms - reverse_offset_ms
        print(f"Step 4: Retracting to middle ({compensated_retract}ms, -{reverse_offset_ms}ms offset)")
        self.send_command("retract")
        time.sleep(compensated_retract / 1000.0)
        self.send_command("stop")
        
        print("✅ Card 1 tap completed (relay style)\n")
    
    def custom_tap_card2(self, 
                        retract_ms: int = 1300, 
                        pause_ms: int = 3000, 
                        extend_ms: int = 1300,
                        reverse_offset_ms: int = 50):
        """
        Custom Card 2 tap with relay-style control and drift compensation.
        
        :param retract_ms: Time to retract to card (default 1300ms)
        :param pause_ms: Time to pause at card (default 3000ms)
        :param extend_ms: Time to extend back to middle (default 1300ms)
        :param reverse_offset_ms: Compensation for return movement (default 50ms)
        """
        print(f"\n🔴 CARD 2 TAP (RELAY STYLE): retract {retract_ms}ms → pause {pause_ms}ms → extend {extend_ms-reverse_offset_ms}ms")
        
        # Step 1: Reset to middle (relay-style full reset)
        print("Step 1: Full reset to middle (relay style)")
        self.send_command("retract")  # Start full retract
        time.sleep(3.0)               # Full retract time
        self.send_command("stop")     # Stop motor
        
        self.send_command("extend")   # Start extend to middle
        time.sleep(1.284)             # Half of full extend time  
        self.send_command("stop")     # Stop at middle
        
        # Step 2: Retract to Card 2 (relay style)
        print(f"Step 2: Retracting to Card 2 ({retract_ms}ms)")
        self.send_command("retract")
        time.sleep(retract_ms / 1000.0)
        self.send_command("stop")
        
        # Step 3: Pause at Card 2 (contact time)
        print(f"Step 3: Pausing at Card 2 for {pause_ms}ms (CONTACT TIME)")
        time.sleep(pause_ms / 1000.0)
        
        # Step 4: Extend back to middle (with drift compensation)
        compensated_extend = extend_ms - reverse_offset_ms
        print(f"Step 4: Extending to middle ({compensated_extend}ms, -{reverse_offset_ms}ms offset)")
        self.send_command("extend")
        time.sleep(compensated_extend / 1000.0)
        self.send_command("stop")
        
        print("✅ Card 2 tap completed (relay style)\n")

def main():
    """Test optimized timing to prevent rapid login/logout."""
    tapper = DirectTapperControl()
    
    print("🔧 Custom Timing Tapper Test")
    print("============================")
    print(f"Connected to: {tapper.base_url}")
    print(f"Current status: {tapper.get_status()}")
    
    # Test with longer pause time to prevent rapid login/logout
    print("\n🔵 Testing Card 1 with 3-second pause:")
    tapper.custom_tap_card1(pause_ms=3000)
    
    time.sleep(3)  # Wait between tests
    
    print("\n🔴 Testing Card 2 with 3-second pause:")
    tapper.custom_tap_card2(pause_ms=3000)
    
    print("\n✅ Test completed!")
    print("Check if 3-second pause prevented rapid login/logout.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        sys.exit(0)