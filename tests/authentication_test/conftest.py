import time
from datetime import timedelta

import pytest
from test_framework.utils.consts.constants import REMOTE_LOG_PATH
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts
from test_framework.utils.handlers.file_analayzer.extractor import LogExtractor
from test_framework.utils.handlers.file_analayzer.parser import LogParser



@pytest.fixture(scope="function")
def log_service(session_manager, test_config, test_logger):
    """Fixture to set up log file download and processing."""
    manager, session_context = session_manager
    log_file_path = test_config['log_file_path']
    test_logger.info("Downloading log file from macOS endpoint")

    # Wait for the log file to be available
    time.sleep(10)
    file_content = session_context.root_context.file_transfer.download_file(
        log_file_path,
        tail_bytes="2097152"
    )

    if not file_content:
        raise RuntimeError(f"Failed to download log file from '{log_file_path}'")

    test_logger.info(f"Downloaded {len(file_content)} bytes from log file")

    # Save content to local file for analysis
    log_filename = f"station_{test_config['station_id']}_test.log"
    local_log_path = save_to_artifacts(file_content, log_filename)
    test_logger.info(f"Log file saved in: '{local_log_path}'")

    return local_log_path


@pytest.fixture(scope="function")
def recent_entries():
    """Fixture that provides log analysis tools - parsing happens in test after login."""
    parser = LogParser()
    data_extractor = LogExtractor()
    
    def parse_logs(log_file_path):
        """Parse logs after login action."""
        entries = parser.parse_file(log_file_path)
        return data_extractor, entries
    
    return parse_logs