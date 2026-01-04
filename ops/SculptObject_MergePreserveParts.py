"""
SculptObject_MergePreserveParts Operator

Merge subtree while preserving parts in surface mode.

Converts all objects to surface mode (collapsing boolean trees),
then merges them together while preserving their separate part identities.

Uses scope resolution to determine merge root.
"""
import coat
from utils.scene_api import SceneAPI
from utils.scope_utils import Scope, resolve_scope
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.TREE,
    preserve_selection: bool = True,
) -> int:
    """
    Merge subtree while preserving parts.

    Args:
        scope: Which objects to merge (typically TREE)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects merged
    """
    from utils.scene_api import SelectionAPI

    # Get the root element for merging
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

    # Convert root element to surface (collapse boolean tree)
    vol: coat.Volume = current.Volume()
    if not vol.isSurface():
        vol.collapseBollTree()
        vol.toSurface()

    # Get subtree and convert all to surface
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(current)
    count: int = 0

    for el in subtree:
        if el.isSculptObject():
            _prepare_for_merge(el)
            count += 1

    # Merge the subtree
    current.selectOne()
    current.mergeSubtree()

    # Restore selection
    if preserve_selection and saved_selection:
        SelectionAPI.restore_selection(saved_selection)

    show_message(f"Merged {count} objects preserving parts", 2000)
    return count


def _prepare_for_merge(element: coat.SceneElement) -> None:
    """
    Prepare a single element for merge by converting to surface.

    Args:
        element: The element to prepare
    """
    vol: coat.Volume = element.Volume()
    if not vol.isSurface():
        vol.collapseBollTree()
        vol.toSurface()
