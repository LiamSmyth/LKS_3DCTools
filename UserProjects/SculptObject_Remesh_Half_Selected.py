"""
Half Polycount

This script reduces the polycount of the current object by half using voxel conversion.
If the object is already voxelized, it converts to surface first.
"""
import coat
from _utils.object_utils import ObjectUtils
from _utils.ui_dialog_utils import UIDialogUtils


def half_polycount():
    """Reduce polycount by half using voxel conversion"""

    # Get current sculpt object and volume with validation
    result = ObjectUtils.get_current_sculpt_volume()
    if not result:
        return

    current_object, vol = result

    # Validate object has polygons
    if not ObjectUtils.validate_object_has_polygons(vol):
        return

    # If it's voxelized, convert to surface first
    ObjectUtils.ensure_surface_mode(vol)

    # Get current polycount
    current_polycount = vol.getPolycount()
    target_polycount = current_polycount // 2

    print(
        f"Reducing polycount by half: {current_polycount:,} -> {target_polycount:,}")

    # Use resample to achieve target polycount, then convert to voxels
    UIDialogUtils.execute_resample_to_half(current_polycount)

    # Convert to voxels with the reduced polycount
    vol.toVoxels()

    new_polycount = vol.getPolycount()
    print(f"Final voxel polycount: {new_polycount:,}")
    ObjectUtils.show_polycount_message("Reduced to Half", new_polycount)


def main():
    half_polycount()


# 3DCoat executes script content directly, so call main() here
main()
