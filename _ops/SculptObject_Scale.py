"""
SculptObject_Scale Operator

Scale sculpt objects by a multiplier factor.
Uses scope resolution to determine which elements to operate on.
"""
import coat
from _utils.scene_api import SceneAPI
from _utils.scope_utils import Scope, resolve_scope
from _utils.object_utils import scale_element
from _utils.coat_ui_utils import show_message, show_error


# =============================================================================
# CONFIGURATION DEFAULTS
# =============================================================================

DEFAULT_SCALE_FACTOR: float = 1.0


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    scale_factor: float = DEFAULT_SCALE_FACTOR,
    preserve_selection: bool = True,
) -> int:
    """
    Scale objects by a multiplier factor.

    Args:
        scope: Which objects to scale
        scale_factor: Multiplier (e.g., 0.01 = 1/100, 100.0 = 100x)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects scaled
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

    # Scale each element
    count: int = 0
    for el in elements:
        if el.isSculptObject():
            scale_element(el, scale_factor)
            count += 1

    # Restore selection
    if preserve_selection and current:
        current.selectOne()

    # Build status message
    if scale_factor < 1.0:
        factor_str: str = f"1/{int(1.0 / scale_factor)}"
    else:
        factor_str = f"{int(scale_factor)}x"

    show_message(f"Scaled {count} objects by {factor_str}", 2000)
    return count
