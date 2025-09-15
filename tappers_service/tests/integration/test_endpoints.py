#!/usr/bin/env python3
"""
Test ESP32 endpoints one by one to see what device returns.
"""

import requests
import time

ESP32_IP = "10.0.0.149"
BASE_URL = f"http://{ESP32_IP}"

def test_endpoint(endpoint, method="GET", params=None):
    """Test a single endpoint and show response."""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, params=params, timeout=5)
        
        print(f"✅ {method} {endpoint}")
        print(f"   Response: {response.text.strip()}")
        print(f"   Status Code: {response.status_code}")
        return response.text.strip()
    except Exception as e:
        print(f"❌ {method} {endpoint}: {e}")
        return None

def main():
    print("🔧 ESP32 Endpoint Testing")
    print("=========================")
    print(f"Testing device: {BASE_URL}")
    print()
    
    # Test /status
    print("📊 TESTING /status")
    print("-" * 20)
    status = test_endpoint("/status")
    print()
    
    input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")