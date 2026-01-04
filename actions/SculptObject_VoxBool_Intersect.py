"""
Create intersect boolean child under selected object.

Room: Sculpt
Action: Clone selected, parent under it, set to intersect boolean with extrusion
Requires: Parent must be in voxel mode
"""
import coat

from utils.SceneElement_boolean_utils import create_intersect_child
from utils.coat_ui_utils import show_message


def main() -> None:
    """Create an intersect boolean child for current element."""
    parent: coat.SceneElement | None = coat.Scene.current()
    if not parent:
        show_message("No object selected", 3000)
        return

    child: coat.SceneElement | None = create_intersect_child(parent)

    if child:
        show_message(f"Created intersect: {child.name()}", 3000)


main()
