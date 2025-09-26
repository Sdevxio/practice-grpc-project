import json
from datetime import datetime
from typing import Dict, Optional, Any, List

from test_framework.utils import get_logger


class WebAutomationRegistry:
    """
    Registry for managing web automation sessions, browser contexts, and configurations.
    
    This registry provides centralized management of:
    - Browser session configuration and state
    - Multi-user context isolation settings
    - Session lifecycle and cleanup tracking
    - Configuration templates for common scenarios
    - Performance and usage metrics
    
    Similar to TapperRegistry, this class helps manage the complexity of coordinating
    multiple browser sessions across different users and test scenarios while maintaining
    proper isolation and resource management.
    
    Attributes:
        logger: Logger instance for registry operations
        sessions: Active session tracking
        configurations: Predefined configuration templates
        metrics: Usage and performance tracking data
    
    Usage:
        registry = WebAutomationRegistry()
        
        # Register a new session
        session_config = {
            "user": "test_user",
            "browser": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        }
        session_id = registry.register_session("test_session", session_config)
        
        # Get session info
        session = registry.get_session(session_id)
        
        # Clean up
        registry.cleanup_session(session_id)
    """

    def __init__(self, logger: Optional[object] = None):
        """
        Initialize the WebAutomationRegistry.
        
        :param logger: Optional logger instance
        """
        self.logger = logger or get_logger("registry.web_automation")
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.configurations: Dict[str, Dict[str, Any]] = {}
        self.metrics: Dict[str, Any] = {
            "total_sessions": 0,
            "active_sessions": 0,
            "session_history": [],
            "performance_data": []
        }

        # Load default configurations
        self._load_default_configurations()

    def _load_default_configurations(self):
        """Load predefined configuration templates."""
        self.configurations = {
            "default": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "timeout": 30000,
                "wait_time": 1000
            },

            "mobile": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 375, "height": 667},
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
                "timeout": 30000,
                "wait_time": 1000,
                "device_scale_factor": 2
            },

            "debug": {
                "browser": "chromium",
                "headless": False,
                "viewport": {"width": 1920, "height": 1080},
                "devtools": True,
                "timeout": 60000,
                "wait_time": 2000,
                "slow_mo": 100
            },

            "performance": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 1920, "height": 1080},
                "timeout": 10000,
                "wait_time": 500,
                "disable_images": True,
                "disable_javascript": False
            }
        }

    def register_session(
            self,
            session_id: str,
            config: Dict[str, Any],
            user: str = "",
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new web automation session.
        
        :param session_id: Unique identifier for the session
        :param config: Session configuration parameters
        :param user: Target user for multi-user routing
        :param metadata: Additional session metadata
        :return: Registered session ID
        """
        if session_id in self.sessions:
            self.logger.warning(f"Session {session_id} already exists, updating configuration")

        session_data = {
            "session_id": session_id,
            "user": user,
            "config": config.copy(),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "status": "registered",
            "context_id": f"{user}_{session_id}" if user else session_id,
            "performance_metrics": {
                "script_executions": 0,
                "screenshots_taken": 0,
                "page_info_requests": 0,
                "total_execution_time": 0
            }
        }

        self.sessions[session_id] = session_data
        self.metrics["total_sessions"] += 1
        self.metrics["active_sessions"] = len(self.sessions)

        # Add to session history
        self.metrics["session_history"].append({
            "session_id": session_id,
            "user": user,
            "action": "registered",
            "timestamp": datetime.now().isoformat()
        })

        self.logger.info(f"Registered session: {session_id} for user: {user}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        :param session_id: Session identifier
        :return: Session data or None if not found
        """
        if session_id not in self.sessions:
            self.logger.warning(f"Session not found: {session_id}")
            return None

        session = self.sessions[session_id]
        session["last_accessed"] = datetime.now().isoformat()

        return session.copy()

    def update_session_config(self, session_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update session configuration.
        
        :param session_id: Session identifier
        :param config_updates: Configuration updates to apply
        :return: True if updated successfully, False if session not found
        """
        if session_id not in self.sessions:
            self.logger.warning(f"Cannot update config for unknown session: {session_id}")
            return False

        self.sessions[session_id]["config"].update(config_updates)
        self.sessions[session_id]["last_accessed"] = datetime.now().isoformat()

        self.logger.debug(f"Updated configuration for session: {session_id}")
        return True

    def record_operation(
            self,
            session_id: str,
            operation_type: str,
            execution_time: int,
            success: bool = True,
            metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record an operation for performance tracking.
        
        :param session_id: Session identifier
        :param operation_type: Type of operation (script, screenshot, page_info)
        :param execution_time: Execution time in milliseconds
        :param success: Whether the operation succeeded
        :param metadata: Additional operation metadata
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        metrics = session["performance_metrics"]

        # Update session metrics
        if operation_type == "script":
            metrics["script_executions"] += 1
        elif operation_type == "screenshot":
            metrics["screenshots_taken"] += 1
        elif operation_type == "page_info":
            metrics["page_info_requests"] += 1

        metrics["total_execution_time"] += execution_time
        session["last_accessed"] = datetime.now().isoformat()

        # Add to global performance data
        performance_record = {
            "session_id": session_id,
            "operation_type": operation_type,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.metrics["performance_data"].append(performance_record)

        # Keep only recent performance data (last 1000 operations)
        if len(self.metrics["performance_data"]) > 1000:
            self.metrics["performance_data"] = self.metrics["performance_data"][-1000:]

    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up and remove a session.
        
        :param session_id: Session identifier
        :return: True if cleaned up successfully, False if not found
        """
        if session_id not in self.sessions:
            self.logger.warning(f"Cannot cleanup unknown session: {session_id}")
            return False

        session = self.sessions.pop(session_id)
        self.metrics["active_sessions"] = len(self.sessions)

        # Add to session history
        self.metrics["session_history"].append({
            "session_id": session_id,
            "user": session["user"],
            "action": "cleaned_up",
            "timestamp": datetime.now().isoformat()
        })

        self.logger.info(f"Cleaned up session: {session_id}")
        return True

    def get_configuration_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a predefined configuration template.
        
        :param template_name: Name of the configuration template
        :return: Configuration template or None if not found
        """
        if template_name not in self.configurations:
            self.logger.warning(f"Configuration template not found: {template_name}")
            return None

        return self.configurations[template_name].copy()

    def create_session_from_template(
            self,
            session_id: str,
            template_name: str,
            user: str = "",
            config_overrides: Optional[Dict[str, Any]] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a session from a configuration template.
        
        :param session_id: Unique identifier for the session
        :param template_name: Name of the configuration template to use
        :param user: Target user for multi-user routing
        :param config_overrides: Configuration overrides to apply
        :param metadata: Additional session metadata
        :return: Session ID if created successfully, None otherwise
        """
        template = self.get_configuration_template(template_name)
        if not template:
            return None

        # Apply any overrides
        if config_overrides:
            template.update(config_overrides)

        # Add template info to metadata
        session_metadata = metadata or {}
        session_metadata["template"] = template_name

        return self.register_session(session_id, template, user, session_metadata)

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active sessions.
        
        :return: List of session summaries
        """
        summaries = []

        for session_id, session in self.sessions.items():
            summary = {
                "session_id": session_id,
                "user": session["user"],
                "context_id": session["context_id"],
                "created_at": session["created_at"],
                "last_accessed": session["last_accessed"],
                "status": session["status"],
                "operations": sum([
                    session["performance_metrics"]["script_executions"],
                    session["performance_metrics"]["screenshots_taken"],
                    session["performance_metrics"]["page_info_requests"]
                ])
            }
            summaries.append(summary)

        return summaries

    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a specific session.
        
        :param session_id: Session identifier
        :return: Session metrics or None if not found
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        metrics = session["performance_metrics"].copy()

        # Calculate derived metrics
        total_operations = (
                metrics["script_executions"] +
                metrics["screenshots_taken"] +
                metrics["page_info_requests"]
        )

        if total_operations > 0:
            metrics["average_execution_time"] = metrics["total_execution_time"] / total_operations
        else:
            metrics["average_execution_time"] = 0

        metrics["session_duration"] = (
                datetime.now() - datetime.fromisoformat(session["created_at"])
        ).total_seconds()

        return metrics

    def get_global_metrics(self) -> Dict[str, Any]:
        """
        Get global registry metrics.
        
        :return: Dictionary with global metrics
        """
        global_metrics = self.metrics.copy()

        # Calculate additional metrics
        if self.metrics["performance_data"]:
            execution_times = [op["execution_time"] for op in self.metrics["performance_data"]]
            global_metrics["average_execution_time"] = sum(execution_times) / len(execution_times)
            global_metrics["total_execution_time"] = sum(execution_times)

            # Success rate
            successful_ops = len([op for op in self.metrics["performance_data"] if op["success"]])
            global_metrics["success_rate"] = successful_ops / len(self.metrics["performance_data"])
        else:
            global_metrics["average_execution_time"] = 0
            global_metrics["total_execution_time"] = 0
            global_metrics["success_rate"] = 1.0

        return global_metrics

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up sessions that haven't been accessed within the specified time.
        
        :param max_age_hours: Maximum age in hours before cleanup
        :return: Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            last_accessed = datetime.fromisoformat(session["last_accessed"])
            age_hours = (now - last_accessed).total_seconds() / 3600

            if age_hours > max_age_hours:
                expired_sessions.append(session_id)

        cleanup_count = 0
        for session_id in expired_sessions:
            if self.cleanup_session(session_id):
                cleanup_count += 1

        if cleanup_count > 0:
            self.logger.info(f"Cleaned up {cleanup_count} expired sessions")

        return cleanup_count

    def export_metrics(self) -> str:
        """
        Export all metrics as JSON string.
        
        :return: JSON string with all registry data
        """
        export_data = {
            "global_metrics": self.get_global_metrics(),
            "active_sessions": self.list_active_sessions(),
            "session_metrics": {
                session_id: self.get_session_metrics(session_id)
                for session_id in self.sessions.keys()
            },
            "configurations": self.configurations,
            "export_timestamp": datetime.now().isoformat()
        }

        return json.dumps(export_data, indent=2)
