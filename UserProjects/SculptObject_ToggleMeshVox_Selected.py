"""
Toggle Mesh/Voxel Same Polycount

This script toggles the current sculpt object between surface (mesh) and voxel modes
while attempting to maintain approximately the same polycount.

Room: Sculpt
Action: Toggle between surface and voxel modes, preserving polycount
"""
import coat

from _utils.object_utils import ObjectUtils
from _utils.mesh_utils import resample_to_target, convert_to_surface
from _utils.coat_ui_utils import show_message, show_error


def main() -> None:
    """Toggle between mesh and voxel modes while preserving polycount."""
    # Get current object with validation
    result = ObjectUtils.get_current_sculpt_volume()
    if not result:
        return

    current_object, vol = result
    initial_polycount: int = vol.getPolycount()
    object_name: str = current_object.name()

    if vol.isSurface():
        # Surface → Voxels: resample, convert, resample again
        print(f"Converting {object_name} to Voxels...")
        resample_to_target(initial_polycount, initial_polycount)
        vol.toVoxels()
        resample_to_target(vol.getPolycount(), initial_polycount)

        new_polycount: int = vol.getPolycount()
        show_message(f"Converted to Voxels: {new_polycount:,} polys", 3000)
    else:
        # Voxels → Surface
        print(f"Converting {object_name} to Surface...")
        convert_to_surface(vol)

        new_polycount: int = vol.getPolycount()
        show_message(f"Converted to Surface: {new_polycount:,} polys", 3000)


main()
