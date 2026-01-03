"""
Decimate selected object to 50% of its original polycount.

Room: Sculpt
Action: Decimate 50% on selected object
"""
import coat

from _utils.object_utils import ObjectUtils
from _utils.mesh_utils import decimate_to_half, cleanup_after_mesh_operation
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Decimate current object to half its polycount."""
    # Get current sculpt object and volume with validation
    result = ObjectUtils.get_current_sculpt_volume()
    if not result:
        return

    current_object, vol = result

    # Validate object has polygons
    if not ObjectUtils.validate_volume_has_polygons(vol):
        return

    # Convert to surface if it's voxelized
    ObjectUtils.ensure_surface_mode(vol)

    # Get current polycount
    current_polycount: int = vol.getPolycount()
    print(f"Decimating object from {current_polycount:,} polygons...")

    # Execute the decimate command to half
    decimate_to_half()

    # Cleanup after mesh operation
    cleanup_after_mesh_operation()

    # Get the new polycount after decimation
    new_polycount: int = vol.getPolycount()
    reduction_percent: float = (
        (current_polycount - new_polycount) / current_polycount) * 100

    # Show summary message to user
    show_message(
        f"Decimated to {new_polycount:,} ({reduction_percent:.1f}% reduction)",
        4000
    )


# 3DCoat executes script content directly
main()
