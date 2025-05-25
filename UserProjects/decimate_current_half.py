"""
Decimate Current Half

This script decimates the current object to 50% of its original polycount.
It uses the 3DCoat decimation dialog with preset values.
"""
import coat
from _utils.object_utils import ObjectUtils
from _utils.ui_dialog_utils import UIDialogUtils


def decimate_current_half():
    """Decimate current object to half its polycount"""

    # Get current sculpt object and volume with validation
    result = ObjectUtils.get_current_sculpt_volume()
    if not result:
        return

    current_object, vol = result

    # Validate object has polygons
    if not ObjectUtils.validate_object_has_polygons(vol):
        return

    # Convert to surface if it's voxelized
    ObjectUtils.ensure_surface_mode(vol)

    # Get current polycount
    current_polycount = vol.getPolycount()

    print(f"Decimating object from {current_polycount:,} polygons...")

    # Execute the decimate command to half
    UIDialogUtils.execute_decimate_to_half()

    # Get the new polycount after decimation
    new_polycount = vol.getPolycount()
    ObjectUtils.print_polycount_info(
        "Decimation complete", current_polycount, new_polycount)

    reduction_percent = (
        (current_polycount - new_polycount) / current_polycount) * 100
    ObjectUtils.show_polycount_message(
        f"Decimated ({reduction_percent:.1f}% reduction)", new_polycount)

    # Show summary message to user
    coat.ui.showInfoMessage(
        f"Object decimated to {new_polycount:,} polygons ({reduction_percent:.1f}% reduction)", 4000)


def main():
    decimate_current_half()


# 3DCoat executes script content directly, so call main() here
main()
