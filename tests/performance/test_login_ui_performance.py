import pytest

from test_framework.utils.handlers.dashboard_handler.dashboard_manager import PerformanceDashboardManager


@pytest.mark.test_user("admin")
def test_login_ui_performance(auth_manager, session_manager, parse_log_file, test_config, test_logger, prepare_log_file):
    """
    Test to measure the performance of the login UI process.
    """
    expected_user = test_config["expected_user"]

    # Log configuration info for debugging
    test_logger.info(f"Expected user: {expected_user}")
    test_logger.info(f"Session timeout: {test_config.get('session_timeout')} seconds")
    user_tap_mapping = test_config.get("user_tap_mapping", {})
    if expected_user in user_tap_mapping:
        test_logger.info(f"User tap endpoint: {user_tap_mapping[expected_user]}")

    # Initialize with SQLite database for persistent performance tracking
    dashboard_manager = PerformanceDashboardManager(
        logger=test_logger,
        use_sqlite=True,
        db_path=r"C:\performance-data\performance.db"
    )

    # Get tap timestamp from the auth manager fixtures
    tap_timestamp = auth_manager.get_last_tap_timestamp()
    test_logger.info(f"Login tap timestamp: {tap_timestamp}")
    assert tap_timestamp is not None, "Tap timestamp should be available from auth_manager fixtures"

    # Initialize session manager and context
    manager, session_context = session_manager
    test_logger.info(f"Session established for user: {session_context.username}")

    # Verify the session was created for the expected user
    assert session_context.username == expected_user, f"Session created for wrong user. Expected: {expected_user}, Got: {session_context.username}"

    # Parse logs to find session activity
    data_extractor, entries = parse_log_file(prepare_log_file)
    test_logger.info(f"Validating {len(entries)} log entries for session activity")


    # Filter entries to only those AFTER the tap timestamp to avoid old sessions
    # Add small buffer (3 seconds before) to account for log writing delays and timing precision
    from datetime import timedelta
    buffer_time = tap_timestamp - timedelta(seconds=3)
    filtered_entries = [
        entry for entry in entries
        if entry.timestamp and data_extractor._parse_timestamp(entry.timestamp) >= buffer_time
    ]
    test_logger.info(f"Filtered to {len(filtered_entries)} entries after {buffer_time} (3s before tap)")
    
    # Find recent entries for this user to ensure we get the current session
    recent_user_entries = [
        entry for entry in filtered_entries
        if hasattr(entry, 'process_name') and entry.process_name == expected_user
    ]
    test_logger.info(f"Found {len(recent_user_entries)} recent entries for user {expected_user}")
    
    session_activity = data_extractor.find_latest_entry_with_criteria(
        filtered_entries,
        message_contains="sessionDidBecomeActive",
        component="DesktopAgent",
        entry_type="debug",
        process_name=expected_user
    )

    assert session_activity is not None, "No 'sessionDidBecomeActive' entry found"

    # Measure timing and generate dashboard in one call
    if tap_timestamp:
        timing_result = dashboard_manager.measure_and_track_timing(
            test_name="session_activity_timing",
            start_time=tap_timestamp,
            end_time=session_activity,
            data_extractor=data_extractor,
            expected_user=expected_user
        )
        test_logger.info(f"Performance timing recorded: {timing_result}")

        # Log database health information
        try:
            db_info = dashboard_manager.get_database_info()
            test_logger.info(
                f"Database: {db_info.get('backend', 'Unknown')} - {db_info.get('total_records', 0)} records")
            if 'file_size_mb' in db_info:
                test_logger.info(f"Database size: {db_info['file_size_mb']:.2f} MB")
        except Exception as e:
            test_logger.warning(f"Could not retrieve database info: {e}")

        # Generate final dashboard
        dashboard_file = dashboard_manager.generate_html_dashboard()
        if dashboard_file:
            test_logger.info(f"Performance dashboard ready: {dashboard_file}")
        else:
            test_logger.error("Failed to generate performance dashboard")