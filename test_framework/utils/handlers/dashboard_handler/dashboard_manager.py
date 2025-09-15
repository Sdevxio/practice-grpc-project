"""
Performance Dashboard Manager - Enterprise SQLite Integration

High-performance dashboard manager with SQLite persistence for unlimited
performance history tracking and professional-grade data management.

Features:
- Enterprise SQLite database with connection pooling
- Unlimited historical data retention  
- Advanced trend analysis and statistics
- Self-contained HTML dashboards with embedded data
- Backward compatibility with JSON-based workflows

Version: 2.0.0 - SQLite Integration
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from test_framework.utils import get_logger
from .json_data_handler import JsonDataHandler
from .sqlite_handler import PerformanceDatabase, PerformanceDatabaseError


class PerformanceDashboardManager:
    """Enterprise performance dashboard manager with SQLite persistence.
    
    Provides unlimited performance data retention, advanced analytics,
    and professional-grade dashboard generation with embedded historical data.
    """
    
    def __init__(self, artifacts_dir: str = None, logger=None, use_sqlite: bool = True, 
                 db_path: str = None):
        """Initialize dashboard manager with enterprise SQLite backend.
        
        Args:
            artifacts_dir: Directory for artifacts output (default: artifacts/)
            logger: Logger instance for operation tracking
            use_sqlite: Enable SQLite database backend (default: True)
            db_path: Custom database path (default: C:\\performance-data\\performance.db)
        """
        self.artifacts_dir = artifacts_dir or self._get_artifacts_dir()
        self.logger = logger or get_logger("performance_dashboard")
        self.use_sqlite = use_sqlite
        
        # Initialize database handlers
        if self.use_sqlite:
            try:
                self.db = PerformanceDatabase(db_path=db_path, logger=self.logger)
                self.logger.info("SQLite backend initialized successfully")
            except PerformanceDatabaseError as e:
                self.logger.error(f"SQLite initialization failed: {e}")
                self.logger.warning("Falling back to JSON backend")
                self.use_sqlite = False
                self._init_json_backend()
        else:
            self._init_json_backend()
    
    def _init_json_backend(self) -> None:
        """Initialize JSON-based backend for fallback compatibility."""
        self.json_handler = JsonDataHandler(base_output_dir=self.artifacts_dir)
        self.history_file = os.path.join(self.artifacts_dir, "performance", "performance_history.json")
        self.logger.info("JSON backend initialized")
    
    def _get_artifacts_dir(self) -> str:
        """Get artifacts directory - always use artifacts/."""
        return "artifacts"
    
    def save_timing_result(self, test_name: str, duration: float, success: bool = True, 
                          log_entry_timestamp: str = None, log_entry_message: str = None,
                          additional_data: Dict[str, Any] = None) -> str:
        """Save timing result with enterprise SQLite backend or JSON fallback."""
        now = datetime.now()
        timing_data = {
            "test_name": test_name,
            "duration": duration,
            "success": success,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "test_run_timestamp": now.isoformat(),
        }
        
        # Include actual log entry data if found
        if log_entry_timestamp and log_entry_message:
            timing_data["log_entry_timestamp"] = log_entry_timestamp
            timing_data["log_entry_message"] = log_entry_message
            timing_data["log_correlation"] = True
        else:
            timing_data["log_entry_timestamp"] = None
            timing_data["log_entry_message"] = "No matching log entry found"
            timing_data["log_correlation"] = False
        
        if additional_data:
            timing_data.update(additional_data)
        
        # Primary: SQLite Backend
        if self.use_sqlite:
            try:
                record_id = self.db.save_performance_result(timing_data)
                self.logger.info(f"📈 Saved to SQLite: {test_name} = {duration:.3f}s (ID: {record_id})")
                return f"sqlite_record_{record_id}"
            except PerformanceDatabaseError as e:
                self.logger.error(f"SQLite save failed: {e}")
                self.logger.warning("Attempting JSON fallback")
        
        # Fallback: JSON Backend
        try:
            individual_file = self.json_handler.save_performance_data(
                data=timing_data,
                test_name=test_name,
                subcategory="ui_timing"
            )
            
            history_file = self.json_handler.append_to_summary_file(
                data=timing_data,
                summary_filename="performance_history.json",
                subfolder="performance"
            )
            
            self.logger.info(f"📈 Saved to JSON: {test_name} = {duration:.3f}s")
            self.logger.info(f"📁 Files: {individual_file}, {history_file}")
            return individual_file
            
        except Exception as e:
            self.logger.error(f"All save methods failed: {e}")
            return None
    
    def measure_and_track_timing(self, test_name: str, start_time, end_time, data_extractor, expected_user: str = None) -> str:
        """Complete timing measurement and dashboard generation in one method."""
        # Simple timing calculation
        if hasattr(end_time, 'timestamp'):
            session_time = data_extractor._parse_timestamp(end_time.timestamp)
            time_diff = (session_time - start_time).total_seconds()
        else:
            time_diff = 0.0
        
        self.logger.info(f"{test_name}: {time_diff:.3f}s delay")
        
        # Extract log entry data if end_time is a log entry
        log_timestamp = getattr(end_time, 'timestamp', None) if hasattr(end_time, 'timestamp') else None
        log_message = getattr(end_time, 'message', None) if hasattr(end_time, 'message') else None
        
        # Save timing result
        self.save_timing_result(
            test_name=test_name,
            duration=time_diff,
            success=True,
            log_entry_timestamp=log_timestamp,
            log_entry_message=log_message,
            additional_data={
                "test_type": test_name,
                "tap_timestamp": start_time.isoformat() if hasattr(start_time, 'isoformat') else str(start_time),
                "session_timestamp": log_timestamp,
                "expected_user": expected_user
            }
        )
        
        # Generate dashboard and summary
        dashboard_file = self.generate_html_dashboard()
        if dashboard_file:
            self.logger.info(f"📊 Dashboard updated: {dashboard_file}")
        
        summary = self.generate_dashboard_summary()
        self.logger.info(summary)
        
        return f"{time_diff:.3f}s"
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load performance history from SQLite or JSON fallback."""
        # Primary: SQLite Backend
        if self.use_sqlite:
            try:
                history = self.db.get_performance_history(limit=1000)  # Last 1000 tests
                self.logger.debug(f"Loaded {len(history)} records from SQLite")
                return history
            except PerformanceDatabaseError as e:
                self.logger.error(f"SQLite load failed: {e}")
                self.logger.warning("Attempting JSON fallback")
        
        # Fallback: JSON Backend  
        try:
            if hasattr(self, 'history_file') and os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "test_results" in data:
                        return data["test_results"]
                    elif isinstance(data, list):
                        return data
                    else:
                        self.logger.warning(f"Unexpected JSON history format: {type(data)}")
        except Exception as e:
            self.logger.warning(f"Could not load JSON history: {e}")
        
        return []
    
    def generate_dashboard_summary(self) -> str:
        """Generate simple dashboard summary."""
        history = self._load_history()
        
        if not history:
            return "📊 Performance Dashboard: No data available"
        
        successful_tests = [r for r in history if r.get("success", False)]
        
        if not successful_tests:
            return "📊 Performance Dashboard: No successful tests"
        
        durations = [r["duration"] for r in successful_tests]
        latest = durations[-1]
        average = sum(durations) / len(durations)
        best = min(durations)
        worst = max(durations)
        
        # Simple trend calculation
        if len(durations) >= 4:
            mid = len(durations) // 2
            recent_avg = sum(durations[mid:]) / len(durations[mid:])
            earlier_avg = sum(durations[:mid]) / len(durations[:mid])
            change = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            if change < -5:
                trend = "📈 Improving"
            elif change > 5:
                trend = "📉 Degrading"
            else:
                trend = "📊 Stable"
        else:
            trend = "📊 Need more data"
        
        return f"""
📊 Performance Dashboard
========================
🎯 Latest: {latest:.3f}s
📈 Average: {average:.3f}s
⚡ Best: {best:.3f}s
🐌 Worst: {worst:.3f}s
📊 Tests: {len(successful_tests)}/{len(history)}
{trend}
"""

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics from SQLite or JSON fallback."""
        # Primary: SQLite Backend (with optimized aggregation)
        if self.use_sqlite:
            try:
                stats = self.db.get_performance_statistics()
                self.logger.debug(f"Retrieved statistics from SQLite: {stats['total_tests']} total tests")
                return stats
            except PerformanceDatabaseError as e:
                self.logger.error(f"SQLite stats failed: {e}")
                self.logger.warning("Attempting JSON fallback for statistics")
        
        # Fallback: JSON Backend (legacy calculation)
        history = self._load_history()
        
        if not history:
            return {
                "total_tests": 0,
                "successful_tests": 0,
                "average_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "latest_duration": 0,
                "trend": "no_data"
            }
        
        successful_tests = [r for r in history if r.get("success", False)]
        
        if not successful_tests:
            return {
                "total_tests": len(history),
                "successful_tests": 0,
                "average_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "latest_duration": 0,
                "trend": "no_successful_tests"
            }
        
        durations = [r["duration"] for r in successful_tests]
        
        # Calculate trend (legacy method)
        trend = "insufficient_data"
        if len(durations) >= 4:
            mid = len(durations) // 2
            recent_avg = sum(durations[mid:]) / len(durations[mid:])
            earlier_avg = sum(durations[:mid]) / len(durations[:mid])
            change = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            if change < -5:
                trend = "improving"
            elif change > 5:
                trend = "degrading"
            else:
                trend = "stable"
        
        return {
            "total_tests": len(history),
            "successful_tests": len(successful_tests),
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "latest_duration": durations[-1],
            "trend": trend
        }

    def generate_html_dashboard(self) -> str:
        """Generate completely self-contained HTML dashboard with embedded historical data."""
        # Load ALL historical data (not limited)
        if self.use_sqlite and hasattr(self, 'db'):
            try:
                # Get unlimited historical data for complete dashboard
                history = self.db.get_performance_history()  # No limit - get everything
                self.logger.info(f"Loaded {len(history)} complete historical records for dashboard")
            except Exception as e:
                self.logger.warning(f"SQLite data load failed, using fallback: {e}")
                history = self._load_history()
        else:
            history = self._load_history()
        
        stats = self.get_performance_statistics()
        
        # Generate self-contained HTML with embedded data
        dashboard_file = os.path.join(self.artifacts_dir, "performance_dashboard.html")
        
        try:
            html_content = self._generate_self_contained_html(history, stats)
            
            with open(dashboard_file, 'w') as f:
                f.write(html_content)
            
            self.logger.info(f"📊 Self-contained HTML dashboard generated: {dashboard_file}")
            self.logger.info(f"📈 Dashboard contains {len(history)} historical records")
            return dashboard_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML dashboard: {e}")
            return None
    
    def _prepare_chart_data(self, history: List[Dict[str, Any]]) -> Dict[str, List]:
        """Prepare comprehensive chart data from complete historical data."""
        if not history:
            return {
                'labels': [],
                'values': [],
                'tooltips': []
            }
        
        # Prepare chart data with timestamps and tooltips
        chart_data = {
            'labels': [],
            'values': [],
            'tooltips': []
        }
        
        for i, record in enumerate(history):
            # Chart label (simple numbering for large datasets)
            if len(history) <= 50:
                try:
                    timestamp = datetime.fromisoformat(record.get('test_run_timestamp', ''))
                    chart_data['labels'].append(timestamp.strftime('%m/%d %H:%M'))
                except:
                    chart_data['labels'].append(f"Test {i+1}")
            else:
                chart_data['labels'].append(f"Test {i+1}")
            
            # Duration value
            chart_data['values'].append(record.get('duration', 0))
            
            # Detailed tooltip
            try:
                timestamp = datetime.fromisoformat(record.get('test_run_timestamp', ''))
                tooltip = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {record.get('duration', 0):.3f}s"
            except:
                tooltip = f"Test {i+1} - {record.get('duration', 0):.3f}s"
            
            chart_data['tooltips'].append(tooltip)
        
        return chart_data
    
    def _generate_table_rows(self, recent_history: List[Dict[str, Any]]) -> str:
        """Generate HTML table rows for recent test results."""
        if not recent_history:
            return '<tr><td colspan="4" style="text-align: center; color: #7f8c8d;">No recent test data available</td></tr>'
        
        table_rows = ""
        
        # Show most recent tests first
        for test in reversed(recent_history):
            try:
                test_time = datetime.fromisoformat(test.get('test_run_timestamp', ''))
                formatted_time = test_time.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = f"{test.get('date', '')} {test.get('time', '')}"
            
            duration = test.get('duration', 0)
            duration_ms = duration * 1000
            
            # Color coding based on performance
            if duration < 3.0:
                status = "🟢 Good"
                duration_class = "duration-good"
            elif duration < 10.0:
                status = "🟡 OK"
                duration_class = "duration-warning"
            else:
                status = "🔴 Slow"
                duration_class = "duration-bad"
            
            table_rows += f'''
                <tr>
                    <td>{formatted_time}</td>
                    <td class="{duration_class}">{duration:.3f}s</td>
                    <td class="{duration_class}">{duration_ms:.0f}ms</td>
                    <td>{status}</td>
                </tr>'''
        
        return table_rows
    
    def _get_trend_info(self, trend: str) -> Dict[str, str]:
        """Get trend display information."""
        trend_mapping = {
            'improving': {
                'class': 'improving',
                'icon': '📈',
                'title': 'Improving'
            },
            'degrading': {
                'class': 'degrading', 
                'icon': '📉',
                'title': 'Degrading'
            },
            'stable': {
                'class': 'stable',
                'icon': '📊',
                'title': 'Stable'
            }
        }
        
        return trend_mapping.get(trend, {
            'class': 'stable',
            'icon': '📋',
            'title': 'Insufficient Data'
        })
    
    def _generate_database_info_section(self) -> str:
        """Generate database information for dashboard footer."""
        try:
            db_info = self.get_database_info()
            backend = db_info.get('backend', 'Unknown')
            total_records = db_info.get('total_records', 0)
            
            if backend == 'SQLite':
                file_size = db_info.get('file_size_mb', 0)
                return f"SQLite Database • {total_records} records • {file_size:.1f} MB"
            else:
                return f"{backend} Backend • {total_records} records"
                
        except Exception as e:
            return "Database info unavailable"
    
    def _generate_self_contained_html(self, history: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Generate complete self-contained HTML using separate template file with embedded data."""
        
        # Prepare comprehensive chart data from ALL history
        chart_data = self._prepare_chart_data(history)
        
        # Generate table rows for recent tests
        table_rows = self._generate_table_rows(history[-20:] if history else [])
        
        # Get trend styling
        trend_info = self._get_trend_info(stats['trend'])
        
        # Generate database info section
        db_info = self._generate_database_info_section()
        
        # Load HTML template
        template_path = os.path.join(os.path.dirname(__file__), "dashboard_self_contained.html")
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        except Exception as e:
            self.logger.error(f"Failed to load self-contained dashboard template: {e}")
            raise PerformanceDatabaseError(f"Template loading failed: {e}")
        
        # Replace template placeholders with actual data
        html_content = html_template.format(
            latest_duration=stats['latest_duration'],
            average_duration=stats['average_duration'],
            min_duration=stats['min_duration'],
            max_duration=stats['max_duration'],
            total_tests=stats['total_tests'],
            trend_class=trend_info['class'],
            trend_icon=trend_info['icon'],
            trend_title=trend_info['title'],
            database_info=db_info,
            table_rows=table_rows,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_records=len(history),
            embedded_chart_data=json.dumps(chart_data, indent=4)
        )
        
        return html_content
    
    def _get_current_time(self):
        """Helper to get current timestamp."""
        return datetime.now()
    
    # Enterprise Database Management Methods
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information and health metrics."""
        if self.use_sqlite and hasattr(self, 'db'):
            try:
                db_info = self.db.get_database_info()
                db_info['backend'] = 'SQLite'
                return db_info
            except PerformanceDatabaseError as e:
                self.logger.error(f"Failed to get database info: {e}")
        
        # Fallback for JSON backend
        json_info = {
            'backend': 'JSON',
            'database_path': getattr(self, 'history_file', 'N/A'),
            'total_records': len(self._load_history()),
            'file_size_bytes': 0,
            'file_size_mb': 0
        }
        
        if hasattr(self, 'history_file') and os.path.exists(self.history_file):
            file_size = os.path.getsize(self.history_file)
            json_info['file_size_bytes'] = file_size
            json_info['file_size_mb'] = round(file_size / (1024 * 1024), 2)
        
        return json_info
    
    def backup_database(self, backup_path: str = None) -> Optional[str]:
        """Create database backup (SQLite only)."""
        if self.use_sqlite and hasattr(self, 'db'):
            try:
                backup_file = self.db.backup_database(backup_path)
                self.logger.info(f"✅ Database backup created: {backup_file}")
                return backup_file
            except PerformanceDatabaseError as e:
                self.logger.error(f"Database backup failed: {e}")
                return None
        else:
            self.logger.warning("Database backup only available for SQLite backend")
            return None
    
    def get_filtered_history(self, test_name: str = None, days: int = None, 
                           limit: int = None) -> List[Dict[str, Any]]:
        """Get filtered performance history with advanced options."""
        if self.use_sqlite and hasattr(self, 'db'):
            try:
                return self.db.get_performance_history(
                    test_name=test_name, 
                    days=days, 
                    limit=limit
                )
            except PerformanceDatabaseError as e:
                self.logger.error(f"Filtered history query failed: {e}")
        
        # Fallback: Basic filtering on loaded history
        history = self._load_history()
        
        if test_name:
            history = [r for r in history if r.get('test_name') == test_name]
        
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            history = [r for r in history 
                      if datetime.fromisoformat(r.get('test_run_timestamp', '')) >= cutoff]
        
        if limit:
            history = history[-limit:]  # Get most recent
        
        return history
    
    def close(self) -> None:
        """Close database connections and cleanup resources."""
        if self.use_sqlite and hasattr(self, 'db'):
            try:
                self.db.close()
                self.logger.info("Database connections closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing database: {e}")
        
        self.logger.info("Performance dashboard manager shutdown complete")