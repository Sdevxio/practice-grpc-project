"""
Tapper commands modules.

This package contains both modern and legacy tapper operation sequences:

- dual_sequences: Modern timed operations for dual card system (recommended)
- legacy_sequences: Legacy single-card operations for backward compatibility

Usage:
    # Modern approach (recommended)
    from tappers_service.tapper_system.commands import dual_sequences
    dual_sequences.tap_card2_timed(protocol)
    
    # Legacy approach (for backward compatibility)
    from tappers_service.tapper_system.commands import legacy_sequences
    legacy_sequences.simple_tap(protocol)  # Original function names preserved
"""

# Import both modules for easy access
from . import dual_tap_sequences as dual_sequences
from . import single_tap_sequences as legacy_sequences

__all__ = ['dual_sequences', 'legacy_sequences']