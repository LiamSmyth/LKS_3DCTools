"""
Switch Voxel 8x Polys

This script converts a surface object to voxels with 8x the original polycount,
or converts voxels back to surface mode.
"""
import coat


def switch_vox_8x_polys():
    """Switch between surface and voxel modes with 8x polycount"""

    # Get the current object
    current_object: coat.SceneElement = coat.Scene.current()

    if not current_object:
        coat.ui.showInfoMessage("No object selected", 3000)
        return

    if not current_object.isSculptObject():
        coat.ui.showInfoMessage("Selected object is not a sculpt object", 3000)
        return

    # Ensure the object is selected
    current_object.selectOne()

    # Get the volume
    vol: coat.Volume = current_object.Volume()

    if not vol:
        coat.ui.showInfoMessage("No volume found on selected object", 3000)
        return

    if vol.isVoxelized():
        # If already voxelized, convert to surface
        vol.toSurface()
        polycount = vol.getPolycount()
        print(f"Converted to surface: {polycount:,} polys")
        coat.ui.showInfoMessage(
            f"Converted to Surface: {polycount:,} polys", 3000)
        return

    # Get current polycount
    current_polycount = vol.getPolycount()
    target_polycount = current_polycount * 8

    print(
        f"Converting to voxels with 8x polycount: {current_polycount:,} -> {target_polycount:,}")

    # Use resample to achieve target polycount, then convert to voxels
    if current_polycount > 0:
        def ui_command():
            coat.ui.setEditBoxValue(
                "$ResampleParams::RequiredPolycount", target_polycount)
            coat.ui.setSliderValue("$ResampleParams::ResamplingScale", 8.0)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$Resample", ui_command)

        # Now convert to voxels
        vol.toVoxels()

        new_polycount = vol.getPolycount()
        print(f"Final voxel polycount: {new_polycount:,}")
        coat.ui.showInfoMessage(
            f"Converted to Voxels (8x): {new_polycount:,} polys", 3000)


def main():
    switch_vox_8x_polys()


# 3DCoat executes script content directly, so call main() here
main()
