"""
Toggle Mesh/Voxel Same Polycount

This script toggles the current sculpt object between surface (mesh) and voxel modes
while attempting to maintain approximately the same polycount.
"""
import coat
from _utils.ui_dialog_utils import UIDialogUtils
import importlib


def toggle_mesh_voxel_same_polycount():
    """Toggle between mesh and voxel modes while preserving polycount"""

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

    # Get current polycount for reference
    initial_polycount = vol.getPolycount()
    object_name = current_object.name()

    print(f"Processing object: {object_name}")
    print(f"Current polycount: {initial_polycount}")

    if vol.isSurface():
        print("Surface Polycount before: ", vol.getPolycount())
        # Resmaple before, and after conversion to voxel
        UIDialogUtils.execute_resample_element_to_polycount(
            current_object, initial_polycount)

        print("Surface Resampled to polycount: ", vol.getPolycount())
        vol.toVoxels()
        print("Converted to Voxels - polycount: ", vol.getPolycount())
        UIDialogUtils.execute_resample_element_to_polycount(
            current_object, initial_polycount)

        print("Voxels Resampled to polycount: ", vol.getPolycount())

        new_polycount = vol.getPolycount()
        print(f"Converted to voxels - new polycount: {new_polycount}")
        coat.ui.showInfoMessage(
            f"Converted to Voxels: {new_polycount:,} polys", 3000)

    else:
        # Currently in voxel mode, convert to surface
        print("Converting from Voxels to Surface...")

        # Convert to surface mesh
        vol.toSurface()

        new_polycount = vol.getPolycount()
        print(f"Converted to surface - new polycount: {new_polycount}")
        coat.ui.showInfoMessage(
            f"Converted to Surface: {new_polycount:,} polys", 3000)


def main():
    toggle_mesh_voxel_same_polycount()


# 3DCoat executes script content directly, so call main() here
main()
