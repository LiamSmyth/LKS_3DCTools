"""
Decimate selected object and all children to half polycount.

Room: Sculpt
Action: Decimate 50% on subtree
"""
import coat

from _utils.mesh_utils import (
    DecimateParams,
    execute_decimate,
    cleanup_after_mesh_operation,
    ensure_surface_mode,
)
from _utils.scene_api import SceneAPI
from _utils.coat_ui_utils import show_message


def decimate_element_half(el: coat.SceneElement) -> bool:
    """Decimate a single element to 50%. Returns False to continue iteration."""
    if not el.isSculptObject():
        return False

    vol: coat.Volume = el.Volume()
    ensure_surface_mode(vol)

    el.selectOne()
    execute_decimate(DecimateParams(reduction_percent=50.0))

    return False  # Continue iteration


def main() -> None:
    """Decimate current object and subtree to half polycount."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_message("No object selected", 3000)
        return

    # Decimate root element
    decimate_element_half(current)

    # Decimate all children
    current.iterateSubtree(decimate_element_half)

    # Restore selection and cleanup
    current.selectOne()
    cleanup_after_mesh_operation()

    show_message("Subtree decimated to 50%", 3000)


main()
