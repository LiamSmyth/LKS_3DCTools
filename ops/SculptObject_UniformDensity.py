"""
SculptObject_UniformDensity Operator

Match polygon density across sculpt objects using a reference.

Uses the selected element as the reference density and
resamples other elements to match that density.

Scopes:
- TREE: Match density of all children to the selected root element
- ALL: Match density of ALL sculpt objects to the selected element

Two modes:
- RESAMPLE: Standard resampling to match density
- SMART: Smart matching with tolerance to avoid unnecessary changes
"""
import coat
from enum import Enum
from utils.scene_api import SceneAPI
from utils.scope_utils import Scope, resolve_scope
from utils.Volume_density_utils import (
    resample_to_match_density,
    smart_match_density
)
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# ENUMS
# =============================================================================

class DensityMode(Enum):
    """Density matching mode."""
    RESAMPLE = "resample"  # Standard resampling
    SMART = "smart"        # Smart matching with tolerance


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.TREE,
    mode: DensityMode = DensityMode.SMART,
    tolerance: float = 0.1,
    preserve_selection: bool = True,
) -> int:
    """
    Match density of elements to the selected reference.

    Args:
        scope: TREE = children only, ALL = all sculpt objects
        mode: Density matching mode (RESAMPLE or SMART)
        tolerance: Tolerance for smart matching (fraction, e.g., 0.1 = 10%)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects processed
    """
    from utils.scene_api import SelectionAPI

    # Get the reference element (selected)
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_error("No object selected", 2000)
        return 0

    if not current.isSculptObject():
        show_error("Selected element is not a sculpt object", 2000)
        return 0

    # Save selection
    saved_selection: list[coat.SceneElement] = []
    if preserve_selection:
        saved_selection = SelectionAPI.save_selection()

    # Get reference volume
    ref_vol: coat.Volume = current.Volume()

    # Get elements to process based on scope
    if scope == Scope.ALL:
        # All sculpt objects
        elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()
    else:
        # Subtree of selected element
        elements = SceneAPI.collect_subtree(current)

    count: int = 0
    for el in elements:
        # Skip reference element and non-sculpt objects
        if el == current or not el.isSculptObject():
            continue

        if mode == DensityMode.SMART:
            smart_match_density(el, ref_vol, tolerance)
        else:
            resample_to_match_density(el, ref_vol)
        count += 1

    # Restore selection
    if preserve_selection and saved_selection:
        SelectionAPI.restore_selection(saved_selection)

    scope_str: str = "all" if scope == Scope.ALL else "subtree"
    mode_str: str = "smart matched" if mode == DensityMode.SMART else "resampled"
    show_message(f"Density {mode_str} {count} {scope_str} objects", 2000)
    return count


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def resample_tree() -> int:
    """Resample subtree to match root density."""
    return main(scope=Scope.TREE, mode=DensityMode.RESAMPLE)


def smart_match_tree(tolerance: float = 0.1) -> int:
    """Smart match subtree density with tolerance."""
    return main(scope=Scope.TREE, mode=DensityMode.SMART, tolerance=tolerance)


def resample_all() -> int:
    """Resample all sculpt objects to match selected density."""
    return main(scope=Scope.ALL, mode=DensityMode.RESAMPLE)


def smart_match_all(tolerance: float = 0.1) -> int:
    """Smart match all objects to selected density."""
    return main(scope=Scope.ALL, mode=DensityMode.SMART, tolerance=tolerance)
