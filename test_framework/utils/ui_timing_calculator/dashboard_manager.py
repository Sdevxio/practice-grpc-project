"""
Performance Dashboard Manager - Uses existing JsonDataHandler for persistence.

Integrates with existing timing_calculator.py and json_data_handler.py infrastructure.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from test_framework.utils import get_logger
from .json_data_handler import JsonDataHandler


class PerformanceDashboardManager:
    """Performance dashboard manager using existing JsonDataHandler."""
    
    def __init__(self, artifacts_dir: str = None, logger=None):
        self.artifacts_dir = artifacts_dir or self._get_artifacts_dir()
        self.logger = logger or get_logger("performance_dashboard")
        
        # Use existing JsonDataHandler
        self.json_handler = JsonDataHandler(base_output_dir=self.artifacts_dir)
        self.history_file = os.path.join(self.artifacts_dir, "performance", "performance_history.json")
    
    def _get_artifacts_dir(self) -> str:
        """Get artifacts directory - always use artifacts/."""
        return "artifacts"
    
    def save_timing_result(self, test_name: str, duration: float, success: bool = True, 
                          log_entry_timestamp: str = None, log_entry_message: str = None,
                          additional_data: Dict[str, Any] = None) -> str:
        """Save timing result with actual log entry data when available."""
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
        
        try:
            # Save individual performance file using existing handler
            individual_file = self.json_handler.save_performance_data(
                data=timing_data,
                test_name=test_name,
                subcategory="ui_timing"
            )
            
            # Also append to summary/history file
            history_file = self.json_handler.append_to_summary_file(
                data=timing_data,
                summary_filename="performance_history.json",
                subfolder="performance"
            )
            
            self.logger.info(f"📈 Saved timing result: {test_name} = {duration:.3f}s")
            self.logger.info(f"📁 Files: {individual_file}, {history_file}")
            
            return individual_file
            
        except Exception as e:
            self.logger.error(f"Failed to save timing result: {e}")
            return None
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load performance history from JsonDataHandler format."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    # JsonDataHandler saves in {"test_results": []} format
                    if isinstance(data, dict) and "test_results" in data:
                        return data["test_results"]
                    elif isinstance(data, list):
                        return data
                    else:
                        self.logger.warning(f"Unexpected history format: {type(data)}")
                        return []
        except Exception as e:
            self.logger.warning(f"Could not load history: {e}")
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
        """Get performance statistics for dashboard and analysis."""
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
        
        # Calculate trend
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
        """Generate HTML dashboard file."""
        history = self._load_history()
        stats = self.get_performance_statistics()
        
        # Debug logging
        self.logger.info(f"📊 Loading dashboard data: {len(history)} history entries")
        self.logger.info(f"📊 Stats: {stats}")
        
        # Prepare data for chart
        if history:
            chart_data = {
                "labels": [f"Test {i+1}" for i in range(len(history))],
                "durations": [r["duration"] for r in history],
                "test_names": [r["test_name"] for r in history]
            }
        else:
            chart_data = {"labels": [], "durations": [], "test_names": []}
        
        # Get trend styling
        trend_class = stats['trend'].replace('_', '')
        if stats['trend'] == 'improving':
            trend_icon = '📈'
            trend_title = 'Improving'
        elif stats['trend'] == 'degrading':
            trend_icon = '📉'
            trend_title = 'Degrading'
        elif stats['trend'] == 'stable':
            trend_icon = '📊'
            trend_title = 'Stable'
        else:
            trend_icon = '📋'
            trend_title = 'Insufficient Data'
            trend_class = 'stable'
        
        # Generate table rows for recent test results
        table_rows = ""
        if history:
            # Show most recent 10 results, reversed to show newest first
            recent_tests = list(reversed(history[-10:]))
            for test in recent_tests:
                try:
                    # Parse test timestamp
                    test_time = datetime.fromisoformat(test.get('test_run_timestamp', ''))
                    formatted_time = test_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = f"{test.get('date', '')} {test.get('time', '')}"
                
                duration = test.get('duration', 0)
                duration_ms = duration * 1000
                
                # Determine status and color based on duration (adjust thresholds as needed)
                if duration < 5.0:  # Good performance
                    status = "🟢 Good"
                    duration_class = "duration-good"
                elif duration < 15.0:  # Warning
                    status = "🟡 OK"
                    duration_class = "duration-warning"
                else:  # Slow
                    status = "🔴 Slow"
                    duration_class = "duration-bad"
                
                table_rows += f"""
                    <tr>
                        <td>{formatted_time}</td>
                        <td class="{duration_class}">{duration:.3f}s</td>
                        <td class="{duration_class}">{duration_ms:.0f}ms</td>
                        <td>{status}</td>
                    </tr>"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
            position: relative;
        }}
        
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3498db, #2ecc71, #f39c12, #e74c3c);
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            margin: 10px 0 0 0;
            opacity: 0.8;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 28px 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(0,0,0,0.05);
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }}
        
        .stat-card:hover::before {{
            opacity: 1;
        }}
        
        .stat-value {{
            font-size: 2.4em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 8px;
            line-height: 1;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 500;
        }}
        
        .latest-test {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
        }}
        
        .latest-test .stat-value {{
            color: white;
        }}
        
        .latest-test .stat-label {{
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
        }}
        
        .trend-section {{
            background: #f8f9fa;
            padding: 20px 35px;
            display: flex;
            justify-content: center;
            align-items: center;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .trend-badge {{
            background: white;
            padding: 15px 25px;
            border-radius: 50px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            font-size: 1.1em;
            color: #2c3e50;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .trend-badge.improving {{
            border-color: #27ae60;
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            color: white;
        }}
        
        .trend-badge.degrading {{
            border-color: #e74c3c;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
        }}
        
        .trend-badge.stable {{
            border-color: #95a5a6;
            background: #ecf0f1;
            color: #2c3e50;
        }}
        
        .trend-icon {{
            font-size: 1.4em;
        }}
        
        .trend-text {{
            font-size: 0.9em;
            margin-right: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .chart-container {{
            padding: 35px;
            background: white;
            margin: 0;
        }}
        
        .chart-title {{
            text-align: center;
            font-size: 1.6em;
            color: #2c3e50;
            margin-bottom: 25px;
            font-weight: 400;
            position: relative;
        }}
        
        .chart-title::after {{
            content: '';
            display: block;
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            margin: 10px auto 0;
            border-radius: 2px;
        }}
        
        .timing-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 25px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .timing-table th,
        .timing-table td {{
            padding: 15px 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .timing-table th {{
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        
        .timing-table tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        .timing-table tr:hover {{
            background: #e8f4fd;
            transform: scale(1.02);
            transition: all 0.2s ease;
        }}
        
        .timing-table td:first-child {{
            font-weight: 500;
            color: #34495e;
        }}
        
        .duration-good {{ color: #27ae60; font-weight: 700; }}
        .duration-warning {{ color: #f39c12; font-weight: 700; }}
        .duration-bad {{ color: #e74c3c; font-weight: 700; }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            background: #f8f9fa;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Performance Dashboard</h1>
            <div class="subtitle">Real-time monitoring of test performance - {len(history)} tests tracked</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card latest-test">
                <div class="stat-value">{stats['latest_duration']:.2f}s</div>
                <div class="stat-label">Latest Test</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['average_duration']:.2f}s</div>
                <div class="stat-label">Average Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['min_duration']:.2f}s</div>
                <div class="stat-label">Best Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_duration']:.2f}s</div>
                <div class="stat-label">Worst Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['successful_tests']}/{stats['total_tests']}</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <div class="trend-section">
            <div class="trend-badge {trend_class}">
                <span class="trend-text">Performance Trend:</span>
                <span class="trend-icon">{trend_icon}</span>
                <span>{trend_title}</span>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Performance Timing Trend ({len(history)} tests)</div>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Recent Test Results</h3>
            <table class="timing-table">
                <thead>
                    <tr>
                        <th>Test Time</th>
                        <th>Duration</th>
                        <th>Milliseconds</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {chart_data['labels']},
                datasets: [{{
                    label: 'Response Time (seconds)',
                    data: {chart_data['durations']},
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3498db',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }},
                    tooltip: {{
                        callbacks: {{
                            title: function(context) {{
                                const index = context[0].dataIndex;
                                return {chart_data['test_names']}[index] || 'Test ' + (index + 1);
                            }},
                            label: function(context) {{
                                return 'Duration: ' + context.parsed.y.toFixed(3) + 's';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Duration (seconds)'
                        }},
                        grid: {{
                            color: 'rgba(0,0,0,0.1)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Test Run'
                        }},
                        grid: {{
                            color: 'rgba(0,0,0,0.1)'
                        }}
                    }}
                }},
                elements: {{
                    point: {{
                        hoverBackgroundColor: '#2980b9'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
        
        # Save HTML dashboard
        dashboard_file = os.path.join(self.artifacts_dir, "performance_dashboard.html")
        try:
            with open(dashboard_file, 'w') as f:
                f.write(html_content)
            
            self.logger.info(f"📊 HTML dashboard generated: {dashboard_file}")
            return dashboard_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML dashboard: {e}")
            return None