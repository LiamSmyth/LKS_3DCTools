"""
Create subtract boolean child under selected object.

Room: Sculpt
Action: Clone selected, parent under it, set to subtract boolean
Requires: Parent must be in voxel mode
"""
import coat

from utils.SceneElement_boolean_utils import create_subtract_child
from utils.coat_ui_utils import show_message


def main() -> None:
    """Create a subtract boolean child for current element."""
    parent: coat.SceneElement | None = coat.Scene.current()
    if not parent:
        show_message("No object selected", 3000)
        return

    child: coat.SceneElement | None = create_subtract_child(parent)

    if child:
        show_message(f"Created subtract: {child.name()}", 3000)


main()
