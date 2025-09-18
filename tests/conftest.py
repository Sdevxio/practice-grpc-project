import time

import pytest

from test_framework.utils.consts.constants import IMPRIVATA_LOG_NAME
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts
from test_framework.utils.handlers.file_analyzer import LogParser, LogExtractor


@pytest.fixture(scope="function")
def prepare_log_file(session_manager, test_config, test_logger):
    """Fixture to download, save, and prepare the log file from the macOS endpoint for analysis."""
    _, session_context = session_manager
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
    local_log_path = save_to_artifacts(file_content, IMPRIVATA_LOG_NAME)
    test_logger.info(f"Log file saved in: '{local_log_path}'")

    return local_log_path


@pytest.fixture(scope="function")
def parse_log_file():
    """Fixture that provides a callable to parse a log file and return a LogExtractor and parsed entries."""
    parser = LogParser()
    data_extractor = LogExtractor()

    def parse(log_file_path):
        """Parse the specified log file and return the extractor and entries."""
        entries = parser.parse_file(log_file_path)
        return data_extractor, entries

    return parse