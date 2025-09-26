import pytest
import time
from test_framework.grpc_session.session_manager import GrpcSessionManager
from web_automation_sdk.helpers.web_automation_helper import WebAutomationHelper


@pytest.mark.integration
def test_simple_navigation():
    """
    Simplified test to isolate and fix browser context issues.
    """
    expected_user = "admin"
    station_id = "station1"
    session_manager = GrpcSessionManager(station_id=station_id)
    session_context = session_manager.create_session(expected_user, timeout=30)
    
    web_automation_client = session_context.user_context.web_automation
    
    print(f"📱 Client connected: {web_automation_client.is_connected()}")
    print(f"🎯 Target user: {web_automation_client.target_user}")
    
    try:
        # Try a simple script execution first
        print("🚀 Testing simple script execution...")
        result = web_automation_client.execute_script("document.title", return_value=True)
        print(f"📜 Script result: {result}")
        
        if result and result.get("success"):
            print("✅ Basic script execution works!")
            
            # Now try navigation
            print("🌐 Testing navigation...")
            nav_result = web_automation_client.execute_script(
                "window.location.href = 'https://httpbin.org/html'",
                return_value=False
            )
            print(f"🧭 Navigation result: {nav_result}")
            
            if nav_result and nav_result.get("success"):
                print("✅ Navigation script executed!")
                
                # Wait a moment for navigation
                time.sleep(2)
                
                # Check if navigation worked
                title_result = web_automation_client.execute_script("document.title", return_value=True)
                print(f"📑 Page title after navigation: {title_result}")
            else:
                print("❌ Navigation failed")
        else:
            print("❌ Basic script execution failed")
            
    except Exception as e:
        print(f"💥 Test error: {e}")
        raise


if __name__ == "__main__":
    test_simple_navigation()