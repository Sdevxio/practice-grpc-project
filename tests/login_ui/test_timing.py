import pytest
from datetime import timedelta

from grpc_client_sdk.services.logs_monitor_stream_service_client import LogsMonitoringServiceClient
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils.handlers.file_analyzer.extractor import LogExtractor
from test_framework.utils.handlers.file_analyzer.log_monitor_streaming import LogMonitorStreaming, EventCriteria
from test_framework.utils.loaders.station_loader import StationLoader
import datetime

@pytest.fixture(scope="function")
def streamed_recent_entries(session_setup, session_config, test_logger):
    """
    Fixture to provide recent log entries using streaming instead of file download.
    Returns (data_extractor, recent_entries) for compatibility with existing tests.
    """
    # Setup log streaming client
    config = StationLoader()
    station_name = session_config["station_id"]
    log_file_path = session_config["log_file_path"]
    session_manager = GrpcSessionManager(station_id=station_name, logger=test_logger)
    client_name = "root"  # Use root context for log streaming
    logs_client = LogsMonitoringServiceClient(client_name=client_name, logger=test_logger)
    logs_client.connect()
    assert logs_client.connected, "Failed to connect to LogsMonitoringServiceClient"

    # Determine time window as in the original fixture
    login_timing = session_setup.session_timing
    tap_start_time = login_timing.get("tap_start_time")
    session_created_time = login_timing.get("session_created_time")
    if tap_start_time is not None:
        start_time = tap_start_time - timedelta(minutes=3)
        end_time = session_created_time + timedelta(minutes=2)
    else:
        start_time = session_created_time - timedelta(minutes=5)
        end_time = session_created_time

    # Use streaming to collect log entries in the window
    criteria = EventCriteria(
        start_time=start_time,
        target_patterns=[""],  # Match all lines
        timeout_seconds=10,  # Reduced wait time for streaming
        min_entries_required=1
    )
    monitor = LogMonitorStreaming(logs_monitor_service=logs_client, log_file_path=log_file_path, test_logger=test_logger)
    streamed_entries = monitor.wait_for_events(criteria)
    if streamed_entries is None:
        test_logger.error(f"No log entries streamed in window {start_time} to {end_time}")
        streamed_entries = []
    else:
        # Further filter to the exact window (since streaming may include more)
        extractor = LogExtractor()
        streamed_entries = extractor.find_entries_in_time_range(streamed_entries, start_time, end_time)
        test_logger.info(f"Streamed and filtered {len(streamed_entries)} entries in window {start_time} to {end_time}")

    data_extractor = LogExtractor()
    return data_extractor, streamed_entries

def test_streamed_authentication_with_pre_tap_streaming(
    tapping_manager, grpc_session_manager, session_config, test_logger
):
    """
    Test streaming authentication log entries by starting streaming BEFORE tap/login event,
    using stream_entries_for_tap_correlation for robust timing correlation.
    """
    station_name = session_config["station_id"]
    log_file_path = session_config["log_file_path"]
    expected_user = session_config["expected_user"]
    expected_card = session_config["expected_card"]
    login_timeout = session_config["login_timeout"]

    logs_client = LogsMonitoringServiceClient(client_name="root", logger=test_logger)
    logs_client.connect()
    assert logs_client.connected, "Failed to connect to LogsMonitoringServiceClient"

    # 1. Capture tap start time
    tap_start_time = datetime.datetime.now()
    test_logger.info(f"[Tap correlation] Tap start time: {tap_start_time}")

    # 2. Define expected patterns
    expected_patterns = [
        f"sessionDidBecomeActive",
    ]

    # 3. Start tap/login event
    login_success = tapping_manager.perform_login_tap(
        verification_callback=None,
        max_attempts=3
    )
    assert login_success, "Tap/login event failed"

    # 4. Create session (wait for user to be logged in)
    session_context = grpc_session_manager.create_session(
        expected_user=expected_user,
        timeout=login_timeout
    )
    session_created_time = datetime.datetime.now()
    test_logger.info(f"[Tap correlation] Session created at: {session_created_time}")

    # 5. Use tap correlation streaming to find log entries
    correlation_results = logs_client.stream_entries_for_tap_correlation(
        tap_start_time=tap_start_time,
        expected_patterns=expected_patterns,
        log_file_path=log_file_path,
        correlation_window_seconds=10  # Reduced wait time
    )

    found_entries = correlation_results.get('found_entries', {})
    test_logger.info(f"[Tap correlation] Found entries: {list(found_entries.keys())}")

    # 6. Validate each expected pattern was found
    for i, pattern in enumerate(expected_patterns):
        entry_info = found_entries.get(f"pattern_{i}")
        if entry_info is None:
            test_logger.error(f"[Tap correlation] No matching log entry found for: {pattern}")
        else:
            entry = entry_info['entry']
            test_logger.info(f"[Tap correlation] Pattern '{pattern}' matched at {entry.timestamp}: {entry.message}")
        assert entry_info is not None, f"[Tap correlation] No matching log entry found for: {pattern}"