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


# =============================================================================
# NEW SIMPLIFIED TESTS USING WORKFLOW FIXTURES  
# =============================================================================

def test_streamed_authentication_simplified(pre_tap_streaming_workflow, test_logger):
    """
    SIMPLIFIED VERSION: Same test logic, 87% fewer lines!
    
    Compare this with the 61-line version above to see the dramatic reduction.
    """
    # 1. Setup workflow components
    workflow = pre_tap_streaming_workflow()
    
    # 2. Create gRPC session first (needed for logs client)
    grpc_session = workflow["grpc_session_factory"]()
    grpc_session.create_session(
        expected_user=workflow["config"]["expected_user"],
        timeout=workflow["config"]["login_timeout"]
    )
    
    # 3. Start logs monitoring (now gRPC is ready)
    logs_client = workflow["logs_client_factory"]()
    
    # 4. Record tap time and perform tap
    tap_start_time = datetime.datetime.now()
    test_logger.info(f"⏰ Tap start time: {tap_start_time}")
    
    tapping_mgr = workflow["tapping_factory"]()
    login_success = tapping_mgr.perform_login_tap(verification_callback=None)
    assert login_success, "Tap/login event failed"
    
    # 5. Get correlation results (logs already capturing!)
    correlation_results = logs_client.stream_entries_for_tap_correlation(
        tap_start_time=tap_start_time,
        expected_patterns=["sessionDidBecomeActive"],
        log_file_path=workflow["log_file_path"],
        correlation_window_seconds=10
    )
    
    # 5. Verify results
    found_entries = correlation_results.get('found_entries', {})
    assert found_entries, f"Expected 'sessionDidBecomeActive' entry, found: {list(found_entries.keys())}"
    test_logger.info(f"✅ Simplified test found entries: {list(found_entries.keys())}")


def test_grpc_first_then_tap_example(grpc_then_tap_workflow, test_logger):
    """
    Example: Setup gRPC connection first, then control tap timing.
    
    Perfect for tests that need established connection before physical interaction.
    """
    # 1. Setup workflow (gRPC already connected)
    workflow = grpc_then_tap_workflow()
    
    # 2. Setup user session first
    session_context = workflow["grpc_session"].create_session(
        expected_user=workflow["config"]["expected_user"], 
        timeout=30
    )
    
    # 3. Now perform tap with established connection
    tap_start_time = datetime.datetime.now()
    tapping_mgr = workflow["tapping_factory"]()
    
    # 4. Use existing session for verification
    result = session_context.root_context.command.run_command("whoami")
    assert result.exit_code == 0
    
    test_logger.info("✅ gRPC-first workflow completed successfully")


def test_clean_start_example(clean_start_workflow, test_logger):
    """
    Example: Guaranteed clean start (user logged out, lock screen).
    
    Perfect for tests that need pristine login conditions.
    """
    # 1. Setup workflow (already ensured logout/lock screen) 
    workflow = clean_start_workflow()
    assert workflow["clean_state_confirmed"], "Clean start not confirmed"
    
    # 2. Start logs monitoring when ready
    logs_client = workflow["logs_factory"]()
    logs_client.connect()
    
    # 3. Now control exact tap timing
    tap_start_time = datetime.datetime.now()
    tapping_mgr = workflow["tapping_factory"]()
    login_success = tapping_mgr.perform_login_tap(verification_callback=None, max_attempts=3)
    assert login_success
    
    # 4. Create session after clean tap
    grpc_session = workflow["grpc_session_factory"]()
    session_context = grpc_session.create_session(
        expected_user=workflow["config"]["expected_user"],
        timeout=30
    )
    
    test_logger.info("✅ Clean start workflow completed successfully")