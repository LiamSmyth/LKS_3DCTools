"""
Merge subtree while preserving parts in surface mode.

Converts all objects in the subtree to surface mode (collapsing boolean trees),
then merges them together while preserving their separate part identities.

Room: Sculpt
Action: Convert all to surface, then merge subtree
"""
import coat
from utils.scene_api import SceneAPI
from utils.coat_ui_utils import show_message, show_error


def prepare_element_for_merge(element: coat.SceneElement) -> None:
    """Convert element to surface mode, collapsing any boolean tree."""
    vol: coat.Volume = element.Volume()

    if not vol.isSurface():
        vol.collapseBollTree()
        vol.toSurface()


def main() -> None:
    """Merge subtree preserving parts in surface mode."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()

    if not current:
        show_error("No object selected", 2000)
        return

    if not current.isSculptObject():
        show_error("Selected element is not a sculpt object", 2000)
        return

    # Convert root element to surface
    prepare_element_for_merge(current)

    # Convert all children to surface
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(current)
    count: int = 0
    for el in subtree:
        if el.isSculptObject():
            prepare_element_for_merge(el)
            count += 1

    # Merge the subtree
    current.selectOne()
    current.mergeSubtree()

    show_message(f"Merged {count} objects preserving parts", 2000)


main()
