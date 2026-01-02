"""
Convert all sculpt objects to surface mode.

Room: Sculpt
Action: Convert all voxel objects to surface mode
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.mesh_utils import convert_to_surface
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Convert all sculpt objects to surface mode."""
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    if not all_elements:
        show_message("No objects in scene", 3000)
        return

    count: int = 0
    for el in all_elements:
        if el.isSculptObject():
            vol: coat.Volume = el.Volume()
            if vol.isVoxelized():
                convert_to_surface(vol)
                count += 1

    show_message(f"Converted {count} objects to surface mode", 3000)


main()
