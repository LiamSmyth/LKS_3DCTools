"""
Subdivide selected object and all children (double polycount).

Room: Sculpt
Action: Subdivide subtree (approximately 2x polycount)
"""
import coat

from _utils.scene_api import SceneAPI
from _utils.mesh_utils import subdivide_once, ensure_surface_mode
from _utils.coat_ui_utils import show_message


def subdivide_element(el: coat.SceneElement) -> bool:
    """Subdivide a single element. Returns False to continue iteration."""
    if not el.isSculptObject():
        return False

    vol: coat.Volume = el.Volume()
    ensure_surface_mode(vol)
    el.selectOne()
    subdivide_once()

    return False  # Continue iteration


def main() -> None:
    """Subdivide current object and subtree."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_message("No object selected", 3000)
        return

    # Subdivide root element
    subdivide_element(current)

    # Subdivide all children
    current.iterateSubtree(subdivide_element)

    # Restore selection
    current.selectOne()

    show_message("Subtree subdivision complete (doubled polycount)", 3000)


main()
