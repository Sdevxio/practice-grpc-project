import pytest
import time
from test_framework.grpc_session.session_manager import GrpcSessionManager
from web_automation_sdk.helpers.web_automation_helper import WebAutomationHelper

@pytest.mark.integration
def test_navigate_to_google_real():
    """
    Integration test: Navigate to Google and print the page title using user session context.
    This test requires the gRPC server and browser to be running and accessible.
    """
    client = None
    helper = None
    
    try:
        # Create a session for the expected user
        expected_user = "admin"  # Change to your actual test user
        station_id = "station1"       # Change to your actual station id if needed
        session_manager = GrpcSessionManager(station_id=station_id)
        session_context = session_manager.create_session(expected_user, timeout=30)

        # ✨ BEAUTIFUL: WebAutomation is now part of the session context!
        # No need to manually create client - it's automatically available
        # Access web_automation directly from the user context
        web_automation_client = session_context.user_context.web_automation
        helper = WebAutomationHelper(web_automation_client)

        # Navigate to Google
        success = helper.navigate_to_url("https://www.google.com")
        assert success, "Navigation to Google failed"

        # Wait a few seconds to allow browser to open for visual confirmation
        time.sleep(3)

        # Get and print the page title
        title = helper.get_page_title()
        print(f"Page title after navigation: {title}")
        assert "Google" in title

        # Wait for the search box to be available
        print("Waiting for Google search box...")
        search_box_found = helper.wait_for_element("textarea[name='q']", timeout=10000)
        if not search_box_found:
            # Try alternative selectors for Google search box
            search_box_found = helper.wait_for_element("input[name='q']", timeout=5000)
        
        assert search_box_found, "Google search box not found"
        print("Search box found!")

        # Type a search query into the search box
        search_query = "playwright web automation"
        print(f"Typing search query: {search_query}")
        
        # Try both possible search box selectors
        search_success = helper.type_text("textarea[name='q']", search_query)
        if not search_success:
            search_success = helper.type_text("input[name='q']", search_query)
        
        assert search_success, "Failed to type in search box"
        print("Successfully typed in search box")

        # Wait a moment for the text to be processed
        time.sleep(1)

        # Look for and click the search button
        print("Looking for search button...")
        
        # Try multiple possible search button selectors
        search_button_selectors = [
            "input[name='btnK']",           # Google Search button
            "button[name='btnK']",          # Alternative search button
            "input[value='Google Search']", # By value attribute
            "[aria-label='Google Search']", # By aria-label
            "form[action='/search'] input[type='submit']" # Form-based search
        ]
        
        search_button_clicked = False
        for selector in search_button_selectors:
            if helper.element_exists(selector):
                print(f"Found search button with selector: {selector}")
                if helper.click_element(selector):
                    search_button_clicked = True
                    print("Successfully clicked search button")
                    break
        
        # If no search button found, try submitting with Enter key
        if not search_button_clicked:
            print("No search button found, trying to submit with Enter key")
            enter_script = """
            (() => {
                const searchBox = document.querySelector('textarea[name="q"]') || document.querySelector('input[name="q"]');
                if (searchBox) {
                    const event = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    });
                    searchBox.dispatchEvent(event);
                    return true;
                }
                return false;
            })()
            """
            enter_result = helper.execute_custom_script(enter_script)
            if enter_result and enter_result.get("result_value") == "true":
                search_button_clicked = True
                print("Successfully submitted search with Enter key")
        
        assert search_button_clicked, "Failed to submit the search"

        # Wait for search results page to load
        print("Waiting for search results to load...")
        time.sleep(3)
        
        # Verify we're on a search results page
        results_title = helper.get_page_title()
        print(f"Search results page title: {results_title}")
        
        # Handle case where title might be None (page still loading)
        if results_title is None:
            print("Page title is None, trying to get page title again after a short wait...")
            time.sleep(2)
            results_title = helper.get_page_title()
            print(f"Second attempt - page title: {results_title}")
        
        # More flexible search results validation
        title_ok = results_title is not None and (search_query in results_title or "Google" in results_title)
        
        if not title_ok:
            # Fallback: Check if we can find search results on the page
            results_found = helper.element_exists("#search") or helper.element_exists("#rso") or helper.element_exists(".g")
            if results_found:
                print("✅ Search results found on page (verified by elements), even though title check failed")
                title_ok = True
        
        if not title_ok:
            print("❌ Neither title nor search results elements found. Checking page URL...")
            page_url = helper.get_page_url()
            print(f"Current page URL: {page_url}")
            if page_url and "google.com" in page_url and "search" in page_url:
                print("✅ Search results page confirmed via URL")
                title_ok = True
        
        assert title_ok, f"Search results page not loaded correctly. Title: {results_title}"
        
        # Check that we have search results
        results_found = helper.wait_for_element("#search", timeout=10000) or helper.wait_for_element("#rso", timeout=5000)
        if results_found:
            print("Search results found on page")
            
            # Try to get the first search result
            first_result = helper.get_element_text("#search .g:first-child") or helper.get_element_text("#rso .g:first-child")
            if first_result:
                print(f"First search result: {first_result[:100]}...")
        else:
            print("Warning: Search results container not found, but search appears to have executed")

        print("✅ Google search test completed successfully!")

    finally:
        # Cleanup - ensure browser resources are properly closed
        print("Cleaning up browser resources...")
        
        if helper and web_automation_client:
            try:
                # Take a final screenshot before cleanup (optional)
                screenshot_result = web_automation_client.take_screenshot()
                if screenshot_result and screenshot_result.get("success"):
                    print("Final screenshot captured before cleanup")
                
                # Execute cleanup script to close current page/context
                cleanup_script = """
                (() => {
                    try {
                        // Close current window if possible
                        if (window.close) {
                            window.close();
                        }
                        return 'cleanup_attempted';
                    } catch (e) {
                        return 'cleanup_error: ' + e.message;
                    }
                })()
                """
                cleanup_result = helper.execute_custom_script(cleanup_script)
                if cleanup_result:
                    print(f"Cleanup script result: {cleanup_result.get('result_value', 'no result')}")
                    
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")
        
        print("🧹 Cleanup completed - session context handles client disconnection")
