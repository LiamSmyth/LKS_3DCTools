"""
Toggle ghost state for selected object and all children.

Room: Sculpt
Action: Toggle ghost on subtree (invert current state)
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.visibility_utils import set_ghost
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Toggle ghost state for current element and its subtree."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_message("No object selected", 3000)
        return

    # Determine new ghost state (invert current)
    current_ghost: bool = current.ghost()
    new_ghost: bool = not current_ghost

    # Collect all elements in subtree
    elements: list[coat.SceneElement] = SceneAPI.collect_subtree(current)

    # Apply ghost state to all
    count: int = set_ghost(elements, new_ghost)

    # Restore selection
    current.selectOne()

    # Show summary
    status: str = "ghosted" if new_ghost else "unghosted"
    show_message(f"{count} objects {status}", 3000)


main()
