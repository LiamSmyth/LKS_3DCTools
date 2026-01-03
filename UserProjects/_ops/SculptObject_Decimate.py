"""
SculptObject_Decimate Operator

Decimate sculpt objects to reduce polygon count.
Supports: percentage reduction, target polycount, and 16x quick proxy.

Uses scope resolution to determine which elements to operate on.
"""
import coat
from dataclasses import dataclass
from _utils.scene_api import SceneAPI
from _utils.scope_utils import Scope, resolve_scope
from _utils.mesh_utils import (
    DecimateParams,
    execute_decimate,
    decimate_16x,
    ensure_surface_mode,
    cleanup_after_mesh_operation,
)
from _utils.coat_ui_utils import show_message, show_error


# =============================================================================
# CONFIGURATION DEFAULTS
# =============================================================================

DEFAULT_REDUCTION_PERCENT: float = 50.0


# =============================================================================
# CONFIG DATACLASS
# =============================================================================

@dataclass
class DecimateConfig:
    """Configuration for decimate operation."""
    reduction_percent: float | None = DEFAULT_REDUCTION_PERCENT
    target_polycount: int | None = None
    use_16x: bool = False  # Quick 16x proxy mode


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _decimate_element(
    element: coat.SceneElement,
    config: DecimateConfig
) -> bool:
    """
    Decimate a single element.

    Returns:
        True if element was decimated, False if skipped
    """
    if not element.isSculptObject():
        return False

    vol: coat.Volume = element.Volume()
    ensure_surface_mode(vol)

    # Select element for operation
    element.selectOne()

    if config.use_16x:
        decimate_16x()
    else:
        params = DecimateParams(
            reduction_percent=config.reduction_percent,
            target_polycount=config.target_polycount,
        )
        execute_decimate(params)

    return True


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    reduction_percent: float | None = DEFAULT_REDUCTION_PERCENT,
    target_polycount: int | None = None,
    use_16x: bool = False,
    preserve_selection: bool = True,
) -> int:
    """
    Decimate objects to reduce polygon count.

    Args:
        scope: Which objects to decimate
        reduction_percent: Percentage of polygons to remove (e.g., 50.0 = half)
        target_polycount: Absolute target polycount (overrides percent if set)
        use_16x: Use quick 16x decimation proxy mode
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects decimated
    """
    # Save selection for restoration
    current: coat.SceneElement | None = None
    if preserve_selection:
        current = SceneAPI.get_current_element()

    # Validate for scope-dependent operations
    if scope in (Scope.CURRENT, Scope.TREE) and not current:
        show_error("No object selected", 2000)
        return 0

    # Build config
    config = DecimateConfig(
        reduction_percent=reduction_percent,
        target_polycount=target_polycount,
        use_16x=use_16x,
    )

    # Resolve which elements to operate on
    elements: list[coat.SceneElement] = resolve_scope(scope)

    if not elements:
        show_error("No objects to process", 2000)
        return 0

    # Decimate each element
    count: int = 0
    for el in elements:
        if _decimate_element(el, config):
            count += 1

    # Cleanup after mesh operations
    cleanup_after_mesh_operation()

    # Restore selection
    if preserve_selection and current:
        current.selectOne()

    # Build status message
    if use_16x:
        status: str = f"16x decimated {count}"
    elif target_polycount is not None:
        status = f"Decimated {count} to {target_polycount:,}"
    else:
        status = f"Decimated {count} by {reduction_percent:.0f}%"

    show_message(f"{status} objects", 2000)
    return count
