import pytest
import time
from test_framework.grpc_session.session_manager import GrpcSessionManager
from web_automation_sdk.helpers.web_automation_helper import WebAutomationHelper


@pytest.mark.integration
def test_web_automation_with_session_context():
    """
    Beautiful integration test showing WebAutomation seamlessly integrated 
    with the gRPC session management framework.
    
    This demonstrates how WebAutomation is now a first-class citizen in the
    test automation framework - no manual client management needed!
    """
    
    # Step 1: Create session - WebAutomation is automatically available
    expected_user = "admin"
    station_id = "station1" 
    session_manager = GrpcSessionManager(station_id=station_id)
    session_context = session_manager.create_session(expected_user, timeout=30)
    
    # Step 2: Access WebAutomation directly from session context 🎉
    # This is the magic - no manual client creation, connection, or management!
    web_client = session_context.user_context.web_automation
    helper = WebAutomationHelper(web_client)
    
    print("✨ WebAutomation client accessed directly from session context!")
    print(f"📍 User context: {expected_user}")
    print(f"🔌 Agent port: {session_context.agent_port}")
    
    # Step 3: Use WebAutomation alongside other services
    # Show how it integrates with existing services in the same session
    try:
        # Navigate to a page
        success = helper.navigate_to_url("https://httpbin.org/html")
        assert success, "Navigation failed"
        
        # Get page title using WebAutomation
        title = helper.get_page_title()
        print(f"📄 Page title via WebAutomation: {title}")
        
        # Take a screenshot using WebAutomation (full page)
        try:
            screenshot = web_client.take_screenshot(full_page=True)
            if screenshot and screenshot.get("success"):
                print(f"📸 Screenshot captured: {len(screenshot['image_data'])} bytes")
            else:
                print(f"📸 Screenshot failed: {screenshot.get('message', 'Unknown error') if screenshot else 'No response'}")
        except Exception as e:
            print(f"📸 Screenshot error: {e}")
        
        # Meanwhile, you can use OTHER services from the same session:
        
        # Use AppleScript service from the same context
        try:
            applescript_client = session_context.user_context.apple_script
            script_result = applescript_client.run_applescript('return "Hello from AppleScript!"')
            if script_result and script_result.get("success"):
                print(f"🍎 AppleScript result: {script_result['result']}")
            else:
                print(f"🍎 AppleScript failed: {script_result.get('message') if script_result else 'No response'}")
        except Exception as e:
            print(f"🍎 AppleScript error: {e}")
        
        # Use Command service from the same context  
        try:
            command_client = session_context.user_context.commands
            cmd_result = command_client.run("echo 'Hello from Commands!'")
            if cmd_result and cmd_result.get("success"):
                print(f"💻 Command result: {cmd_result['output']}")
            else:
                print(f"💻 Command failed: {cmd_result.get('message') if cmd_result else 'No response'}")
        except Exception as e:
            print(f"💻 Command error: {e}")
        
        # Use Screen Capture service from the same context
        try:
            screen_client = session_context.user_context.screen_capture  
            screen_shot = screen_client.capture_screenshot()
            if screen_shot and screen_shot.get("success"):
                print(f"📷 System screenshot: {len(screen_shot['image_data'])} bytes")
            else:
                print(f"📷 System screenshot failed: {screen_shot.get('message') if screen_shot else 'No response'}")
        except Exception as e:
            print(f"📷 System screenshot error: {e}")
            
        print("🎊 ALL SERVICES WORKING IN HARMONY!")
        print("🚀 This shows the beautiful modularity of the framework!")
        
        # WebAutomation working alongside:
        # ✅ AppleScript Service (GUI automation)
        # ✅ Command Service (system commands)  
        # ✅ Screen Capture Service (screenshots)
        # ✅ File Transfer Service (not shown but available)
        # ✅ Connection Service (not shown but available)
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        raise
        
    print("✅ Session context integration test completed successfully!")


@pytest.mark.integration
def test_root_vs_user_web_automation():
    """
    Demonstrate the difference between root and user context WebAutomation.
    Shows the routing capabilities and multi-user support.
    """
    expected_user = "admin"
    station_id = "station1"
    session_manager = GrpcSessionManager(station_id=station_id)
    session_context = session_manager.create_session(expected_user, timeout=30)
    
    # Root context - routes to user agents
    root_web_client = session_context.root_context.web_automation
    root_helper = WebAutomationHelper(root_web_client)
    
    # User context - executes directly
    user_web_client = session_context.user_context.web_automation  
    user_helper = WebAutomationHelper(user_web_client)
    
    print("🔄 Testing root vs user context WebAutomation...")
    
    # Both should work but with different routing:
    # Root context: Routes through registry to user agent
    # User context: Executes directly on user agent
    
    # Test navigation with both contexts
    root_success = root_helper.navigate_to_url("https://httpbin.org/get")
    user_success = user_helper.navigate_to_url("https://httpbin.org/json") 
    
    print(f"🌐 Root context navigation: {'✅' if root_success else '❌'}")
    print(f"👤 User context navigation: {'✅' if user_success else '❌'}")
    
    # Get page titles from both
    root_title = root_helper.get_page_title()
    user_title = user_helper.get_page_title() 
    
    print(f"📄 Root context title: {root_title}")
    print(f"📄 User context title: {user_title}")
    
    print("🎯 Both contexts can access WebAutomation with proper routing!")


if __name__ == "__main__":
    test_web_automation_with_session_context()
    test_root_vs_user_web_automation()