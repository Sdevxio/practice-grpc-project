#!/usr/bin/env python3
"""
Dynamic Log Simulator - Mimics Real-Time Log Generation

This script simulates realistic log file behavior by continuously writing
log entries based on realistic event patterns and timing.
"""

import time
import random
import threading
import queue
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Types of events that can occur in the system"""
    CARD_DETECTION = "card_detection"
    USER_AUTH = "user_auth"
    SESSION_CREATE = "session_create"
    UI_SWITCH = "ui_switch"
    SYSTEM_MONITOR = "system_monitor"
    ERROR_EVENT = "error_event"
    NETWORK_EVENT = "network_event"
    PERFORMANCE_CHECK = "performance_check"


@dataclass
class LogTemplate:
    """Template for generating log entries"""
    component: str
    subcomponent: str
    process_name: str
    level: int
    message_template: str
    event_type: EventType
    delay_range: tuple = (0.1, 2.0)  # Min/max delay in seconds


class DynamicLogSimulator:
    """
    Simulates dynamic log file generation with realistic patterns
    """

    def __init__(self, log_file_path: str = "dynamic_test.log",
                 max_file_size: int = 10 * 1024 * 1024):  # 10MB default
        self.log_file_path = Path(log_file_path)
        self.max_file_size = max_file_size
        self.event_queue = queue.Queue()
        self.running = False
        self.writer_thread = None
        self.event_generator_thread = None

        # Process ID counters
        self.pid_counter = 1000
        self.process_id_counter = 6000

        # User simulation state
        self.current_users = []
        self.available_cards = ["AF17C52201", "BF28D63312", "CF39E74423", "DF40F85534"]

        # Log templates for different event types
        self.log_templates = self._init_log_templates()

        # Event probability weights (higher = more frequent)
        self.event_weights = {
            EventType.SYSTEM_MONITOR: 0.2,
            EventType.CARD_DETECTION: 0.15,
            EventType.USER_AUTH: 0.15,
            EventType.SESSION_CREATE: 0.1,
            EventType.UI_SWITCH: 0.25,  # Much higher chance for UI events
            EventType.NETWORK_EVENT: 0.05,
            EventType.PERFORMANCE_CHECK: 0.05,
            EventType.ERROR_EVENT: 0.05,
        }

    def _init_log_templates(self) -> Dict[EventType, List[LogTemplate]]:
        """Initialize log templates for different event types"""
        return {
            EventType.CARD_DETECTION: [
                LogTemplate("DeviceManager", "CardReader", "root", 2,
                            "Card detected on reader", EventType.CARD_DETECTION, (0.1, 0.5)),
                LogTemplate("DeviceManager", "CardReader", "root", 2,
                            "Read card id: {card_id}", EventType.CARD_DETECTION, (0.2, 0.8)),
            ],

            EventType.USER_AUTH: [
                LogTemplate("AuthService", "LoginHandler", "root", 2,
                            "Processing card authentication for {card_id}", EventType.USER_AUTH, (0.5, 1.5)),
                LogTemplate("LoginPlugin", "UserManager", "root", 2,
                            "CreateUser user: \"{username}\" full name: \"{username}\" first name: \"\" last name: \"\"",
                            EventType.USER_AUTH, (0.3, 1.0)),
                LogTemplate("AuthService", "LoginHandler", "root", 2,
                            "User {username} authenticated successfully", EventType.USER_AUTH, (0.2, 0.7)),
            ],

            EventType.SESSION_CREATE: [
                LogTemplate("SessionManager", "UserSession", "{username}", 2,
                            "Session created for user {username}", EventType.SESSION_CREATE, (0.5, 1.5)),
                LogTemplate("Desktop", "PolicyEngine", "{username}", 2,
                            "WalkAway customization config has been synchronized", EventType.SESSION_CREATE,
                            (1.0, 3.0)),
            ],

            EventType.UI_SWITCH: [
                LogTemplate("DesktopAgent", "UIManager", "{username}", 2,
                            "Switching to Login UI", EventType.UI_SWITCH, (1.0, 3.0)),
                LogTemplate("LoginPlugin", "ScreenManager", "_securityagent", 2,
                            "Opened proxcard screen", EventType.UI_SWITCH, (1.0, 3.0)),
                LogTemplate("DesktopAgent", "ScreenManager", "{username}", 2,
                            "sessionDidBecomeActive", EventType.UI_SWITCH, (0.5, 2.0)),
                LogTemplate("DesktopAgent", "UIManager", "{username}", 2,
                            "Desktop Agent UI initialization complete", EventType.UI_SWITCH, (1.0, 3.0)),
            ],

            EventType.SYSTEM_MONITOR: [
                LogTemplate("ResourceMonitor", "CPUMonitor", "monitor", 2,
                            "CPU usage: {cpu_usage}% (normal)", EventType.SYSTEM_MONITOR, (5.0, 15.0)),
                LogTemplate("ResourceMonitor", "MemoryMonitor", "monitor", 2,
                            "Memory usage: {memory_usage}GB / 8.0GB ({memory_percent}%)",
                            EventType.SYSTEM_MONITOR, (5.0, 15.0)),
                LogTemplate("PerformanceMonitor", "SystemMetrics", "root", 2,
                            "System load average: {load1}, {load2}, {load3}", EventType.SYSTEM_MONITOR, (10.0, 30.0)),
            ],

            EventType.ERROR_EVENT: [
                LogTemplate("DeviceManager", "CardReader", "root", 4,
                            "Card reader communication timeout", EventType.ERROR_EVENT, (30.0, 120.0)),
                LogTemplate("AuthService", "LoginHandler", "root", 4,
                            "Authentication failed for card {card_id}", EventType.ERROR_EVENT, (10.0, 60.0)),
                LogTemplate("NetworkManager", "ConnectionHandler", "network", 3,
                            "Connection timeout - retrying", EventType.ERROR_EVENT, (15.0, 90.0)),
            ],

            EventType.NETWORK_EVENT: [
                LogTemplate("NetworkManager", "ConnectionHandler", "network", 2,
                            "Establishing connection to authentication server", EventType.NETWORK_EVENT, (2.0, 10.0)),
                LogTemplate("NetworkManager", "DataTransfer", "network", 2,
                            "Received authentication response: HTTP 200 OK", EventType.NETWORK_EVENT, (1.0, 5.0)),
            ],

            EventType.PERFORMANCE_CHECK: [
                LogTemplate("PerformanceMonitor", "SystemMetrics", "root", 2,
                            "UI switch completed in {duration} seconds", EventType.PERFORMANCE_CHECK, (3.0, 15.0)),
                LogTemplate("DatabaseManager", "QueryExecutor", "db", 2,
                            "Query completed in {query_time}ms, returned {row_count} rows",
                            EventType.PERFORMANCE_CHECK, (1.0, 8.0)),
            ],
        }

    def _generate_log_entry(self, template: LogTemplate, **kwargs) -> str:
        """Generate a single log entry from a template"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Remove last 3 digits for milliseconds

        pid = self.pid_counter
        thread_id = f"0x7fff8a{random.randint(100000, 999999):06x}"
        process_id = self.process_id_counter

        # Format message with provided kwargs
        try:
            message = template.message_template.format(**kwargs)
        except KeyError:
            # If formatting fails, use template as-is
            message = template.message_template

        # Handle level names
        level_names = {1: "Debug", 2: "Info", 3: "Warning", 4: "Error"}
        level_name = level_names.get(template.level, "Info")

        # Format process name
        process_name = template.process_name.format(**kwargs) if "{" in template.process_name else template.process_name

        log_entry = (f"{timestamp} {template.component} {template.subcomponent} "
                     f"{pid} {thread_id} {template.level} {process_id} {process_name} "
                     f"{level_name}: {message}")

        # Increment counters
        self.pid_counter += 1
        self.process_id_counter += 1

        return log_entry

    def _get_random_event_type(self) -> EventType:
        """Select a random event type based on weights"""
        events = list(self.event_weights.keys())
        weights = list(self.event_weights.values())
        return random.choices(events, weights=weights)[0]

    def _generate_event_data(self, event_type: EventType) -> Dict[str, Any]:
        """Generate contextual data for specific event types"""
        data = {}

        if event_type in [EventType.CARD_DETECTION, EventType.USER_AUTH]:
            data["card_id"] = random.choice(self.available_cards)
            data["username"] = "admin"

        elif event_type == EventType.SESSION_CREATE:
            if self.current_users:
                data["username"] = random.choice(self.current_users)
            else:
                data["username"] = "admin"
        
        elif event_type == EventType.UI_SWITCH:
            data["username"] = "admin"

        elif event_type == EventType.SYSTEM_MONITOR:
            data.update({
                "cpu_usage": round(random.uniform(5.0, 95.0), 1),
                "memory_usage": round(random.uniform(1.0, 7.5), 1),
                "memory_percent": random.randint(15, 85),
                "load1": round(random.uniform(0.5, 3.0), 2),
                "load2": round(random.uniform(0.5, 3.0), 2),
                "load3": round(random.uniform(0.5, 3.0), 2),
            })

        elif event_type == EventType.PERFORMANCE_CHECK:
            data.update({
                "duration": round(random.uniform(0.5, 5.0), 3),
                "query_time": random.randint(10, 500),
                "row_count": random.randint(1, 100),
            })

        elif event_type == EventType.ERROR_EVENT:
            data["card_id"] = "INVALID_" + random.choice(self.available_cards)

        return data

    def _event_generator(self):
        """Background thread that generates events at realistic intervals"""
        print(f"📝 Event generator started")

        while self.running:
            try:
                # Select random event type
                event_type = self._get_random_event_type()

                # Get templates for this event type
                templates = self.log_templates.get(event_type, [])
                if not templates:
                    time.sleep(0.1)  # faster idle
                    continue

                # Generate contextual data
                event_data = self._generate_event_data(event_type)

                # For USER_AUTH, update active users
                if event_type == EventType.USER_AUTH:
                    username = event_data.get("username")
                    if username and username not in self.current_users:
                        self.current_users.append(username)
                        if len(self.current_users) > 3:
                            self.current_users.pop(0)

                # Generate log entries
                for idx, template in enumerate(templates):
                    if (
                            event_type == EventType.UI_SWITCH
                            and idx > 0
                            and templates[idx - 1].message_template == "Switching to Login UI"
                            and template.message_template == "Opened proxcard screen"
                    ):
                        # Force real time gap BEFORE creating second entry
                        time.sleep(random.uniform(1.0, 3.0))
                        log_entry = self._generate_log_entry(template, **event_data)
                    else:
                        log_entry = self._generate_log_entry(template, **event_data)

                    # Use faster normal delays for all other entries
                    if event_type == EventType.UI_SWITCH and "Opened proxcard screen" in template.message_template:
                        # already delayed above, so no queue delay here
                        self.event_queue.put((log_entry, 0))
                    else:
                        delay = random.uniform(
                            max(template.delay_range[0] * 0.3, 0.05),  # 70% faster
                            max(template.delay_range[1] * 0.3, 0.1)
                        )
                        self.event_queue.put((log_entry, delay))

                # Faster base delay between events
                base_delay = random.uniform(0.1, 0.5)

                # Busy/quiet period adjustment
                if random.random() < 0.2:  # busy period
                    base_delay *= 0.2
                elif random.random() < 0.1:  # quiet period
                    base_delay *= 1.0  # still fast

                time.sleep(base_delay)

            except Exception as e:
                print(f"❌ Error in event generator: {e}")
                time.sleep(0.1)

    def _log_writer(self):
        """Background thread that writes log entries to file"""
        print(f"📁 Log writer started - writing to {self.log_file_path}")

        while self.running:
            try:
                # Get log entry from queue (block for up to 1 second)
                try:
                    log_entry, delay = self.event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Wait for the specified delay
                if delay > 0:
                    time.sleep(delay)

                # Check file size and rotate if needed
                if self.log_file_path.exists() and self.log_file_path.stat().st_size > self.max_file_size:
                    self._rotate_log_file()

                # Write log entry
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
                    f.flush()  # Ensure immediate write

                self.event_queue.task_done()

            except Exception as e:
                print(f"❌ Error in log writer: {e}")
                time.sleep(1.0)

    def _rotate_log_file(self):
        """Rotate log file when it gets too large"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.log_file_path.with_suffix(f".{timestamp}.bak")

        try:
            self.log_file_path.rename(backup_path)
            print(f"🔄 Log file rotated: {backup_path}")
        except Exception as e:
            print(f"❌ Failed to rotate log file: {e}")

    def start(self):
        """Start the background log simulation"""
        if self.running:
            print("⚠️  Simulator already running")
            return

        print(f"🚀 Starting Dynamic Log Simulator")
        print(f"📁 Log file: {self.log_file_path.absolute()}")
        print(f"📏 Max file size: {self.max_file_size / 1024 / 1024:.1f} MB")
        print(f"⏹️  Press Ctrl+C to stop")

        self.running = True

        # Start background threads
        self.event_generator_thread = threading.Thread(target=self._event_generator, daemon=True)
        self.writer_thread = threading.Thread(target=self._log_writer, daemon=True)

        self.event_generator_thread.start()
        self.writer_thread.start()

        # Write initial startup message
        startup_msg = self._generate_log_entry(
            LogTemplate("LogSimulator", "Startup", "simulator", 2,
                        "Dynamic log simulation started", EventType.SYSTEM_MONITOR),

        )
        self.event_queue.put((startup_msg, 0))

        print("✅ Simulator started successfully")

    def stop(self):
        """Stop the background log simulation"""
        if not self.running:
            return

        print("\n🛑 Stopping Dynamic Log Simulator...")
        self.running = False

        # Write shutdown message
        if self.event_queue:
            shutdown_msg = self._generate_log_entry(
                LogTemplate("LogSimulator", "Shutdown", "simulator", 2,
                            "Dynamic log simulation stopped", EventType.SYSTEM_MONITOR),
            )
            self.event_queue.put((shutdown_msg, 0))

        # Wait for threads to finish
        if self.event_generator_thread and self.event_generator_thread.is_alive():
            self.event_generator_thread.join(timeout=2.0)

        if self.writer_thread and self.writer_thread.is_alive():
            self.writer_thread.join(timeout=2.0)

        print("✅ Simulator stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current simulator status"""
        return {
            "running": self.running,
            "log_file": str(self.log_file_path),
            "file_exists": self.log_file_path.exists(),
            "file_size": self.log_file_path.stat().st_size if self.log_file_path.exists() else 0,
            "queue_size": self.event_queue.qsize(),
            "current_users": self.current_users,
        }


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global simulator
    if 'simulator' in globals():
        simulator.stop()
    sys.exit(0)


