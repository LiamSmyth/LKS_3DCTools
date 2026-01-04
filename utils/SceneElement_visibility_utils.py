"""
Visibility Utilities

Pure functions for manipulating visibility and ghost state of scene elements.
All functions receive elements as arguments - no context fetching.

Design Principles:
- Functions take element lists as arguments
- No coat.Scene calls inside these functions
- Return counts for feedback
"""
import coat
from typing import Callable


# =============================================================================
# ELEMENT VISIBILITY OPERATIONS (Pure functions)
# =============================================================================

def set_visibility(elements: list[coat.SceneElement], visible: bool) -> int:
    """
    Set visibility state for a list of elements.

    Args:
        elements: List of elements to modify
        visible: True to show, False to hide

    Returns:
        Number of elements modified
    """
    count: int = 0
    for el in elements:
        el.setVisibility(visible)
        count += 1
    return count


def hide_elements(elements: list[coat.SceneElement]) -> int:
    """
    Hide a list of elements.

    Args:
        elements: List of elements to hide

    Returns:
        Number of elements hidden
    """
    return set_visibility(elements, False)


def show_elements(elements: list[coat.SceneElement]) -> int:
    """
    Show a list of elements.

    Args:
        elements: List of elements to show

    Returns:
        Number of elements shown
    """
    return set_visibility(elements, True)


def set_ghost(elements: list[coat.SceneElement], ghosted: bool) -> int:
    """
    Set ghost state for a list of elements.

    Args:
        elements: List of elements to modify
        ghosted: True to ghost, False to unghost

    Returns:
        Number of elements modified
    """
    count: int = 0
    for el in elements:
        el.setGhost(ghosted)
        count += 1
    return count


def ghost_elements(elements: list[coat.SceneElement]) -> int:
    """
    Ghost a list of elements.

    Args:
        elements: List of elements to ghost

    Returns:
        Number of elements ghosted
    """
    return set_ghost(elements, True)


def unghost_elements(elements: list[coat.SceneElement]) -> int:
    """
    Unghost a list of elements.

    Args:
        elements: List of elements to unghost

    Returns:
        Number of elements unghosted
    """
    return set_ghost(elements, False)


def invert_visibility_on_elements(elements: list[coat.SceneElement]) -> int:
    """
    Invert visibility on a list of elements.

    Args:
        elements: List of elements to invert

    Returns:
        Number of elements inverted
    """
    count: int = 0
    for el in elements:
        current: bool = el.visible()
        el.setVisibility(not current)
        count += 1
    return count


def invert_ghost_on_elements(elements: list[coat.SceneElement]) -> int:
    """
    Invert ghost state on a list of elements.

    Args:
        elements: List of elements to invert

    Returns:
        Number of elements inverted
    """
    count: int = 0
    for el in elements:
        current: bool = el.ghost()
        el.setGhost(not current)
        count += 1
    return count


# =============================================================================
# STATE CACHING
# =============================================================================

def cache_ghost_states(
    elements: list[coat.SceneElement]
) -> dict[int, bool]:
    """
    Cache the ghost state of all elements.

    Args:
        elements: List of elements to cache

    Returns:
        Dict mapping element id() to ghost state
    """
    return {id(el): el.ghost() for el in elements}


def restore_ghost_states(
    elements: list[coat.SceneElement],
    cache: dict[int, bool]
) -> int:
    """
    Restore ghost states from a cache.

    Args:
        elements: List of elements to restore
        cache: Dict from cache_ghost_states()

    Returns:
        Number of elements restored
    """
    count: int = 0
    for el in elements:
        el_id: int = id(el)
        if el_id in cache:
            el.setGhost(cache[el_id])
            count += 1
    return count


# =============================================================================
# FILTERED OPERATIONS
# =============================================================================

def _element_in_list(el: coat.SceneElement, elements: list[coat.SceneElement]) -> bool:
    """
    Check if element is in list using 3DCoat's equality operator.

    Note: We use explicit loop with __eq__ because Python set/dict would use
    id() or __hash__ which may not work correctly for 3DCoat wrapper objects.

    Args:
        el: Element to check
        elements: List to check against

    Returns:
        True if element is in list (via __eq__)
    """
    for other in elements:
        if el == other:
            return True
    return False


def hide_except(
    all_elements: list[coat.SceneElement],
    keep_visible: list[coat.SceneElement]
) -> int:
    """
    Hide all elements except those in the keep_visible list.

    Args:
        all_elements: All elements to consider
        keep_visible: Elements that should remain visible

    Returns:
        Number of elements hidden
    """
    to_hide: list[coat.SceneElement] = [
        el for el in all_elements if not _element_in_list(el, keep_visible)
    ]
    return hide_elements(to_hide)


def ghost_except(
    all_elements: list[coat.SceneElement],
    keep_unghosted: list[coat.SceneElement]
) -> int:
    """
    Ghost all elements except those in the keep_unghosted list.

    Args:
        all_elements: All elements to consider
        keep_unghosted: Elements that should remain unghosted

    Returns:
        Number of elements ghosted
    """
    to_ghost: list[coat.SceneElement] = [
        el for el in all_elements if not _element_in_list(el, keep_unghosted)
    ]
    return ghost_elements(to_ghost)
