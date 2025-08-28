from typing import Optional, Any
from abc import ABC, abstractmethod

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class BaseServiceClient(ABC):
    """
    Abstract base class for all gRPC service clients.
    
    Provides common functionality for:
    - Client initialization with consistent naming and logging
    - Connection management via GrpcClientManager
    - Stub creation with proper error handling
    
    Subclasses must implement:
    - stub_class: The gRPC stub class to instantiate
    - service_name: Human-readable service name for logging
    """
    
    @property
    @abstractmethod
    def stub_class(self) -> type:
        """Return the gRPC stub class for this service."""
        pass
    
    @property
    @abstractmethod 
    def service_name(self) -> str:
        """Return human-readable service name for logging."""
        pass
    
    def __init__(self, client_name: str, default_client_name: str, logger: Optional[object] = None):
        """
        Initialize the service client.
        
        Args:
            client_name: Name of the gRPC client in GrpcClientManager
            default_client_name: Default client name if none provided
            logger: Custom logger instance. If None, creates default logger
        """
        self.client_name = client_name or default_client_name
        self.logger = logger or get_logger(f"{self.__class__.__name__}[{self.client_name}]")
        self.stub: Optional[Any] = None
    
    def connect(self) -> None:
        """
        Establish the gRPC connection and create service stub.
        
        Uses GrpcClientManager to get the appropriate stub instance
        for the configured client name.
        """
        self.logger.debug(f"Connecting to {self.service_name} via client '{self.client_name}'")
        self.stub = GrpcClientManager.get_stub(self.client_name, self.stub_class)
        self.logger.debug(f"Successfully connected to {self.service_name}")
    
    def is_connected(self) -> bool:
        """
        Check if the client has an active stub connection.
        
        Returns:
            True if stub is available, False otherwise
        """
        return self.stub is not None
    
    def ensure_connected(self) -> None:
        """
        Ensure the client is connected, connecting if necessary.
        
        Raises:
            RuntimeError: If connection cannot be established
        """
        if not self.is_connected():
            try:
                self.connect()
            except Exception as e:
                self.logger.error(f"Failed to connect to {self.service_name}: {e}")
                raise RuntimeError(f"Cannot connect to {self.service_name}: {e}")