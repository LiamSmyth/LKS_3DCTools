"""
Scene Iteration Utilities

Common utility functions for 3DCoat scene tree iteration operations.
This module provides static functions for common tree traversal patterns.

Note: Files starting with "_" are hidden from the Addons menu per 3DCoat convention.
"""
import coat
from typing import Callable, Optional


class SceneIterationUtils:
    """Static utility functions for 3DCoat scene iteration operations"""

    @staticmethod
    def iterate_sculpt_objects(operation_func: Callable[[coat.SceneElement], bool],
                               include_current: bool = True) -> None:
        """
        Iterate over all sculpt objects and apply an operation function.

        Args:
            operation_func: Function to apply to each sculpt object. 
                          Should return False to continue iteration, True to stop.
            include_current: Whether to include the current object in iteration
        """
        active_element: coat.SceneElement = coat.Scene.current()
        scene_root: coat.SceneElement = coat.Scene.sculptRoot()

        if include_current and active_element:
            operation_func(active_element)

        scene_root.iterateSubtree(operation_func)

        # Restore selection to the original active element
        if active_element:
            active_element.selectOne()

    @staticmethod
    def convert_all_to_surface() -> None:
        """Convert all sculpt objects to surface mode."""
        def convert_to_surface(el: coat.SceneElement):
            el.selectOne()
            vol: coat.Volume = el.Volume()
            if vol and not vol.isSurface():
                vol.toSurface()
            return False  # Continue iteration

        SceneIterationUtils.iterate_sculpt_objects(convert_to_surface)

    @staticmethod
    def convert_all_to_voxels() -> None:
        """Convert all sculpt objects to voxel mode."""
        def convert_to_voxels(el: coat.SceneElement):
            el.selectOne()
            vol: coat.Volume = el.Volume()
            if vol and vol.isSurface():
                vol.toVoxels()
            return False  # Continue iteration

        SceneIterationUtils.iterate_sculpt_objects(convert_to_voxels)

    @staticmethod
    def apply_to_subtree(root_element: coat.SceneElement,
                         operation_func: Callable[[coat.SceneElement], bool]) -> None:
        """
        Apply operation to a specific subtree.

        Args:
            root_element: The root element of the subtree
            operation_func: Function to apply to each element in subtree
        """
        if not root_element:
            return

        # Apply to root first
        operation_func(root_element)

        # Then apply to subtree
        root_element.iterateSubtree(operation_func)

    @staticmethod
    def get_all_sculpt_objects() -> list:
        """
        Get a list of all sculpt objects in the scene.

        Returns:
            List of all sculpt objects
        """
        objects = []

        def collect_object(el: coat.SceneElement):
            if el.isSculptObject():
                objects.append(el)
            return False  # Continue iteration

        scene_root: coat.SceneElement = coat.Scene.sculptRoot()
        collect_object(scene_root)
        scene_root.iterateSubtree(collect_object)

        return objects

    @staticmethod
    def toggle_ghost_all_except_current() -> None:
        """Toggle ghost state for all objects except the current one."""
        active_element: coat.SceneElement = coat.Scene.current()
        sculpt_root: coat.SceneElement = coat.Scene.sculptRoot()

        # Check if isolate is currently active
        isolate_is_active = sculpt_root.ghost()

        def update_ghost(el: coat.SceneElement):
            el.setGhost(not isolate_is_active)
            return False  # Continue iteration

        # Update root and all children
        update_ghost(sculpt_root)
        sculpt_root.iterateSubtree(update_ghost)

        # Ensure the active element is not ghosted
        if active_element:
            active_element.selectOne()
            active_element.setGhost(False)
