#!/usr/bin/env python3
"""
Integration Test Runner for Tapper Service

This script provides a convenient way to run integration tests with various
options and configurations. It includes hardware detection, test categorization,
and detailed reporting.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('/Users/admin/Tapper_Project')

def check_hardware_available():
    """Check if tapper hardware is available for testing."""
    try:
        from tappers_service.tapper_system import TapperService
        service = TapperService("station1")
        available = service.connect()
        if available:
            service.disconnect()
        return available
    except Exception as e:
        print(f"Hardware check failed: {e}")
        return False

def run_pytest(args_list):
    """Run pytest with given arguments."""
    cmd = ['python', '-m', 'pytest'] + args_list
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tapper service integration tests")
    
    # Test selection
    parser.add_argument('--all', action='store_true', help='Run all integration tests')
    parser.add_argument('--timing', action='store_true', help='Run timing-related tests')
    parser.add_argument('--protocol', action='store_true', help='Run protocol tests')
    parser.add_argument('--cards', action='store_true', help='Run card operation tests')
    parser.add_argument('--system', action='store_true', help='Run system tests')
    parser.add_argument('--utils', action='store_true', help='Run utility tests')
    parser.add_argument('--fast', action='store_true', help='Run only fast tests (skip slow)')
    parser.add_argument('--file', type=str, help='Run specific test file')
    parser.add_argument('--test', type=str, help='Run specific test function')
    
    # Hardware options
    parser.add_argument('--skip-hardware', action='store_true', help='Skip hardware tests')
    parser.add_argument('--station', type=str, default='station1', help='Station ID to use')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='count', default=1, help='Increase verbosity')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    parser.add_argument('--no-capture', '-s', action='store_true', help='Disable output capture')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Reporting options
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--junit', type=str, help='Generate JUnit XML report')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    
    args = parser.parse_args()
    
    # Check hardware availability
    if not args.skip_hardware:
        print("🔧 Checking hardware availability...")
        hardware_available = check_hardware_available()
        
        if hardware_available:
            print("✅ Tapper hardware detected and accessible")
        else:
            print("❌ No tapper hardware detected")
            response = input("Continue with --skip-hardware? (y/N): ")
            if response.lower() != 'y':
                print("Exiting. Use --skip-hardware to run without hardware.")
                return 1
            args.skip_hardware = True
    
    # Build pytest arguments
    pytest_args = []
    
    # Test selection
    if args.file:
        pytest_args.append(args.file)
    elif args.test:
        pytest_args.append(f"-k {args.test}")
    elif args.timing:
        pytest_args.extend(['-m', 'timing'])
    elif args.protocol:
        pytest_args.extend(['-m', 'protocol'])
    elif args.cards:
        pytest_args.extend(['-m', 'card1 or card2 or dual_card'])
    elif args.system:
        pytest_args.append('test_dual_protocol_system.py')
        pytest_args.append('test_tapper_system.py')
    elif args.utils:
        pytest_args.append('test_endpoints.py')
    elif args.fast:
        pytest_args.extend(['-m', 'not slow'])
    elif not args.all:
        # Default: run core system tests
        pytest_args.append('test_dual_protocol_system.py')
    
    # Hardware options
    if args.skip_hardware:
        pytest_args.append('--skip-hardware')
    if args.station != 'station1':
        pytest_args.extend(['--station', args.station])
    
    # Output options
    if args.quiet:
        pytest_args.append('-q')
    else:
        pytest_args.extend(['-v'] * args.verbose)
    
    if args.no_capture:
        pytest_args.append('-s')
    
    if args.debug:
        pytest_args.extend(['--log-level=DEBUG', '-s'])
    
    # Reporting options
    if args.html:
        pytest_args.extend(['--html=reports/integration_report.html', '--self-contained-html'])
    
    if args.junit:
        pytest_args.extend(['--junit-xml', args.junit])
    
    if args.coverage:
        pytest_args.extend(['--cov=tappers_service', '--cov-report=html', '--cov-report=term'])
    
    # Run tests
    print(f"🚀 Starting integration tests...")
    if args.skip_hardware:
        print("⚠️  Hardware tests will be skipped")
    
    return run_pytest(pytest_args)

if __name__ == '__main__':
    exit_code = main()
    
    if exit_code == 0:
        print("\n✅ All tests completed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code)