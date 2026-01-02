"""
Isolate selected object (ghost all others).

Room: Sculpt
Action: Ghost all except selected (toggle isolation mode)
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.SceneElement_visibility_utils import ghost_except
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Toggle isolation mode - ghost all except current selection."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()

    if not current:
        show_message("No object selected", 3000)
        return

    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    # Get currently selected elements (could be multiple)
    selected: list[coat.SceneElement] = SceneAPI.get_selected_elements()

    # Ghost all except selected
    count: int = ghost_except(all_elements, selected)

    show_message(f"Isolated - ghosted {count} objects", 3000)


main()
