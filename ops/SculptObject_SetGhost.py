"""
SculptObject_SetGhost Operator

Unified operator for all ghost-related operations on sculpt objects.
Supports: set ghost, unghost, invert, and isolate (ghost all except).

Uses scope resolution to determine which elements to operate on.
"""
import coat
from enum import Enum
from utils.scene_api import SceneAPI
from utils.scope_utils import Scope, resolve_scope
from utils.SceneElement_visibility_utils import (
    set_ghost,
    ghost_elements,
    unghost_elements,
    invert_ghost_on_elements,
    ghost_except,
)
from utils.coat_ui_utils import show_message, show_error


class GhostMode(Enum):
    """Ghost operation mode."""
    SET = "set"          # Set ghost to specific value
    INVERT = "invert"    # Invert current ghost state
    ISOLATE = "isolate"  # Ghost all except scope


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    ghost: bool = True,
    mode: GhostMode = GhostMode.SET,
    preserve_selection: bool = True,
) -> int:
    """
    Apply ghost operation to objects.

    Args:
        scope: Which objects to operate on
        ghost: For SET mode, True = ghost, False = unghost
        mode: Operation mode (SET, INVERT, ISOLATE)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects affected
    """
    # Save selection for restoration
    current: coat.SceneElement | None = None
    if preserve_selection:
        current = SceneAPI.get_current_element()

    # Validate for scope-dependent operations
    if scope in (Scope.CURRENT, Scope.TREE) and not current:
        show_error("No object selected", 2000)
        return 0

    count: int = 0

    if mode == GhostMode.ISOLATE:
        # Isolate: ghost all EXCEPT the scope elements
        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        keep_unghosted: list[coat.SceneElement] = resolve_scope(scope)
        count = ghost_except(all_elements, keep_unghosted)
        status: str = f"Isolated - ghosted {count}"

    elif mode == GhostMode.INVERT:
        # Invert: toggle ghost state on scope elements
        elements: list[coat.SceneElement] = resolve_scope(scope)
        count = invert_ghost_on_elements(elements)
        status = f"Inverted ghost on {count}"

    else:  # GhostMode.SET
        elements = resolve_scope(scope)
        count = set_ghost(elements, ghost)
        action: str = "ghosted" if ghost else "unghosted"
        status = f"{action.capitalize()} {count}"

    # Restore selection
    if preserve_selection and current:
        current.selectOne()

    show_message(f"{status} objects", 2000)
    return count
