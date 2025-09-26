#!/usr/bin/env python3
"""
Server SDK Integration - Automatic Python 3.6 environment with legacy server SDK proxy.

This module provides seamless integration with external server SDKs that require Python 3.6.
It automatically creates and manages a separate Python 3.6 virtual environment and proxies
method calls to the legacy SDK through subprocess execution.

Features:
- Automatic Python 3.6 virtual environment creation
- Lazy initialization on first import
- Method proxying through subprocess calls
- JSON-based result serialization
- Error handling and propagation

Usage:
    from sdk import server_sdk
    
    # Methods are automatically proxied to Python 3.6 environment
    result = server_sdk.some_method(param1, param2)
    data = server_sdk.another_method(key="value")
"""

import subprocess
import os
import json
import sys
from typing import Any, Dict


class ServerSDK:
    """
    Proxy class for external server SDK requiring Python 3.6.
    
    Automatically creates and manages a Python 3.6 virtual environment,
    installs the required server SDK, and proxies method calls through
    subprocess execution.
    """
    
    def __init__(self):
        """Initialize ServerSDK with automatic environment setup."""
        self.sdk_dir = os.path.dirname(__file__)
        self.venv_path = os.path.join(self.sdk_dir, '.venv36')
        
        # Determine Python executable path based on platform
        if sys.platform == "win32":
            self.py36_path = os.path.join(self.venv_path, 'Scripts', 'python.exe')
            self.pip_exe = os.path.join(self.venv_path, 'Scripts', 'pip.exe')
        else:
            self.py36_path = os.path.join(self.venv_path, 'bin', 'python')
            self.pip_exe = os.path.join(self.venv_path, 'bin', 'pip')
        
        # Auto-setup environment on first import
        self._ensure_sdk_environment()
    
    def _ensure_sdk_environment(self):
        """Create Python 3.6 venv and install SDK if not exists."""
        if not os.path.exists(self.venv_path):
            print("Setting up SDK environment...")
            try:
                # Try different Python 3.6 executable names
                python36_candidates = ['python3.6', 'python36', 'python3']
                python36_exe = None
                
                for candidate in python36_candidates:
                    try:
                        result = subprocess.run([candidate, '--version'], 
                                              capture_output=True, text=True)
                        if result.returncode == 0 and '3.6' in result.stdout:
                            python36_exe = candidate
                            break
                    except FileNotFoundError:
                        continue
                
                if not python36_exe:
                    raise Exception("Python 3.6 not found. Please install Python 3.6.")
                
                print(f"Using Python 3.6: {python36_exe}")
                
                # Create virtual environment
                subprocess.run([python36_exe, '-m', 'venv', self.venv_path], check=True)
                
                # Upgrade pip in the virtual environment
                subprocess.run([self.pip_exe, 'install', '--upgrade', 'pip'], check=True)
                
                # Install server SDK using your pip.ini config
                # Note: Replace 'server_sdk' with the actual package name
                subprocess.run([self.pip_exe, 'install', 'server_sdk'], check=True)
                
                print("SDK environment ready!")
                
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to setup SDK environment: {e}")
            except Exception as e:
                raise Exception(f"Environment setup error: {e}")
    
    def _execute_sdk_method(self, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method on the server SDK in the Python 3.6 environment.
        
        Args:
            method_name: Name of the method to call on the SDK
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method
            
        Returns:
            Result from the SDK method call
            
        Raises:
            Exception: If the SDK call fails or returns an error
        """
        script = f'''
import sys
import json
try:
    # Import your actual server SDK here
    # Replace 'YourSDKClass' with the actual class name
    from server_sdk import YourSDKClass
    
    sdk = YourSDKClass()
    result = getattr(sdk, "{method_name}")(*{repr(args)}, **{repr(kwargs)})
    
    # Convert result to JSON-serializable format
    if hasattr(result, '__dict__'):
        result_data = result.__dict__
    else:
        result_data = result
    
    print("SUCCESS:" + json.dumps({{"result": result_data}}))
    
except ImportError as e:
    print("ERROR:SDK not installed or import failed: " + str(e))
except AttributeError as e:
    print("ERROR:Method not found: " + str(e))
except Exception as e:
    print("ERROR:SDK call failed: " + str(e))
'''
        
        try:
            proc = subprocess.run([self.py36_path, '-c', script], 
                                capture_output=True, text=True, timeout=30)
            
            output = proc.stdout.strip()
            
            if output.startswith('SUCCESS:'):
                result_json = output[8:]
                return json.loads(result_json)['result']
            elif output.startswith('ERROR:'):
                raise Exception(output[6:])
            else:
                error_msg = f"SDK call failed. STDOUT: {proc.stdout}, STDERR: {proc.stderr}"
                raise Exception(error_msg)
                
        except subprocess.TimeoutExpired:
            raise Exception(f"SDK method '{method_name}' timed out after 30 seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse SDK response: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute SDK method '{method_name}': {e}")
    
    def __getattr__(self, method_name: str):
        """
        Dynamic method proxy for SDK methods.
        
        Args:
            method_name: Name of the method to proxy
            
        Returns:
            Callable that will execute the method in Python 3.6 environment
        """
        def sdk_method(*args, **kwargs):
            return self._execute_sdk_method(method_name, *args, **kwargs)
        
        return sdk_method
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the SDK environment and connection.
        
        Returns:
            Dictionary with environment information and test results
        """
        test_script = '''
import sys
import json
try:
    print("SUCCESS:" + json.dumps({
        "python_version": sys.version,
        "python_executable": sys.executable,
        "sdk_available": True
    }))
except Exception as e:
    print("ERROR:" + str(e))
'''
        
        try:
            proc = subprocess.run([self.py36_path, '-c', test_script], 
                                capture_output=True, text=True)
            
            output = proc.stdout.strip()
            if output.startswith('SUCCESS:'):
                return json.loads(output[8:])
            else:
                return {"error": proc.stderr or "Unknown error"}
                
        except Exception as e:
            return {"error": f"Test failed: {e}"}


# Create singleton instance - setup happens automatically on first import
server_sdk = ServerSDK()

# Export the singleton for easy import
__all__ = ['server_sdk', 'ServerSDK']