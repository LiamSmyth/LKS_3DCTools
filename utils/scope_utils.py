"""
Scope Utilities

Provides a unified scope model for batch operations:
- CURRENT: Selected sculpt object(s) only
- TREE: Selection + all children recursively  
- OTHER: Everything EXCEPT selection subtree
- ALL: Entire sculpt tree

Design Principles:
- Use SceneAPI for all context fetching
- Pure functions that take elements as arguments
- Selection preservation is handled at the caller level
"""
import coat
from typing import Callable
from enum import Enum

from utils.scene_api import SceneAPI, SelectionAPI, deduplicate_elements


class Scope(Enum):
    """Operation scope enumeration."""
    CURRENT: str = "current"  # Selected object(s) only
    TREE: str = "tree"        # Selection + children
    OTHER: str = "other"      # Everything except selection subtree
    ALL: str = "all"          # Entire sculpt tree


# =============================================================================
# SCOPE RESOLUTION - Convert scope enum to element lists
# =============================================================================

def resolve_scope(
    scope: Scope,
    selected: list[coat.SceneElement] | None = None,
    include_hidden: bool = False
) -> list[coat.SceneElement]:
    """
    Resolve a scope enum to a list of elements.

    Args:
        scope: The operation scope
        selected: Optional pre-fetched selection (avoids re-fetching)
        include_hidden: If True, include hidden elements (for visibility ops)

    Returns:
        List of elements matching the scope
    """
    # Fetch selection if not provided
    if selected is None:
        selected = SceneAPI.get_selected_elements()

    root: coat.SceneElement | None = SceneAPI.get_sculpt_root()

    if scope == Scope.CURRENT:
        return list(selected)

    elif scope == Scope.TREE:
        return _resolve_tree_scope(selected, include_hidden)

    elif scope == Scope.OTHER:
        return _resolve_other_scope(selected, root, include_hidden)

    elif scope == Scope.ALL:
        return _resolve_all_scope(root, include_hidden)

    return []


def _resolve_tree_scope(
    selected: list[coat.SceneElement],
    include_hidden: bool = False
) -> list[coat.SceneElement]:
    """
    Resolve TREE scope: selection + all descendants.

    Args:
        selected: Currently selected elements
        include_hidden: If True, include hidden elements

    Returns:
        Selected elements plus all their descendants
    """
    tree_elements: list[coat.SceneElement] = []
    for sel in selected:
        if include_hidden:
            tree_elements.extend(SceneAPI.collect_all_subtree(sel))
        else:
            tree_elements.extend(SceneAPI.collect_subtree(sel))
    return deduplicate_elements(tree_elements)


def _resolve_other_scope(
    selected: list[coat.SceneElement],
    root: coat.SceneElement | None,
    include_hidden: bool = False
) -> list[coat.SceneElement]:
    """
    Resolve OTHER scope: everything except selection subtrees.

    Args:
        selected: Currently selected elements
        root: Scene root element
        include_hidden: If True, include hidden elements

    Returns:
        All elements not in any selection subtree
    """
    if not root:
        return []

    # Build set of IDs in selection trees
    tree_ids: set[int] = set()
    for sel in selected:
        subtree = SceneAPI.collect_all_subtree(
            sel) if include_hidden else SceneAPI.collect_subtree(sel)
        for el in subtree:
            tree_ids.add(id(el))

    # Collect all elements NOT in selection trees
    all_elements: list[coat.SceneElement] = (
        SceneAPI.collect_all_subtree(
            root) if include_hidden else SceneAPI.collect_subtree(root)
    )
    return [el for el in all_elements if id(el) not in tree_ids]


def _resolve_all_scope(
    root: coat.SceneElement | None,
    include_hidden: bool = False
) -> list[coat.SceneElement]:
    """
    Resolve ALL scope: entire sculpt tree.

    Args:
        root: Scene root element
        include_hidden: If True, include hidden elements

    Returns:
        All elements in the scene
    """
    if not root:
        return []
    if include_hidden:
        return SceneAPI.collect_all_subtree(root)
    return SceneAPI.collect_subtree(root)


# =============================================================================
# SCOPED OPERATIONS - Apply operations to scoped elements
# =============================================================================

def apply_to_scope(
    scope: Scope,
    operation: Callable[[coat.SceneElement], None],
    preserve_selection: bool = True
) -> int:
    """
    Apply an operation to all elements matching the scope.

    Args:
        scope: The operation scope
        operation: Function to apply to each element
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of elements processed
    """
    # Cache selection for restoration
    original_selection: list[coat.SceneElement] = []
    if preserve_selection:
        original_selection = SelectionAPI.save_selection()

    # Resolve scope to elements
    elements: list[coat.SceneElement] = resolve_scope(
        scope, original_selection)

    # Apply operation
    count: int = 0
    for el in elements:
        operation(el)
        count += 1

    # Restore selection
    if preserve_selection and original_selection:
        SelectionAPI.restore_selection(original_selection)

    return count


# =============================================================================
# DEPRECATED - Kept for backwards compatibility
# Use scene_api.py and SceneElement_visibility_utils.py for new code
# =============================================================================

def get_selected_elements() -> list[coat.SceneElement]:
    """DEPRECATED: Use SceneAPI.get_selected_elements() instead."""
    return SceneAPI.get_selected_elements()


def restore_selection(elements: list[coat.SceneElement]) -> None:
    """DEPRECATED: Use SelectionAPI.restore_selection() instead."""
    SelectionAPI.restore_selection(elements)


def get_elements_by_scope(scope: Scope) -> list[coat.SceneElement]:
    """DEPRECATED: Use resolve_scope() instead."""
    return resolve_scope(scope)


def collect_tree_elements(root: coat.SceneElement) -> list[coat.SceneElement]:
    """DEPRECATED: Use SceneAPI.collect_subtree() instead."""
    return SceneAPI.collect_subtree(root)
