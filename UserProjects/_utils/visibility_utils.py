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
# FILTERED OPERATIONS
# =============================================================================

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
    keep_ids: set[int] = {id(el) for el in keep_visible}
    to_hide: list[coat.SceneElement] = [
        el for el in all_elements if id(el) not in keep_ids
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
    keep_ids: set[int] = {id(el) for el in keep_unghosted}
    to_ghost: list[coat.SceneElement] = [
        el for el in all_elements if id(el) not in keep_ids
    ]
    return ghost_elements(to_ghost)
