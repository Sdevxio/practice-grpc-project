class TestSingleUserAuthentication:
    """Test class for single user authentication scenarios."""

    def _assert_log_entry_exists(self, data_extractor, recent_entries, test_logger,
                                 expected_message, component, entry_type, process_name):
        """Helper method to assert log entry exists with given criteria."""
        latest_entry = data_extractor.find_latest_entry_with_criteria(
            recent_entries,
            message_contains=expected_message,
            component=component,
            entry_type=entry_type,
            process_name=process_name
        )

        if latest_entry:
            test_logger.info(f"Latest entry found: {latest_entry.timestamp} - {latest_entry.message}")
        else:
            test_logger.error("No matching log entry found")

        assert latest_entry is not None, f"No matching log entry found for: {expected_message}"


    def test_monitor_single_user_authentication(self, recent_entries, session_config, test_logger):
        """Test to verify single user authentication log entries."""
        data_extractor, entries = recent_entries
        expected_user = session_config["expected_user"]
        expected_card = session_config["expected_card"]

        test_logger.info(f"Expected User: {expected_user}")
        test_logger.info(f"Expected Card: {expected_card}")
        test_logger.info(f"Validating {len(entries)} log entries")

        # Validation 1: User login entry
        self._assert_log_entry_exists(
            data_extractor,
            entries,
            test_logger,
            expected_message=f"Read card id: {expected_card}",
            component="DeviceManager",
            entry_type="info",
            process_name="root"
        )

        # Validation 2: User session creation entry
        user_creation_message = f'CreateUser user: "{expected_user}" full name: "{expected_user}" first name: "" last name: ""'
        self._assert_log_entry_exists(
            data_extractor,
            entries,
            test_logger,
            expected_message=user_creation_message,
            component="LoginPlugin",
            entry_type="info",
            process_name="root"
        )


    def test_desktop_agent_ui_process_performance(self,session_setup, recent_entries, session_config, test_logger):
        """Test to verify Desktop Agent UI process performance timing."""
        data_extractor, entries = recent_entries
        expected_user = session_config["expected_user"]

        test_logger.info(f"Expected User: {expected_user}")
        test_logger.info(f"Validating {len(entries)} log entries for UI performance")

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
            message_contains="Exiting switchToLoginWindow",
            component="DesktopAgent",
            entry_type="debug",
            process_name=expected_user
        )
        assert exit_switch_ui is not None, "No 'Exiting switch to login window' entry found"

        # Parse timestamps
        start_time = data_extractor._parse_timestamp(login_ui.timestamp)
        end_time = data_extractor._parse_timestamp(exit_switch_ui.timestamp)

        # Calculate and validate timing
        time_difference = end_time - start_time
        seconds_diff = time_difference.total_seconds()

        test_logger.info(f"UI switch timing: {seconds_diff:.3f} seconds")
        test_logger.info(f"Start: {login_ui.timestamp}, End: {exit_switch_ui.timestamp}")

        # Validate timing constraints
        assert seconds_diff >= 0, f"Invalid sequence: exit ({exit_switch_ui.timestamp}) before start ({login_ui.timestamp})"
        assert seconds_diff <= 1.5, f"UI switch too slow: {seconds_diff:.3f}s exceeds 1.5s limit"