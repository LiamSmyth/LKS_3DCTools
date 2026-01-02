"""
Convert surface to voxels with 2x polycount (or back to surface).

Room: Sculpt
Action: Resample to 2x polycount and convert to voxels
"""
from _utils.object_utils import ObjectUtils
from _utils.mesh_utils import resample_and_voxelize
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Toggle between surface and voxels with 2x polycount."""
    result = ObjectUtils.get_current_sculpt_volume()
    if not result:
        return

    current_object, vol = result
    was_voxelized: bool = vol.isVoxelized()
    
    new_polycount: int = resample_and_voxelize(vol, multiplier=2.0)
    
    if was_voxelized:
        show_message(f"Converted to Surface: {new_polycount:,} polys", 3000)
    else:
        show_message(f"Converted to Voxels (2x): {new_polycount:,} polys", 3000)


main()
