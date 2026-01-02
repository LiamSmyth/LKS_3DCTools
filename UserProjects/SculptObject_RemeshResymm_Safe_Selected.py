"""
Safely remesh and re-symmetrize the selected sculpt object.

Preserves the original polycount by resampling first, converting to voxels,
making symmetrical, converting back to surface, then decimating if needed.

Room: Sculpt
Action: Remesh, symmetrize, and restore polycount on selected object
"""
import coat
from _utils.object_utils import ObjectUtils
from _utils.mesh_utils import (
    execute_resample,
    ResampleParams,
    decimate_to_target,
    make_symmetrical,
    cleanup_after_mesh_operation,
)
from _utils.coat_ui_utils import show_message, show_error

# Default resample scale preserves details during voxel conversion
DEFAULT_RESAMPLE_SCALE: float = 4.0


def remesh_resymm_safe(element: coat.SceneElement) -> bool:
    """
    Safely remesh and symmetrize a sculpt object.

    Process:
    1. Resample at higher detail if surface mode
    2. Convert to voxels
    3. Make symmetrical
    4. Convert back to surface
    5. Decimate back to original polycount if needed

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

    print(f"Remeshing {element.name()} to target {target_polycount:,} polys")

    # Resample to preserve detail if surface
    if not vol.isVoxelized():
        params = ResampleParams(
            target_polycount=target_polycount,
            scale=DEFAULT_RESAMPLE_SCALE
        )
        execute_resample(params)
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
        print(f"Decimating from {new_polycount:,} to {target_polycount:,}")
        decimate_to_target(target_polycount)
        new_polycount = vol.getPolycount()
        attempt += 1

    cleanup_after_mesh_operation()

    print(f"Completed: {element.name()} at {new_polycount:,} polys")
    return True


def main() -> None:
    """Remesh and symmetrize the currently selected object."""
    element: coat.SceneElement | None = ObjectUtils.get_current_sculpt_object()
    if not element:
        show_error("No sculpt object selected", 2000)
        return

    success: bool = remesh_resymm_safe(element)

    if success:
        show_message(f"Remesh + symmetrize complete", 2000)
    else:
        show_error("Failed to process object", 2000)


main()
