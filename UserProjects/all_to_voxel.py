"""
All to Voxel

Convert all sculpt objects in the scene to voxel mode.
"""
import coat
from _utils.scene_iteration_utils import SceneIterationUtils


def main():
    """Convert all sculpt objects to voxel mode"""
    print("Converting all objects to voxel mode...")
    SceneIterationUtils.convert_all_to_voxels()
    print("All objects converted to voxel mode")

    # Show summary message to user
    coat.ui.showInfoMessage("All objects converted to voxel mode", 3000)


# 3DCoat executes script content directly, so call main() here
main()
