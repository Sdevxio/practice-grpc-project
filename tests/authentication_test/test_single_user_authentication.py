import pytest


@pytest.mark.auto_manage(False)
def test_monitor_single_user_authentication(login_state, recent_entries, log_service):
    """Test to verify single user authentication log entries."""
    # Perform login first to generate authentication events
    login_state.ensure_logged_in()
    
    # Wait a moment for log entries to be written
    import time
    time.sleep(2)
    
    # Then parse logs to find the authentication events we just generated
    data_extractor, entries = recent_entries(log_service)
    expected_user = "admin"  # Match actual log data
    expected_card = "DF40F85534"   # Match actual log data

    login_state.logger.info(f"Expected User: {expected_user}")
    login_state.logger.info(f"Expected Card: {expected_card}")
    login_state.logger.info(f"Validating {len(entries)} log entries")

    # Validation 1: User login entry
    latest_entry = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains=f"Read card id: {expected_card}",
        component="DeviceManager",
        entry_type="info",
        process_name="root"
    )
    assert latest_entry is not None, f"No matching log entry found for: Read card id: {expected_card}"

    # Validation 2: User session creation entry
    user_creation_message = f'CreateUser user: "{expected_user}" full name: "{expected_user}" first name: "" last name: ""'
    latest_entry = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains=user_creation_message,
        component="LoginPlugin",
        entry_type="info",
        process_name="root"
    )
    assert latest_entry is not None, f"No matching log entry found for: {user_creation_message}"


@pytest.mark.auto_manage(False)
def test_desktop_agent_ui_process_performance(login_state, recent_entries, log_service):
    """Test to verify Desktop Agent UI process performance timing."""
    # Perform login first to generate authentication events
    login_state.ensure_logged_in()
    
    # Wait a moment for log entries to be written
    import time
    time.sleep(2)
    
    # Then parse logs to find the authentication events we just generated
    data_extractor, entries = recent_entries(log_service)
    expected_user = "admin"  # Match actual log data

    login_state.logger.info(f"Expected User: {expected_user}")
    login_state.logger.info(f"Validating {len(entries)} log entries for UI performance")

    # Find both required log entries
    login_ui = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains="Switching to Login UI",
        component="DesktopAgent",
        entry_type="info",
        process_name=expected_user
    )
    assert login_ui is not None, "No 'Switching to Login UI' entry found"

    exit_switch_ui = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains="Desktop Agent UI initialization complete",
        component="DesktopAgent",
        entry_type="info",
        process_name=expected_user
    )
    assert exit_switch_ui is not None, "No 'Desktop Agent UI initialization complete' entry found"

    # Parse timestamps
    start_time = data_extractor._parse_timestamp(login_ui.timestamp)
    end_time = data_extractor._parse_timestamp(exit_switch_ui.timestamp)

    # Calculate and validate timing
    time_difference = end_time - start_time
    seconds_diff = time_difference.total_seconds()

    login_state.logger.info(f"UI switch timing: {seconds_diff:.3f} seconds")
    login_state.logger.info(f"Start: {login_ui.timestamp}, End: {exit_switch_ui.timestamp}")

    # Validate timing constraints
    assert seconds_diff >= 0, f"Invalid sequence: exit ({exit_switch_ui.timestamp}) before start ({login_ui.timestamp})"
    assert seconds_diff <= 3, f"UI switch too slow: {seconds_diff:.3f}s exceeds 1.5s limit"


def test_desktop_agent_session_activity(login_state, recent_entries, test_config, test_logger, log_service):
    from test_framework.utils.handlers.dashboard_handler import PerformanceDashboardManager
    
    expected_user = test_config["expected_user"]
    # Initialize with SQLite database for persistent performance tracking
    dashboard_manager = PerformanceDashboardManager(
        logger=test_logger,
        use_sqlite=True,
        db_path=r"C:\performance-data\performance.db"
    )
    
    # Force tap regardless of current login state
    login_state.manager.force_tap()
    tap_timestamp = login_state.manager.last_tap_timestamp
    test_logger.info(f"Force tap timestamp: {tap_timestamp}")

    # Parse logs to find session activity
    data_extractor, entries = recent_entries(log_service)
    test_logger.info(f"Validating {len(entries)} log entries for session activity")

    session_activity = data_extractor.find_latest_entry_with_criteria(
        entries,
        message_contains="sessionDidBecomeActive",
        component="DesktopAgent",
        entry_type="info",
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
            test_logger.info(f"Database: {db_info.get('backend', 'Unknown')} - {db_info.get('total_records', 0)} records")
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