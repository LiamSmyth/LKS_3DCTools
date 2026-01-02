"""
Scene API - Thin wrappers around 3DCoat's native scene iteration.

This module provides static functions that return Python lists instead of
requiring callbacks. All context-fetching is localized here - other modules
should receive data as arguments rather than fetching their own context.

Design Principles:
- Wrap callback-based iterators into list-returning functions
- Provide typed return values for better IDE support
- Localize 3DCoat context operations here
- Pass data explicitly to downstream functions
"""
import coat
from typing import Callable


# =============================================================================
# SCENE ELEMENT COLLECTION
# =============================================================================

class SceneAPI:
    """
    Static API for 3DCoat scene operations.

    All methods are static - no instance state.
    This class wraps 3DCoat's callback-based iteration patterns
    into simple list-returning functions.
    """

    @staticmethod
    def get_sculpt_root() -> coat.SceneElement | None:
        """
        Get the sculpt tree root element.

        Returns:
            Root element, or None if no scene loaded
        """
        return coat.Scene.sculptRoot()

    @staticmethod
    def get_current_element() -> coat.SceneElement | None:
        """
        Get the currently selected/active element.

        Returns:
            Current element, or None if nothing selected
        """
        return coat.Scene.current()

    @staticmethod
    def get_current_volume() -> coat.Volume | None:
        """
        Get the volume of the currently selected element.

        Returns:
            Current volume, or None if no volume selected
        """
        current: coat.SceneElement | None = coat.Scene.current()
        if not current:
            return None
        return current.Volume()

    @staticmethod
    def get_selected_elements() -> list[coat.SceneElement]:
        """
        Get all currently selected sculpt elements as a list.

        Returns:
            List of selected SceneElement objects (may be empty)
        """
        root: coat.SceneElement | None = coat.Scene.sculptRoot()
        if not root:
            return []
        return root.collectSelected()

    @staticmethod
    def collect_subtree(root: coat.SceneElement) -> list[coat.SceneElement]:
        """
        Collect all elements in a subtree (root + all visible descendants).

        Uses iterateVisibleSubtree internally.

        Args:
            root: Root element of the subtree

        Returns:
            List containing root and all visible descendants
        """
        elements: list[coat.SceneElement] = [root]

        def collector(el: coat.SceneElement) -> bool:
            elements.append(el)
            return False  # Continue iteration

        root.iterateVisibleSubtree(collector)
        return elements

    @staticmethod
    def collect_all_subtree(root: coat.SceneElement) -> list[coat.SceneElement]:
        """
        Collect all elements in a subtree (root + ALL descendants).

        Uses iterateSubtree (not just visible).

        Args:
            root: Root element of the subtree

        Returns:
            List containing root and all descendants
        """
        elements: list[coat.SceneElement] = [root]

        def collector(el: coat.SceneElement) -> bool:
            elements.append(el)
            return False  # Continue iteration

        root.iterateSubtree(collector)
        return elements

    @staticmethod
    def collect_all_sculpt_objects() -> list[coat.SceneElement]:
        """
        Collect all sculpt objects in the entire scene.

        Returns:
            List of all sculpt objects (elements where isSculptObject() is True)
        """
        root: coat.SceneElement | None = coat.Scene.sculptRoot()
        if not root:
            return []

        objects: list[coat.SceneElement] = []

        def collector(el: coat.SceneElement) -> bool:
            if el.isSculptObject():
                objects.append(el)
            return False  # Continue iteration

        if root.isSculptObject():
            objects.append(root)
        root.iterateSubtree(collector)
        return objects

    @staticmethod
    def collect_visible_sculpt_objects() -> list[coat.SceneElement]:
        """
        Collect all visible sculpt objects in the scene.

        Returns:
            List of visible sculpt objects
        """
        root: coat.SceneElement | None = coat.Scene.sculptRoot()
        if not root:
            return []

        objects: list[coat.SceneElement] = []

        def collector(el: coat.SceneElement) -> bool:
            if el.isSculptObject():
                objects.append(el)
            return False  # Continue iteration

        if root.isSculptObject():
            objects.append(root)
        root.iterateVisibleSubtree(collector)
        return objects


# =============================================================================
# SELECTION OPERATIONS
# =============================================================================

class SelectionAPI:
    """
    Static API for selection state management.

    Provides utilities for saving and restoring selection state,
    which is important because many operations inadvertently change selection.
    """

    @staticmethod
    def save_selection() -> list[coat.SceneElement]:
        """
        Save the current selection state.

        Returns:
            List of currently selected elements (for later restoration)
        """
        return SceneAPI.get_selected_elements()

    @staticmethod
    def restore_selection(elements: list[coat.SceneElement]) -> None:
        """
        Restore selection to a previously saved state.

        Args:
            elements: List of elements to select (from save_selection)
        """
        if not elements:
            return

        # Select the first one exclusively, then add others
        elements[0].selectOne()
        for el in elements[1:]:
            el.select()

    @staticmethod
    def select_one(element: coat.SceneElement) -> None:
        """
        Select a single element exclusively (deselect all others).

        Args:
            element: Element to select
        """
        element.selectOne()

    @staticmethod
    def select_add(element: coat.SceneElement) -> None:
        """
        Add an element to the current selection.

        Args:
            element: Element to add to selection
        """
        element.select()


# =============================================================================
# ELEMENT OPERATIONS (Pure functions that take elements as args)
# =============================================================================

def apply_to_elements(
    elements: list[coat.SceneElement],
    operation: Callable[[coat.SceneElement], None]
) -> int:
    """
    Apply an operation to a list of elements.

    This is the core pattern: receive data as arguments, don't fetch context.

    Args:
        elements: List of elements to process
        operation: Function to apply to each element

    Returns:
        Number of elements processed
    """
    count: int = 0
    for el in elements:
        operation(el)
        count += 1
    return count


def filter_elements(
    elements: list[coat.SceneElement],
    predicate: Callable[[coat.SceneElement], bool]
) -> list[coat.SceneElement]:
    """
    Filter elements by a predicate function.

    Args:
        elements: List of elements to filter
        predicate: Function returning True for elements to keep

    Returns:
        Filtered list of elements
    """
    return [el for el in elements if predicate(el)]


def filter_sculpt_objects(elements: list[coat.SceneElement]) -> list[coat.SceneElement]:
    """
    Filter to only sculpt objects.

    Args:
        elements: List of elements to filter

    Returns:
        List containing only elements where isSculptObject() is True
    """
    return filter_elements(elements, lambda el: el.isSculptObject())


def get_element_ids(elements: list[coat.SceneElement]) -> set[int]:
    """
    Get Python object IDs for a list of elements (for fast set operations).

    Args:
        elements: List of elements

    Returns:
        Set of Python object IDs
    """
    return {id(el) for el in elements}


def deduplicate_elements(elements: list[coat.SceneElement]) -> list[coat.SceneElement]:
    """
    Remove duplicate elements while preserving order.

    Args:
        elements: List that may contain duplicates

    Returns:
        List with duplicates removed
    """
    seen: set[int] = set()
    unique: list[coat.SceneElement] = []
    for el in elements:
        el_id: int = id(el)
        if el_id not in seen:
            seen.add(el_id)
            unique.append(el)
    return unique
