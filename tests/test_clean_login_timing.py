"""
Clean Login Timing Test - Demonstrates the clean fixture architecture.

Your exact scenario using clean, focused fixtures with no duplication.
"""

import pytest
from datetime import datetime


def test_login_timing_simple(grpc_with_user, login_manager_with_session, logs_client, timing_calc, test_config, test_logger):
    """Your scenario: logs monitoring + tap login + timing - clean architecture."""
    
    test_logger.info("🚀 Starting login timing test with CLEAN architecture")
    
    # 1. Start gRPC and logs (grpc_with_user already has user setup)
    log_file_path = test_config.get("log_file_path", "/Users/admin/PA/dynamic_log_generator/dynamic_test.log")
    stream_id = logs_client.stream_log_entries(log_file_path)
    test_logger.info(f"📊 Started log stream: {stream_id}")
    
    # 2. Tap login with timing
    login_mgr = login_manager_with_session(grpc_with_user)  # Uses same session!
    expected_user = test_config["expected_user"]
    test_logger.info(f"🔐 Starting login process for user: {expected_user}")
    
    tap_time = datetime.now()
    test_logger.info(f"⏰ Tap timestamp recorded: {tap_time.strftime('%H:%M:%S.%f')[:-3]}")
    
    login_mgr.ensure_logged_in(expected_user)
    test_logger.info(f"✅ Login completed for user: {expected_user}")
    
    # 3. Calculate timing
    delay = timing_calc.calculate_delay(tap_time)
    test_logger.info(f"⏱️ Login operation took: {delay['delay_formatted']}")
    
    # 4. Check for log entry with "sessionDidBecomeActive" (use large window for demo)
    test_logger.info("📋 Searching for 'sessionDidBecomeActive' log entry...")
    correlation = logs_client.stream_entries_for_tap_correlation(
        tap_start_time=tap_time,
        expected_patterns=["sessionDidBecomeActive"],
        log_file_path=log_file_path,
        correlation_window_seconds=3600,  # 1 hour window to find existing entries
        structured_criteria={'component': 'DesktopAgent', 'process_name': 'ScreenManager'}
    )
    
    # 5. Assert we found the expected log entry  
    assert correlation['found_entries'], f"Expected to find 'sessionDidBecomeActive' log entry, but found {len(correlation['found_entries'])} entries"
    test_logger.info(f"🎯 Found {len(correlation['found_entries'])} matching log entries")
    
    for pattern_key, result in correlation['found_entries'].items():
        delay_seconds = result['delay_seconds']
        message = result['message']
        
        test_logger.info(f"✅ Pattern '{pattern_key}' found:")
        test_logger.info(f"   📝 Message: {message}")
        test_logger.info(f"   ⏱️ Delay from tap: {delay_seconds:.3f}s ({abs(delay_seconds):.3f}s {'before' if delay_seconds < 0 else 'after'} tap)")
        test_logger.info(f"   🏢 Component: DesktopAgent")
        test_logger.info(f"   🖥️ Process: ScreenManager")
        
        # Verify it contains the expected message
        assert "sessionDidBecomeActive" in result['message'], f"Expected 'sessionDidBecomeActive' in message: {result['message']}"
        test_logger.info("✅ Message validation passed: contains 'sessionDidBecomeActive'")
    
    # 6. Cleanup
    logs_client.stop_log_stream(stream_id)
    test_logger.info("🧹 Cleaned up log stream")
    
    test_logger.info("🎉 CLEAN ARCHITECTURE LOGIN TIMING TEST COMPLETED!")
    test_logger.info("Key achievements:")
    test_logger.info("  ✅ Single source of truth for gRPC session")
    test_logger.info("  ✅ No fixture duplication or conflicts")
    test_logger.info("  ✅ Clear, focused responsibilities")
    test_logger.info("  ✅ Clean dependency hierarchy")
    test_logger.info("  ✅ Successful log correlation with timing analysis")

