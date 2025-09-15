#!/usr/bin/env python3
"""
Live ESP32 Tapper Calibration Monitor
Monitors ESP32 status in real-time during calibration process
"""

import requests
import time
import sys
import os
from datetime import datetime

class ESP32Monitor:
    def __init__(self, esp32_ip="10.0.0.149"):
        self.esp32_ip = esp32_ip
        self.base_url = f"http://{esp32_ip}"
        self.last_status = ""
        
    def get_status(self):
        """Get current ESP32 status"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=2)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException as e:
            return f"ERROR: {e}"
        return "No response"
    
    def get_debug_info(self):
        """Get detailed debug information"""
        try:
            response = requests.get(f"{self.base_url}/debug", timeout=2)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException as e:
            return f"ERROR: {e}"
        return "No response"
    
    def send_command(self, command):
        """Send command to ESP32 and return response"""
        try:
            response = requests.get(f"{self.base_url}/{command}", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException as e:
            return f"ERROR: {e}"
        return "No response"
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self):
        """Display monitoring header"""
        print("=" * 70)
        print(f"ESP32 Tapper Live Monitor - {datetime.now().strftime('%H:%M:%S')}")
        print(f"Device: {self.esp32_ip}")
        print("=" * 70)
    
    def monitor_loop(self, refresh_interval=1.0):
        """Main monitoring loop with live updates"""
        print(f"Starting live monitor for ESP32 at {self.esp32_ip}")
        print("Press Ctrl+C to exit")
        print()
        
        try:
            while True:
                self.clear_screen()
                self.display_header()
                
                # Get current status
                current_status = self.get_status()
                
                print(f"Current Status: {current_status}")
                
                # Show status change indicator
                if current_status != self.last_status and self.last_status:
                    print(f"Status Changed: {self.last_status} → {current_status}")
                    print()
                
                self.last_status = current_status
                
                print("\nAvailable Commands:")
                print("  manual_extend    - Start manual extend")
                print("  manual_retract   - Start manual retract")  
                print("  manual_stop      - Stop motor")
                print("  capture_middle   - Set current position as middle")
                print("  reset           - Reset to middle position")
                print("  card1           - Tap Card 1")
                print("  card2           - Tap Card 2") 
                print("  power_usb       - Set USB power mode")
                print("  power_12v       - Set 12V power mode")
                print("  debug           - Show debug info")
                print()
                print("Press Ctrl+C to exit monitor")
                
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    
    def interactive_mode(self):
        """Interactive command mode"""
        print(f"ESP32 Interactive Mode - Device: {self.esp32_ip}")
        print("Type commands or 'quit' to exit")
        print()
        
        while True:
            try:
                # Show current status
                status = self.get_status()
                print(f"Status: {status}")
                
                # Get user input
                command = input("Enter command: ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command == 'debug':
                    debug_info = self.get_debug_info()
                    print(debug_info)
                elif command == 'monitor':
                    self.monitor_loop()
                    return
                elif command:
                    response = self.send_command(command)
                    print(f"Response: {response}")
                    
                    # Wait a moment for status to update
                    time.sleep(0.5)
                
                print()
                
            except KeyboardInterrupt:
                break
        
        print("Interactive mode ended.")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "10.0.0.149"
    
    monitor = ESP32Monitor(ip)
    
    # Test connection first
    print(f"Testing connection to ESP32 at {ip}...")
    status = monitor.get_status()
    if "ERROR" in status:
        print(f"Cannot connect to ESP32: {status}")
        return
    
    print(f"Connected! Current status: {status}")
    print()
    
    # Ask user for mode
    print("Select mode:")
    print("1. Live monitor (auto-refresh)")
    print("2. Interactive command mode")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        monitor.monitor_loop()
    else:
        monitor.interactive_mode()

if __name__ == "__main__":
    main()