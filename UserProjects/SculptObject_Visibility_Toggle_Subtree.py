"""
Toggle visibility for selected object and all children.

Room: Sculpt
Action: Toggle visibility on subtree (invert current state)
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.SceneElement_visibility_utils import set_visibility
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Toggle visibility state for current element and its subtree."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_message("No object selected", 3000)
        return

    # Determine new visibility state (invert current)
    current_visible: bool = current.visible()
    new_visible: bool = not current_visible

    # Collect all elements in subtree
    elements: list[coat.SceneElement] = SceneAPI.collect_subtree(current)

    # Apply visibility state to all
    count: int = set_visibility(elements, new_visible)

    # Restore selection
    current.selectOne()

    # Show summary
    status: str = "shown" if new_visible else "hidden"
    show_message(f"{count} objects {status}", 3000)


main()
