#!/usr/bin/env python3
"""
Test script for Server SDK integration.

This script tests the automatic Python 3.6 environment setup and
SDK proxy functionality.
"""

def test_sdk_integration():
    """Test the server SDK integration."""
    print("Testing Server SDK Integration...")
    print("=" * 50)
    
    try:
        # Import the SDK - this should trigger automatic setup
        print("1. Importing SDK...")
        from sdk import server_sdk
        print("   ✓ SDK imported successfully")
        
        # Test environment connection
        print("\n2. Testing environment connection...")
        test_result = server_sdk.test_connection()
        
        if "error" in test_result:
            print(f"   ✗ Environment test failed: {test_result['error']}")
            return False
        else:
            print(f"   ✓ Python version: {test_result.get('python_version', 'Unknown')}")
            print(f"   ✓ Python executable: {test_result.get('python_executable', 'Unknown')}")
            print(f"   ✓ SDK available: {test_result.get('sdk_available', False)}")
        
        # Test method call (this will likely fail until actual SDK is installed)
        print("\n3. Testing method proxy...")
        try:
            # This is just an example - replace with actual SDK methods
            result = server_sdk.some_example_method("test_param")
            print(f"   ✓ Method call successful: {result}")
        except Exception as e:
            print(f"   ⚠ Method call failed (expected until real SDK installed): {e}")
        
        print("\n" + "=" * 50)
        print("SDK Integration Test Complete!")
        return True
        
    except Exception as e:
        print(f"\n✗ SDK integration test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_sdk_integration()
    exit(0 if success else 1)