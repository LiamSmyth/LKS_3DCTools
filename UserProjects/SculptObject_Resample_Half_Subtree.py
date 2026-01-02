"""
Resample selected object and all children to half polycount.

Room: Sculpt
Action: Resample 50% on subtree
"""
from _utils.scene_api import SceneAPI
from _utils.mesh_utils import resample_to_half, ensure_surface_mode, cleanup_after_mesh_operation
from _utils.coat_ui_utils import show_message
import coat


def resample_element_half(el: coat.SceneElement) -> bool:
    """Resample a single element to 50%. Returns False to continue iteration."""
    if not el.isSculptObject():
        return False

    vol: coat.Volume = el.Volume()
    ensure_surface_mode(vol)
    
    current_polycount: int = vol.getPolycount()
    if current_polycount <= 0:
        return False

    el.selectOne()
    resample_to_half(current_polycount)

    return False  # Continue iteration


def main() -> None:
    """Resample current object and subtree to half polycount."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if not current:
        show_message("No object selected", 3000)
        return

    # Resample root element
    resample_element_half(current)

    # Resample all children
    current.iterateSubtree(resample_element_half)

    # Restore selection and cleanup
    current.selectOne()
    cleanup_after_mesh_operation()

    show_message("Subtree resampled to 50%", 3000)


main()
