"""
Object Utilities

Common utility functions for 3DCoat object validation and manipulation.
This module provides static functions for repetitive object operations.

Note: Files starting with "_" are hidden from the Addons menu per 3DCoat convention.
"""
import coat
from typing import Optional, Tuple


class ObjectUtils:
    """Static utility functions for 3DCoat object operations"""

    @staticmethod
    def get_current_sculpt_object() -> Optional[coat.SceneElement]:
        """
        Get the current sculpt object with validation.

        Returns:
            The current sculpt object, or None if invalid
        """
        current_object: coat.SceneElement = coat.Scene.current()

        if not current_object:
            coat.ui.showInfoMessage("No object selected", 3000)
            return None

        if not current_object.isSculptObject():
            coat.ui.showInfoMessage(
                "Selected object is not a sculpt object", 3000)
            return None

        return current_object

    @staticmethod
    def get_volume_from_object(obj: coat.SceneElement) -> Optional[coat.Volume]:
        """
        Get volume from a scene element with validation.

        Args:
            obj: The scene element to get volume from

        Returns:
            The volume object, or None if invalid
        """
        if not obj:
            return None

        vol: coat.Volume = obj.Volume()

        if not vol:
            coat.ui.showInfoMessage("No volume found on selected object", 3000)
            return None

        return vol

    @staticmethod
    def validate_object_has_polygons(vol: coat.Volume) -> bool:
        """
        Validate that a volume has polygons.

        Args:
            vol: The volume to validate

        Returns:
            True if volume has polygons, False otherwise
        """
        if not vol:
            return False

        polycount = vol.getPolycount()
        if polycount == 0:
            coat.ui.showInfoMessage("Object has no polygons", 3000)
            return False

        return True

    @staticmethod
    def get_current_sculpt_volume() -> Optional[Tuple[coat.SceneElement, coat.Volume]]:
        """
        Get current sculpt object and its volume with full validation.

        Returns:
            Tuple of (object, volume) if valid, None otherwise
        """
        obj = ObjectUtils.get_current_sculpt_object()
        if not obj:
            return None

        # Ensure the object is selected
        obj.selectOne()

        vol = ObjectUtils.get_volume_from_object(obj)
        if not vol:
            return None

        return (obj, vol)

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
        reduction_percent = ((before - after) / before) * \
            100 if before > 0 else 0
        print(
            f"{name}: {before:,} -> {after:,} polygons ({reduction_percent:.1f}% reduction)")

    @staticmethod
    def show_polycount_message(operation: str, polycount: int, duration: int = 3000) -> None:
        """
        Show a formatted polycount message to the user.

        Args:
            operation: The operation performed
            polycount: The resulting polycount
            duration: Message duration in milliseconds
        """
        coat.ui.showInfoMessage(f"{operation}: {polycount:,} polys", duration)

    @staticmethod
    def scale_selected_element(el: coat.SceneElement, scale_factor: float):
        el.selectOne()

        # Get the current 4x4 transformation matrix
        transform: coat.mat4 = el.getTransform()

        existing_scale: coat.vec3 = transform.GetScaling()
        new_scale = existing_scale * scale_factor
        transform.SetScaling(new_scale)
        el.setTransform(transform)
