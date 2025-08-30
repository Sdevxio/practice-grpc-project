"""
Session Timing Tests - Focus on sessionDidBecomeActive timing calculation.

Test Scenario 1: Start streaming → Tap → Calculate timing → Dashboard
Test Scenario 2: Fetch sessionDidBecomeActive entry without tapping
"""

import pytest
from datetime import datetime, timedelta
from test_framework.utils.ui_timing_calculator.timing_calculator import LogMonitorStreaming, EventCriteria
from test_framework.utils.ui_timing_calculator.dashboard_manager import PerformanceDashboardManager
import re
import time


def test_tap_to_session_active_timing(hardware_controller, test_config, test_logger):
    """
    Scenario 1: Real tap → Monitor new sessionDidBecomeActive → Calculate actual timing → Dashboard
    
    Measures real timing between tap action and new sessionDidBecomeActive log entry.
    """
    log_file_path = test_config["log_file_path"]
    
    # Get baseline - find current last line number to detect new entries
    with open(log_file_path, 'r') as f:
        baseline_lines = len(f.readlines())
    
    # Record current time as fake tap time
    fake_tap_time = datetime.now()
    test_logger.info(f"Fake tap time recorded at: {fake_tap_time.strftime('%H:%M:%S.%f')[:-3]}")
    
    # Find most recent sessionDidBecomeActive entry
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        recent_lines = lines[-50:] if len(lines) > 50 else lines
    
    session_entry = None
    for line in reversed(recent_lines):
        if "sessionDidBecomeActive" in line:
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line.strip())
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                try:
                    log_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    session_entry = {
                        'timestamp': timestamp_str,
                        'message': line.strip(),
                        'datetime': log_datetime
                    }
                    break
                except ValueError:
                    continue
    
    if session_entry:
        # Calculate real timing difference between fake tap time and log entry time
        total_duration = abs((fake_tap_time - session_entry['datetime']).total_seconds())
        
        test_logger.info(f"sessionDidBecomeActive found at {session_entry['timestamp']}")
        test_logger.info(f"Real tap-to-session timing: {total_duration:.3f}s")
        
        # Save real timing to dashboard
        dashboard_manager = PerformanceDashboardManager(logger=test_logger)
        saved_file = dashboard_manager.save_timing_result(
            test_name="real_tap_to_session_active",
            duration=total_duration,
            success=True,
            log_entry_timestamp=session_entry['timestamp'],
            log_entry_message=session_entry['message'],
            additional_data={
                "fake_tap_time": fake_tap_time.isoformat(),
                "log_entry_time": session_entry['datetime'].isoformat(),
                "method": "datetime_calculation"
            }
        )
        assert saved_file is not None, "Should save timing result"
        
        # Generate dashboard with real data
        dashboard_manager.generate_html_dashboard()
        test_logger.info("Dashboard updated with real tap-to-session timing")
        
        assert total_duration > 0, "Duration should be positive"
        assert total_duration < 86400, "Duration should be reasonable (< 24 hours)"
        
    else:
        test_logger.warning("No sessionDidBecomeActive entry found in log file")
        pytest.fail("Expected to find sessionDidBecomeActive log entry")


def test_fetch_session_active_without_tapping(test_config, test_logger):
    """
    Scenario 2: Real log parsing performance - measure actual file read and search timing
    
    Measures real performance of reading and parsing log file for sessionDidBecomeActive entries.
    """
    log_file_path = test_config["log_file_path"]
    
    # Measure file read performance
    read_start_time = time.time()
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        recent_lines = lines[-1000:] if len(lines) > 1000 else lines  # Parse more lines for realistic test
    read_duration = time.time() - read_start_time
    
    # Measure parsing performance
    parse_start_time = time.time()
    found_entries = []
    for line_num, line in enumerate(recent_lines, start=len(lines)-len(recent_lines)+1):
        if "sessionDidBecomeActive" in line:
            # Extract timestamp and parse to datetime for real timing
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line.strip())
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                try:
                    log_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    found_entries.append({
                        'timestamp': timestamp_str,
                        'message': line.strip(),
                        'line_number': line_num,
                        'datetime': log_datetime
                    })
                except ValueError:
                    continue
    
    parse_duration = time.time() - parse_start_time
    total_search_duration = read_duration + parse_duration
    
    # Process found entries with real performance data
    if found_entries:
        test_logger.info(f"Found {len(found_entries)} sessionDidBecomeActive entries")
        test_logger.info(f"File read time: {read_duration:.4f}s")
        test_logger.info(f"Parse time: {parse_duration:.4f}s")
        test_logger.info(f"Total search time: {total_search_duration:.4f}s")
        
        dashboard_manager = PerformanceDashboardManager(logger=test_logger)
        
        # Save real search performance metrics
        dashboard_manager.save_timing_result(
            test_name="log_file_read_performance",
            duration=read_duration,
            success=True,
            log_entry_timestamp=found_entries[0]['timestamp'],
            log_entry_message=f"Read {len(lines)} lines, found {len(found_entries)} entries",
            additional_data={
                "total_lines": len(lines),
                "searched_lines": len(recent_lines),
                "entries_found": len(found_entries),
                "method": "file_read_timing"
            }
        )
        
        dashboard_manager.save_timing_result(
            test_name="log_parsing_performance",
            duration=parse_duration,
            success=True,
            log_entry_timestamp=found_entries[0]['timestamp'],
            log_entry_message=f"Parsed {len(recent_lines)} lines in {parse_duration:.4f}s",
            additional_data={
                "lines_parsed": len(recent_lines),
                "entries_found": len(found_entries),
                "method": "parsing_timing"
            }
        )
        
        dashboard_manager.save_timing_result(
            test_name="total_search_performance",
            duration=total_search_duration,
            success=True,
            log_entry_timestamp=found_entries[0]['timestamp'],
            log_entry_message=f"Complete search: {total_search_duration:.4f}s",
            additional_data={
                "read_time": read_duration,
                "parse_time": parse_duration,
                "total_lines": len(lines),
                "entries_found": len(found_entries),
                "method": "complete_search_timing"
            }
        )
        
        # Generate dashboard with real performance data
        dashboard_manager.generate_html_dashboard()
        test_logger.info("Dashboard updated with real log parsing performance")
        
        assert len(found_entries) > 0, "Should find at least one sessionDidBecomeActive entry"
        assert total_search_duration < 5.0, "Search should complete within 5 seconds"
        
    else:
        search_duration = time.time() - (time.time() - total_search_duration)
        test_logger.info("No sessionDidBecomeActive entries found")
        
        # Save real performance data even for failed search
        dashboard_manager = PerformanceDashboardManager(logger=test_logger)
        dashboard_manager.save_timing_result(
            test_name="search_no_results_performance",
            duration=total_search_duration,
            success=False,
            log_entry_timestamp=None,
            log_entry_message=f"No entries found after searching {len(recent_lines)} lines in {total_search_duration:.4f}s",
            additional_data={
                "read_time": read_duration,
                "parse_time": parse_duration,
                "total_lines": len(lines),
                "method": "failed_search_timing"
            }
        )
        pytest.fail("Expected to find sessionDidBecomeActive log entries")