"""
stc_core backward compatibility shim
====================================
stc_core has been renamed to d2b_core (Design2Build Core).
This module re-exports d2b_core for backwards compatibility.
"""

import sys
import d2b_core

# Forward all attributes from d2b_core
sys.modules[__name__] = d2b_core
