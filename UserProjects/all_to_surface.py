"""
All to Surface

Convert all sculpt objects in the scene to surface mode.
"""
import coat
from _utils.scene_iteration_utils import SceneIterationUtils


def main():
    """Convert all sculpt objects to surface mode"""
    print("Converting all objects to surface mode...")
    SceneIterationUtils.convert_all_to_surface()
    print("All objects converted to surface mode")

    # Show summary message to user
    coat.ui.showInfoMessage("All objects converted to surface mode", 3000)


# 3DCoat executes script content directly, so call main() here
main()
