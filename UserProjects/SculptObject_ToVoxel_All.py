"""
Convert all sculpt objects to voxel mode.

Room: Sculpt
Action: Convert all surface objects to voxel mode
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Convert all sculpt objects to voxel mode."""
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    if not all_elements:
        show_message("No objects in scene", 3000)
        return

    count: int = 0
    for el in all_elements:
        if el.isSculptObject():
            vol: coat.Volume = el.Volume()
            if vol.isSurface():
                vol.toVoxels()
                count += 1

    show_message(f"Converted {count} objects to voxel mode", 3000)


main()
