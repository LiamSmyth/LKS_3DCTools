"""
Invert ghost state for all objects in scene.

Room: Sculpt
Action: Invert ghost state (ghosted→unghosted, unghosted→ghosted)
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.SceneElement_visibility_utils import invert_ghost_on_elements
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Invert ghost state for all objects in sculpt tree."""
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    if not all_elements:
        show_message("No objects in scene", 3000)
        return

    count: int = invert_ghost_on_elements(all_elements)
    show_message(f"Inverted ghost on {count} objects", 3000)


main()
