"""
Object Utilities

Common utility functions for 3DCoat object validation and manipulation.
This module provides static functions for repetitive object operations.

Design Principles:
- Static functions that receive data as arguments
- Use SceneAPI for context fetching (localized at entry points)
- Explicit type annotations everywhere

Note: Files starting with "_" are hidden from the Addons menu per 3DCoat convention.
"""
import coat

from _utils.scene_api import SceneAPI, SelectionAPI
from _utils.coat_ui_utils import show_message, show_error


# =============================================================================
# CONSTANTS
# =============================================================================

MESSAGE_NO_OBJECT: str = "No object selected"
MESSAGE_NOT_SCULPT_OBJECT: str = "Selected object is not a sculpt object"
MESSAGE_NO_VOLUME: str = "No volume found on selected object"
MESSAGE_NO_POLYGONS: str = "Object has no polygons"

DEFAULT_MESSAGE_DURATION_MS: int = 3000


class ObjectUtils:
    """Static utility functions for 3DCoat object operations."""

    @staticmethod
    def get_current_sculpt_object() -> coat.SceneElement | None:
        """
        Get the current sculpt object with validation.

        Returns:
            The current sculpt object, or None if invalid
        """
        current_object: coat.SceneElement | None = SceneAPI.get_current_element()

        if not current_object:
            show_error(MESSAGE_NO_OBJECT, DEFAULT_MESSAGE_DURATION_MS)
            return None

        if not current_object.isSculptObject():
            show_error(MESSAGE_NOT_SCULPT_OBJECT, DEFAULT_MESSAGE_DURATION_MS)
            return None

        return current_object

    @staticmethod
    def get_volume_from_element(element: coat.SceneElement) -> coat.Volume | None:
        """
        Get volume from a scene element with validation.

        Args:
            element: The scene element to get volume from

        Returns:
            The volume object, or None if invalid
        """
        if not element:
            return None

        vol: coat.Volume | None = element.Volume()

        if not vol:
            show_error(MESSAGE_NO_VOLUME, DEFAULT_MESSAGE_DURATION_MS)
            return None

        return vol

    @staticmethod
    def validate_volume_has_polygons(vol: coat.Volume) -> bool:
        """
        Validate that a volume has polygons.

        Args:
            vol: The volume to validate

        Returns:
            True if volume has polygons, False otherwise
        """
        if not vol:
            return False

        polycount: int = vol.getPolycount()
        if polycount == 0:
            show_error(MESSAGE_NO_POLYGONS, DEFAULT_MESSAGE_DURATION_MS)
            return False

        return True

    @staticmethod
    def get_current_sculpt_volume() -> tuple[coat.SceneElement, coat.Volume] | None:
        """
        Get current sculpt object and its volume with full validation.

        Returns:
            Tuple of (element, volume) if valid, None otherwise
        """
        element: coat.SceneElement | None = ObjectUtils.get_current_sculpt_object()
        if not element:
            return None

        # Ensure the object is selected
        SelectionAPI.select_one(element)

        vol: coat.Volume | None = ObjectUtils.get_volume_from_element(element)
        if not vol:
            return None

        return (element, vol)

    @staticmethod
    def ensure_surface_mode(vol: coat.Volume) -> None:
        """
        Ensure volume is in surface mode (convert from voxels if needed).

        Args:
            vol: The volume to convert
        """
        if vol.isVoxelized():
            vol.toSurface()

    @staticmethod
    def print_polycount_info(name: str, before: int, after: int) -> None:
        """
        Print formatted polycount information.

        Args:
            name: Operation name
            before: Polycount before operation
            after: Polycount after operation
        """
        reduction_percent: float = 0.0
        if before > 0:
            reduction_percent = ((before - after) / before) * 100

        message: str = f"{name}: {before:,} -> {after:,} polygons ({reduction_percent:.1f}% reduction)"
        print(message)


# =============================================================================
# VALIDATION + MODE UTILITIES (Pure functions)
# =============================================================================

def validate_and_ensure_surface_mode() -> bool:
    """
    Validate current sculpt object exists and ensure it's in surface mode.

    This is a convenience function for action scripts that need to verify:
    1. A sculpt object is selected
    2. It has a valid volume
    3. It's in surface mode (converting from voxels if needed)

    Returns:
        True if a valid sculpt object is ready in surface mode, False otherwise
    """
    current: coat.SceneElement | None = coat.Scene.current()
    if not current:
        return False
    if not current.isSculptObject():
        return False

    vol: coat.Volume | None = current.Volume()
    if not vol:
        return False

    if not vol.isSurface():
        # Convert to surface mode
        vol.toSurface()
        coat.io.step(2)

    return True

    @staticmethod
    def show_polycount_message(
        operation: str,
        polycount: int,
        duration_ms: int = DEFAULT_MESSAGE_DURATION_MS
    ) -> None:
        """
        Show a formatted polycount message to the user.

        Args:
            operation: The operation performed
            polycount: The resulting polycount
            duration_ms: Message duration in milliseconds
        """
        message: str = f"{operation}: {polycount:,} polys"
        show_message(message, duration_ms)

    @staticmethod
    def scale_selected_element(element: coat.SceneElement, scale_factor: float) -> None:
        """
        Select and scale an element by factor.

        Args:
            element: The element to scale
            scale_factor: Factor to multiply current scale by
        """
        scale_element_with_select(element, scale_factor)


# =============================================================================
# ELEMENT TRANSFORM OPERATIONS (Pure functions)
# =============================================================================

def scale_element(element: coat.SceneElement, scale_factor: float) -> None:
    """
    Scale a scene element by a factor.

    Does NOT select the element - caller should handle selection if needed.

    Args:
        element: The element to scale
        scale_factor: Factor to multiply current scale by
    """
    # Get the current 4x4 transformation matrix
    transform: coat.mat4 = element.getTransform()

    existing_scale: coat.vec3 = transform.GetScaling()
    new_scale: coat.vec3 = existing_scale * scale_factor
    transform.SetScaling(new_scale)
    element.setTransform(transform)


def scale_element_with_select(element: coat.SceneElement, scale_factor: float) -> None:
    """
    Select and scale a scene element by a factor.

    Args:
        element: The element to scale
        scale_factor: Factor to multiply current scale by
    """
    SelectionAPI.select_one(element)
    scale_element(element, scale_factor)


def scale_elements(elements: list[coat.SceneElement], scale_factor: float) -> int:
    """
    Scale multiple elements by a factor.

    Args:
        elements: List of elements to scale
        scale_factor: Factor to multiply current scale by

    Returns:
        Number of elements scaled
    """
    count: int = 0
    for el in elements:
        scale_element(el, scale_factor)
        count += 1
    return count
