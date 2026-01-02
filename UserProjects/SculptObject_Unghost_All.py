"""
Unghost all objects in scene.

Room: Sculpt
Action: Remove ghost state from all objects
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.SceneElement_visibility_utils import unghost_elements
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Unghost all objects in sculpt tree."""
    # Save current selection
    current: coat.SceneElement | None = SceneAPI.get_current_element()

    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    if not all_elements:
        show_message("No objects in scene", 3000)
        return

    count: int = unghost_elements(all_elements)

    # Restore selection
    if current:
        current.selectOne()

    show_message(f"Unghosted {count} objects", 3000)


main()
