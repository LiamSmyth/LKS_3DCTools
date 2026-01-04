"""
Volume Proxy Utilities - Proxy mode operations on Volumes.

Low-level primitives with RAW ARGUMENTS ONLY (no dataclasses).
Proxy mode is 3DCoat's decimation cache for faster viewport performance.

Supports multiple proxy levels:
- Decimate: 16X, 8X, 4X, 2X (destructive decimation-based)
- Reduce: 8X, 4X, 2X (non-destructive reduction)
"""
import coat
from enum import Enum

from utils.coat_ui_utils import wait_frames

# =============================================================================
# MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
# =============================================================================

# Decimate-based proxy commands (destructive)
CMD_DECIMATE_16X: str = "$Decimate16X"
CMD_DECIMATE_8X: str = "$Decimate8X"
CMD_DECIMATE_4X: str = "$Decimate4X"
CMD_DECIMATE_2X: str = "$Decimate2X"

# Reduce-based proxy commands (non-destructive)
CMD_REDUCE_8X: str = "$Reduce8X"
CMD_REDUCE_4X: str = "$Reduce4X"
CMD_REDUCE_2X: str = "$Reduce2X"

# =============================================================================
# ENUMS
# =============================================================================


class ProxyType(Enum):
    """Available proxy modes in 3DCoat."""
    # Decimate-based (destructive)
    DECIMATE_16X = CMD_DECIMATE_16X
    DECIMATE_8X = CMD_DECIMATE_8X
    DECIMATE_4X = CMD_DECIMATE_4X
    DECIMATE_2X = CMD_DECIMATE_2X
    # Reduce-based (non-destructive)
    REDUCE_8X = CMD_REDUCE_8X
    REDUCE_4X = CMD_REDUCE_4X
    REDUCE_2X = CMD_REDUCE_2X


# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_PROXY_TYPE: ProxyType = ProxyType.DECIMATE_16X
MESH_OP_WAIT_FRAMES: int = 2


# =============================================================================
# EXECUTE FUNCTIONS (raw args)
# =============================================================================

def toggle_proxy(proxy_type: ProxyType = DEFAULT_PROXY_TYPE) -> None:
    """
    Toggle proxy mode on current Volume.

    Args:
        proxy_type: The type of proxy to toggle (default: DECIMATE_16X)

    This is a viewport optimization that shows a decimated/reduced version
    for faster editing, while preserving the full-resolution mesh.
    """
    coat.ui.cmd(proxy_type.value)
    wait_frames(MESH_OP_WAIT_FRAMES)


# =============================================================================
# CONVENIENCE FUNCTIONS (thin wrappers)
# =============================================================================

def toggle_decimate_16x() -> None:
    """Toggle 16X decimate proxy on current Volume."""
    toggle_proxy(ProxyType.DECIMATE_16X)


def toggle_decimate_8x() -> None:
    """Toggle 8X decimate proxy on current Volume."""
    toggle_proxy(ProxyType.DECIMATE_8X)


def toggle_decimate_4x() -> None:
    """Toggle 4X decimate proxy on current Volume."""
    toggle_proxy(ProxyType.DECIMATE_4X)


def toggle_decimate_2x() -> None:
    """Toggle 2X decimate proxy on current Volume."""
    toggle_proxy(ProxyType.DECIMATE_2X)


def toggle_reduce_8x() -> None:
    """Toggle 8X reduce proxy on current Volume."""
    toggle_proxy(ProxyType.REDUCE_8X)


def toggle_reduce_4x() -> None:
    """Toggle 4X reduce proxy on current Volume."""
    toggle_proxy(ProxyType.REDUCE_4X)


def toggle_reduce_2x() -> None:
    """Toggle 2X reduce proxy on current Volume."""
    toggle_proxy(ProxyType.REDUCE_2X)
