import pytest


@pytest.mark.test_user("admin")
def test_monitor_single_user_authentication(auth_manager, session_manager, test_logger, test_config, parse_log_file,
                                            prepare_log_file):
    """Test to verify single user authentication log entries."""
    expected_user = test_config["expected_user"]
    expected_card = test_config["expected_card"]

    # Parse logs to find session activity
    data_extractor, entries = parse_log_file(prepare_log_file)
    test_logger.info(f"Validating {len(entries)} log entries for session activity")

    # Initialize session manager and context
    manager, session_context = session_manager
    test_logger.info(f"Session established for user: {session_context.username}")

    # Validation 1: User login entry
    card_id_entry = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains=f"Read card id: {expected_card}",
        component="DeviceManager",
        entry_type="info",
        process_name="root"
    )
    assert card_id_entry is not None, f"No 'Read card id: {expected_card}' entry found"

    # Validation 2: User session creation entry
    user_creation_message = f'CreateUser user: "{expected_user}" full name: "{expected_user}" first name: "" last name: ""'
    user_creation_entry = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains=user_creation_message,
        component="LoginPlugin",
        entry_type="info",
        process_name="root"
    )
    assert user_creation_entry is not None, f"No user creation entry found for user: {expected_user}"