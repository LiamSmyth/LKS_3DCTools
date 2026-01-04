"""
SculptObject_Resample Operator

Resample sculpt objects to change polygon count.
Supports: half polycount, target polycount, or ratio-based resampling.

Uses scope resolution to determine which elements to operate on.
"""
import coat
from _utils.scene_api import SceneAPI
from _utils.scope_utils import Scope, resolve_scope
from _utils.Volume_resample_utils import (
    execute_resample,
    resample_to_half,
)
from _utils.Volume_mode_utils import ensure_surface_mode
from _utils.Scene_cleanup_utils import cleanup_after_mesh_operation
from _utils.coat_ui_utils import show_message, show_error


# =============================================================================
# CONFIGURATION DEFAULTS
# =============================================================================

DEFAULT_SCALE: float = 0.5


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _resample_element(
    element: coat.SceneElement,
    target_polycount: int | None = None,
    scale: float = DEFAULT_SCALE,
    use_half: bool = False,
) -> bool:
    """
    Resample a single element.

    Returns:
        True if element was resampled, False if skipped
    """
    if not element.isSculptObject():
        return False

    vol: coat.Volume = element.Volume()
    ensure_surface_mode(vol)

    # Select element for operation
    element.selectOne()

    current_polycount: int = vol.getPolycount()
    if current_polycount <= 0:
        return False

    if use_half:
        resample_to_half(current_polycount)
    elif target_polycount is not None:
        ratio: float = target_polycount / current_polycount
        execute_resample(target_polycount=target_polycount, scale=ratio)
    else:
        # Scale-based resample
        new_target: int = int(current_polycount * scale)
        execute_resample(target_polycount=new_target, scale=scale)

    return True


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    target_polycount: int | None = None,
    scale: float = DEFAULT_SCALE,
    use_half: bool = False,
    preserve_selection: bool = True,
) -> int:
    """
    Resample objects to change polygon count.

    Args:
        scope: Which objects to resample
        target_polycount: Absolute target polycount (if set)
        scale: Scale factor for polycount (e.g., 0.5 = half)
        use_half: Quick mode to resample to half polycount
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects resampled
    """
    # Save selection for restoration
    current: coat.SceneElement | None = None
    if preserve_selection:
        current = SceneAPI.get_current_element()

    # Validate for scope-dependent operations
    if scope in (Scope.CURRENT, Scope.TREE) and not current:
        show_error("No object selected", 2000)
        return 0

    # Resolve which elements to operate on
    elements: list[coat.SceneElement] = resolve_scope(scope)

    if not elements:
        show_error("No objects to process", 2000)
        return 0

    # Resample each element
    count: int = 0
    for el in elements:
        if _resample_element(el, target_polycount, scale, use_half):
            count += 1

    # Cleanup after mesh operations
    cleanup_after_mesh_operation()

    # Restore selection
    if preserve_selection and current:
        current.selectOne()

    # Build status message
    if use_half:
        status: str = f"Resampled {count} to half"
    elif target_polycount is not None:
        status = f"Resampled {count} to {target_polycount:,}"
    else:
        status = f"Resampled {count} by {scale:.0%}"

    show_message(f"{status} objects", 2000)
    return count
