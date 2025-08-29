"""
Fixtures package for the test framework.

Domain-specific fixture architecture:
- config_fixtures: Test configuration and hardware settings
- session_fixtures: gRPC session management  
- monitoring_fixtures: Log streaming and event monitoring
- hardware_fixtures: Tapping and physical interactions
- workflow_fixtures: Combined workflow patterns
"""

from .config_fixtures import test_config, hardware_config
from .session_fixtures import session_manager, authenticated_session
from .hardware_fixtures import hardware_controller
from .workflow_fixtures import monitoring_ready_workflow, session_first_workflow, clean_state_workflow

__all__ = [
    # Configuration
    'test_config',
    'hardware_config',
    
    # Session management
    'session_manager', 
    'authenticated_session',
    
    # Hardware
    'hardware_controller',
    
    # Workflows
    'monitoring_ready_workflow',
    'session_first_workflow', 
    'clean_state_workflow',
]