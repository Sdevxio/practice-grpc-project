from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.log_streaming_service_client import LogsMonitoringServiceClient
from test_framework.utils.consts.constants import REMOTE_LOG_PATH


def test_logs_monitoring_service_connection(setup):
    """
    Test basic connection to LogsMonitoringServiceClient.
    """
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    logs_client = LogsMonitoringServiceClient(client_name="root")
    logs_client.connect()

    assert logs_client.client_name == "root"


def test_get_active_streams(setup):
    """
    Test getting active streams information.
    """
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    logs_client = LogsMonitoringServiceClient(client_name="root")
    logs_client.connect()

    active_streams = logs_client.get_active_streams()
    assert isinstance(active_streams, dict)


def test_monitor_logs_entry(setup):
    """
    Test monitoring logs entry.
    """
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    logs_stream_client = LogsMonitoringServiceClient(client_name="root")
    logs_stream_client.connect()

    log_path = REMOTE_LOG_PATH
    stream_id = logs_stream_client.stream_log_entries(
        log_file_path=log_path,
        filter_patterns=['sessionDidBecomeActive'],
        include_existing=True,
        entry_callback=None,
        structured_criteria=None
    )
    assert isinstance(stream_id, str)
    print(f"Stream ID: {stream_id}")
    
    # Give the stream time to collect entries
    import time
    time.sleep(3)
    
    # Get and print the retrieved entries
    active_streams = logs_stream_client.get_active_streams()
    if stream_id in active_streams:
        entry_count = active_streams[stream_id]['entry_count']
        print(f"Retrieved {entry_count} log entries")
        
        # Access the actual entries from the stream
        with logs_stream_client.stream_lock:
            if stream_id in logs_stream_client.active_streams:
                entries = logs_stream_client.active_streams[stream_id]['entries']
                print(f"Total entries: {len(entries)}")
                # Print last 5 entries (most recent)
                for i, entry in enumerate(entries[-5:]):
                    print(f"Entry {len(entries)-4+i}: {entry.timestamp} - {entry.message}")
    
    # Stop the stream and cleanup all streams to prevent threading issues
    logs_stream_client.stop_log_stream(stream_id)
    logs_stream_client.stop_all_streams()

