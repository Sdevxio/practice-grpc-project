# Tapper Service Integration Tests

This directory contains integration tests that interact with real tapper hardware devices. These tests validate the complete system functionality including protocol communication, timing operations, and dual card operations.

## Test Categories

### 🔧 **System & Protocol Tests**
- `test_dual_protocol_system.py` - Complete pytest suite with dual protocol fallback
- `test_protocol_examples.py` - Protocol usage examples and integration patterns
- `test_tapper_system.py` - Core tapper system functionality

### ⏱️ **Timing & Operation Tests**
- `test_timed_operations.py` - Basic timed operations (extend/retract for time)
- `test_adaptive_timing.py` - Adaptive timing with drift compensation
- `test_custom_timing.py` - Custom timing configurations
- `test_smart_tuning.py` - Smart timing tuning algorithms with microsecond precision

### 🃏 **Card Operation Tests**
- `test_simple_card2.py` - Simple Card 2 operations
- `test_card2_only.py` - Card 2 focused testing
- `dual_card_test_example.py` - Dual card operation examples
- `test_tap_sequence.py` - Complex tap sequences

### 🛠️ **Utility & Infrastructure Tests**
- `test_endpoints.py` - Endpoint validation and URL building
- `live_calibration_monitor.py` - Live calibration monitoring tools

## Hardware Requirements

These tests require:
- **ESP32 tapper device** connected and accessible via network
- **Dual card setup** with Card 1 and Card 2 positioned correctly
- **Network connectivity** for HTTP/MQTT protocols
- **12V or USB power** for the linear actuator

## Running Integration Tests

### Basic Usage
```bash
# Run all integration tests
pytest tappers_service/tests/integration/ -v

# Run with output capture disabled (see print statements)
pytest tappers_service/tests/integration/ -v -s

# Run specific test category
pytest tappers_service/tests/integration/ -v -m "timing"
pytest tappers_service/tests/integration/ -v -m "card2"
pytest tappers_service/tests/integration/ -v -m "protocol"
```

### Hardware Control
```bash
# Skip hardware tests (useful for CI/CD)
pytest tappers_service/tests/integration/ --skip-hardware

# Use specific station configuration
pytest tappers_service/tests/integration/ --station=station2
```

### Advanced Usage
```bash
# Run only fast tests
pytest tappers_service/tests/integration/ -v -m "not slow"

# Run specific test file
pytest tappers_service/tests/integration/test_dual_protocol_system.py -v

# Run with detailed logging
pytest tappers_service/tests/integration/ -v -s --log-level=DEBUG
```

## Test Markers

Integration tests use the following markers:

- `@pytest.mark.hardware` - Requires real hardware (auto-applied to all integration tests)
- `@pytest.mark.timing` - Tests timing-related functionality
- `@pytest.mark.protocol` - Tests protocol behavior and fallback
- `@pytest.mark.slow` - Tests that take significant time (>10 seconds)
- `@pytest.mark.card1` - Tests specific to Card 1 operations
- `@pytest.mark.card2` - Tests specific to Card 2 operations  
- `@pytest.mark.dual_card` - Tests using both cards

## Fixtures Available

### Connection Fixtures
- `tapper_service` (session-scoped) - Shared service for entire test session
- `tapper` (function-scoped) - Fresh service connection per test
- `protocol` - Direct protocol access from tapper service

### Utility Fixtures  
- `skip_if_no_hardware` - Explicit hardware dependency check
- `station_id` - Station ID from command line (default: station1)
- `reset_hardware_state` (auto-use) - Resets tapper to middle position before each test

## Test Structure

```
tappers_service/tests/integration/
├── README.md                          # This file
├── conftest.py                        # Shared fixtures and configuration
├── __init__.py                        # Package marker
│
├── test_dual_protocol_system.py       # ✅ Complete pytest suite (10 tests)
├── test_protocol_examples.py          # 🔧 Protocol usage examples
├── test_tapper_system.py             # 🔧 Core system tests
│
├── test_timed_operations.py          # ⏱️ Basic timing tests
├── test_adaptive_timing.py           # ⏱️ Drift compensation
├── test_custom_timing.py             # ⏱️ Custom configurations  
├── test_smart_tuning.py              # ⏱️ Smart tuning algorithms
│
├── test_simple_card2.py              # 🃏 Simple Card 2 tests
├── test_card2_only.py                # 🃏 Card 2 focused tests
├── dual_card_test_example.py         # 🃏 Dual card examples
├── test_tap_sequence.py              # 🃏 Complex sequences
│
├── test_endpoints.py                 # 🛠️ Endpoint validation
└── live_calibration_monitor.py       # 🛠️ Live monitoring tools
```

## Expected Test Results

When hardware is connected and working:
- ✅ **All tests should pass** with real hardware operations
- 🔄 **Protocol fallback** should work (MQTT fails → HTTP succeeds)
- 🎯 **Timing accuracy** should be within acceptable ranges
- 📊 **Status reporting** should show middle position after operations

When hardware is not available:
- ⏭️ **Tests are skipped** with appropriate skip messages
- 🚫 **No failures** due to missing hardware
- 📝 **Clear messaging** about hardware requirements

## Troubleshooting

### Common Issues

**Connection Failures:**
```
pytest.skip("No tapper hardware available")
```
- Check ESP32 device is powered and connected to network
- Verify station configuration in `station_definitions.yaml`
- Test direct HTTP access: `curl http://192.168.1.100/status`

**Timing Issues:**
```
AssertionError: Device not at expected position
```
- Check power source (USB vs 12V affects timing)
- Verify timing configuration in station YAML
- Run calibration sequence to measure actual timings
- **NEW**: Firmware now uses microsecond precision (1000x improvement)
- **NEW**: Automatic drift compensation reduces cumulative positioning errors

**Protocol Issues:**
```
TapperConnectionError: Cannot connect via any protocol
```
- Check both HTTP and MQTT connectivity
- Verify firewall settings
- Test individual protocols separately

### Debug Mode

For detailed debugging:
```bash
# Enable debug logging
pytest tappers_service/tests/integration/ -v -s --log-level=DEBUG

# Run single test with maximum verbosity
pytest tappers_service/tests/integration/test_dual_protocol_system.py::test_dual_card_operations -vvv -s
```

## Contributing

When adding new integration tests:

1. **Use appropriate markers** for categorization
2. **Include hardware checks** using fixtures
3. **Reset hardware state** between tests (auto-handled)
4. **Document test purpose** clearly in docstrings
5. **Handle missing hardware** gracefully with skips
6. **Follow naming convention** `test_*.py`

## Architecture Integration

These integration tests validate:

- 🏗️ **Clean Architecture**: Service → Protocol → Device layering
- 🔄 **Protocol Fallback**: HTTP → MQTT automatic failover  
- ⚡ **Modern Timing**: Python-controlled vs firmware timing
- 🎯 **Dual Card System**: Independent Card 1/Card 2 operations
- 📊 **Utility Integration**: Timing, endpoints, exceptions modules
- 🧪 **Test Framework**: Pytest fixtures, markers, and configuration

The integration tests serve as both validation and living documentation of the complete tapper system functionality.