import os
import re
import time

import pytest

from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts

# @pytest.mark.test_user("macos_lab_1")
@pytest.mark.auto_manage(False)
def test_complete_tap_to_login(login_state, session_manager, parse_log_file, prepare_log_file, test_config, test_logger):
    """
    Complete tap to login test - combines all verification steps using new framework
    """
    test_logger.info("Starting complete tap to login test")
    expected_user = test_config["expected_user"]
    manager, session_context = session_manager

    # STEP 1: Verify session establishment
    test_logger.info("STEP 1: Verifying session establishment")
    assert session_context is not None
    assert session_context.username == test_config["expected_user"]
    assert session_context.agent_port is not None
    assert session_context.root_context is not None
    assert session_context.user_context is not None
    test_logger.info(f"Session verified for user: {session_context.username}")

    # STEP 2: Perform login tap and verify using commands
    test_logger.info("STEP 2: Performing login tap and verifying using commands")
    login_state.ensure_logged_in(expected_user)

    time.sleep(2)
    result = session_context.root_context.command.get_logged_in_users()
    test_logger.info(f"Command execution result: {result}")
    assert result is not None, "Command result should not be None"

    logged_in_user = result.get("console_user")
    assert expected_user in logged_in_user
    test_logger.info("User verification using commands passed")

    # STEP 3: Verify user logged in using logs
    test_logger.info("STEP 3: Verifying user login using logs")

    # Wait for log entries to be written
    time.sleep(2)

    # Parse logs to find authentication events we just generated
    data_extractor, entries = parse_log_file(prepare_log_file)
    test_logger.info(f"Parsed {len(entries)} log entries")

    # Search for authentication entries
    domain = test_config.get("domains", {}).get('PEGASUS', 'default_domain')
    auth_pattern = f'PIDC authenticating with domain: "{domain}" username: "{expected_user}"'

    auth_entries = data_extractor.find_entries_containing(entries, "PIDC authenticating")
    if auth_entries:
        test_logger.info(f"Found {len(auth_entries)} authentication entries")
        data_extractor.log_messages(auth_entries, "Authentication Entries", limit=3)

    # Alternative check for session activation
    session_entries = data_extractor.find_entries_containing(entries, "sessionDidBecomeActive")
    if session_entries:
        test_logger.info(f"Found {len(session_entries)} session activation entries")

    auth_entry_found = len(auth_entries) > 0 or len(session_entries) > 0
    assert auth_entry_found, f"Required authentication log entry not found for user '{expected_user}'"

    # Search for card ID authentication entry
    card_entries = data_extractor.find_entries_containing(entries, "proxCard")
    card_entry_found = len(card_entries) > 0
    if card_entries:
        test_logger.info(f"Found {len(card_entries)} card authentication entries")
        data_extractor.log_messages(card_entries, "Card Entries", limit=2)

    assert card_entry_found, "Required card authentication log entry not found"
    test_logger.info("User and card verification using logs passed")

    # STEP 4: Verify user logged in using AppleScript
    test_logger.info("STEP 4: Verifying user login using AppleScript")
    script = '''
    tell application "System Events"
        tell process "Finder"
            set appleMenuItems to name of every menu item of menu "Apple" of menu bar 1
            return appleMenuItems as string
        end tell
    end tell'''

    script_result = session_context.user_context.apple_script.run_applescript(script=script)
    test_logger.info(f"AppleScript execution result: {script_result}")
    assert script_result["success"] == True
    applescript_output = script_result["stdout"]
    test_logger.info(f"AppleScript returned output: {applescript_output}")

    # Extract user from "Log Out username" pattern
    user_match = re.search(r'Log Out ([^â€¦]+)', applescript_output)
    if user_match:
        extracted_user = user_match.group(1)
        test_logger.info(f"Extracted user from AppleScript: {extracted_user}")
        assert extracted_user.lower() == expected_user.lower()
    else:
        # Fallback - check if user appears anywhere in output
        test_logger.info("Could not extract user from Log Out pattern, checking if user appears in output")
        assert expected_user in applescript_output
    test_logger.info("User verification using AppleScript passed")

    # STEP 5: Verify user logged in using UI screenshot
    test_logger.info("STEP 5: Verifying user login using UI screenshot")
    apple_menu_script = '''tell application "System Events"
        click menu bar item 1 of menu bar 1 of application process "Finder"
    end tell'''

    test_logger.debug(f"Executing AppleScript commands: {apple_menu_script}")
    applescript_result = session_context.user_context.apple_script.run_applescript(
        script=apple_menu_script
    )
    test_logger.info(f"AppleScript result: {applescript_result}")

    screenshot = session_context.user_context.screen_capture.capture_screenshot(
        capture_region=True,
        region_x=0,
        region_y=0,
        region_width=400,
        region_height=300,
    )
    assert screenshot is not None
    assert screenshot.get("success") is True
    assert screenshot.get("image_data") is not None

    # Save image data to local file
    local_path = save_to_artifacts(screenshot["image_data"], "applemenu_screenshot.png", subfolder="screenshots")

    # Close the menu using AppleScript (press Escape)
    test_logger.info("Closing Apple Menu using AppleScript...")
    close_menu_script = '''
    tell application "System Events"
        key code 53
    end tell
    '''
    close_menu_script_result = session_context.user_context.apple_script.run_applescript(script=close_menu_script)
    test_logger.debug(f"AppleScript execution result: {close_menu_script_result}")
    assert close_menu_script_result["success"] == True, "Failed to close Apple Menu"

    assert os.path.exists(local_path), f"File not saved at {local_path}"

    # # Extract text from the captured image data
    # extracted_text = extract_text_from_image(local_path)
    # test_logger.info(f"Extracted text from screenshot: {extracted_text}")
    # assert extracted_text, "OCR extraction failed"
    # assert expected_user.lower() in extracted_text.lower(), f"Expected user '{expected_user}' not found in OCR result"

    # Explicit cleanup at the end of the test
    test_logger.info("Cleaning up: logging out the latest logged-in user.")
    login_state.cleanup(expected_user)
    test_logger.info("Complete tap to login test passed successfully")