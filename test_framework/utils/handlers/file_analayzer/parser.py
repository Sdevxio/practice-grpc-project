import re
from typing import List, Optional

from test_framework.utils import get_logger
from test_framework.utils.handlers.file_analayzer.entry import LogEntry


class LogParser:
    """Parser for macOS log files."""

    def __init__(self):
        """Initialize the file_analyzer."""
        self.logger = get_logger("framework.handler.log_parser")

        # Regular expression for parsing log lines
        self.pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})\s+'  # timestamp
            r'(\w+\s*\w*)\s+'  # component
            r'(\w+\s*\w*)\s+'  # subcomponent
            r'(\d+)\s+'  # pid
            r'(0x[0-9a-f]+)\s+'  # thread_id
            r'(\d+)\s+'  # level
            r'(\d+)\s+'  # process_id
            r'(\w+)\s+'  # process_name
            r'(\w+):\s+'  # type
            r'(.*)'  # message
        )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single line of log text.

        :param line: The log line to parse
        :param line_number: Line number in the file (for reference)
        :return: LogEntry object if parsing succeeds, None otherwise
        """
        try:
            match = self.pattern.match(line.strip())
            if not match:
                return None

            # Extract all groups
            timestamp, component, subcomponent, pid, thread_id, level, \
                process_id, process_name, type_value, message = match.groups()

            return LogEntry(
                timestamp=timestamp,
                component=component,
                subcomponent=subcomponent,
                pid=pid,
                thread_id=thread_id,
                level=level,
                process_id=process_id,
                process_name=process_name,
                type=type_value,
                message=message,
                raw_line=line.strip(),
                line_number=line_number
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse line {line_number}: {str(e)}")
            return None

    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        Parse a log file.

        :param file_path: Path to the log file
        :return: List of LogEntry objects
        """
        self.logger.info(f"Parsing log file: {file_path}")
        entries = []

        try:
            with open(file_path, 'r') as f:
                for i, line in enumerate(f, 1):
                    if line.strip():
                        entry = self.parse_line(line, i)
                        if entry:
                            entries.append(entry)

            self.logger.info(f"Successfully parsed {len(entries)} log entries")
            return entries
        except Exception as e:
            self.logger.error(f"Error parsing file: {str(e)}")
            return []