def main():
    """Main function for running the simulator"""
    global simulator

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Dynamic Log Simulator")
    parser.add_argument("--log-file", default="dynamic_test.log",
                        help="Path to log file (default: dynamic_test.log)")
    parser.add_argument("--max-size", type=int, default=10,
                        help="Maximum log file size in MB (default: 10)")
    parser.add_argument("--quiet", action="store_true",
                        help="Reduce output verbosity")
    parser.add_argument("--status-interval", type=int, default=30,
                        help="Status update interval in seconds (default: 30)")

    args = parser.parse_args()

    # Create simulator
    max_size_bytes = args.max_size * 1024 * 1024
    simulator = DynamicLogSimulator(args.log_file, max_size_bytes)

    try:
        # Start simulation
        simulator.start()

        # Run until interrupted
        last_status_time = time.time()

        while True:
            time.sleep(1.0)

            # Print status updates periodically
            current_time = time.time()
            if current_time - last_status_time >= args.status_interval:
                if not args.quiet:
                    status = simulator.get_status()
                    file_size_mb = status['file_size'] / 1024 / 1024
                    print(f"📊 Status: {status['queue_size']} events queued, "
                          f"{file_size_mb:.2f}MB written, "
                          f"{len(status['current_users'])} active users")

                last_status_time = current_time

    except KeyboardInterrupt:
        pass
    finally:
        simulator.stop()


if __name__ == "__main__":
    main()