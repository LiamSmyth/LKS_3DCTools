"""
Safely remesh and re-symmetrize all objects in the selected subtree.

Applies the safe remesh+symmetrize process to each sculpt object in the
subtree, preserving original polycounts.

Room: Sculpt
Action: Remesh, symmetrize all objects in subtree
"""
import coat
from _utils.scene_api import SceneAPI
from _utils.Volume_resample_utils import execute_resample
from _utils.Volume_decimate_utils import decimate_to_target
from _utils.Volume_subdivide_utils import make_symmetrical
from _utils.Scene_cleanup_utils import cleanup_after_mesh_operation
from _utils.coat_ui_utils import show_message, show_error

# Default resample scale preserves details during voxel conversion
DEFAULT_RESAMPLE_SCALE: float = 4.0


def remesh_resymm_safe(element: coat.SceneElement) -> bool:
    """
    Safely remesh and symmetrize a sculpt object.

    Args:
        element: The SceneElement to process

    Returns:
        True if successful, False otherwise
    """
    element.selectOne()

    if not element.isSculptObject():
        return False

    vol: coat.Volume = element.Volume()
    target_polycount: int = vol.getPolycount()

    if target_polycount <= 0:
        return False

    # Resample to preserve detail if surface
    if not vol.isVoxelized():
        resample_target: int = int(target_polycount * DEFAULT_RESAMPLE_SCALE)
        execute_resample(
            target_polycount=resample_target,
            scale=DEFAULT_RESAMPLE_SCALE,
        )
        vol.toVoxels()

    # Make symmetrical in voxel mode
    make_symmetrical()

    # Convert back to surface
    vol.toSurface()
    new_polycount: int = vol.getPolycount()

    # Decimate back to target if polycount increased
    max_attempts: int = 3
    attempt: int = 0

    while new_polycount > target_polycount + 1000 and attempt < max_attempts:
        decimate_to_target(target_polycount)
        new_polycount = vol.getPolycount()
        attempt += 1

    return True


def main() -> None:
    """Remesh and symmetrize all objects in subtree."""
    root: coat.SceneElement | None = SceneAPI.get_current_element()
    if not root:
        show_error("No object selected", 2000)
        return

    # Collect all sculpt objects in subtree
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(root)
    sculpt_objects: list[coat.SceneElement] = [
        el for el in subtree if el.isSculptObject()
    ]

    if not sculpt_objects:
        show_error("No sculpt objects in subtree", 2000)
        return

    # Process each object
    count: int = 0
    for element in sculpt_objects:
        if remesh_resymm_safe(element):
            count += 1

    # Cleanup and restore selection
    cleanup_after_mesh_operation()
    root.selectOne()

    show_message(f"Remesh + symmetrize: {count} objects", 2000)


main()
