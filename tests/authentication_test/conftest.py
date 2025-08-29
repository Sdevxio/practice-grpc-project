import time
from datetime import timedelta

import pytest

from test_framework.utils.consts.constants import REMOTE_LOG_PATH
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts
from test_framework.utils.handlers.file_analyzer.extractor import LogExtractor
from test_framework.utils.handlers.file_analyzer.parser import LogParser


@pytest.fixture(scope="function")
def log_service(session_setup, session_config, test_logger):
    """Fixture to set up log file download and processing."""
    LOG_FILE_PATH = session_config['log_file_path']
    test_logger.info("Downloading log file from macOS endpoint")

    # Wait for the log file to be available
    time.sleep(60)
    file_content = session_setup.root_context.file_transfer.download_file(
        LOG_FILE_PATH,
        tail_bytes="2097152"
    )

    if not file_content:
        raise RuntimeError(f"Failed to download log file from '{LOG_FILE_PATH}'")

    test_logger.info(f"Downloaded {len(file_content)} bytes from log file")

    # Save content to local file for analysis
    log_filename = REMOTE_LOG_PATH.format(session_config["station_id"])
    local_log_path = save_to_artifacts(file_content, log_filename)
    test_logger.info(f"Log file saved in: '{local_log_path}'")

    return local_log_path


@pytest.fixture(scope="function")
def log_analyzer(log_service, test_logger):
    """Fixture to provide log analysis tools with parsed entries."""
    parser = LogParser()
    data_extractor = LogExtractor()

    entries = parser.parse_file(log_service)
    test_logger.info(f"Parsed {len(entries)} log entries from the file")

    return data_extractor, entries


@pytest.fixture(scope="function")
def recent_entries(log_analyzer, session_setup, test_logger):
    """Fixture to provide recent log entries within test execution window."""
    data_extractor, entries = log_analyzer

    # Current timing from session_setup
    login_timing = session_setup.session_timing
    tap_start_time = login_timing["tap_start_time"]
    session_created_time = login_timing["session_created_time"]

    if tap_start_time is not None:
        # With tapping precise window
        start_time = tap_start_time - timedelta(minutes=3)
        end_time = session_created_time + timedelta(minutes=2)
    else:
        # Without tapping, around session creation
        start_time = session_created_time - timedelta(minutes=5)
        end_time = session_setup.session_created_time

    # get entries in time window
    recent_log_entries = data_extractor.get_entries_in_time_range(entries, start_time, end_time)
    test_logger.info(f"Found {len(recent_log_entries)} entries in {start_time} to {end_time} window")

    return data_extractor, recent_log_entries