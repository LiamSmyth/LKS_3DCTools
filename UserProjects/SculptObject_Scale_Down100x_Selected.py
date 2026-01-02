"""
Scale selected object down by 100x.

Room: Sculpt
Action: Apply 0.01 scale factor to selected object
"""
import coat

from _utils.object_utils import ObjectUtils
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Scale current object down by 100x (scale factor 0.01)."""
    el: coat.SceneElement = coat.Scene.current()
    if not el:
        show_message("No object selected", 3000)
        return

    ObjectUtils.scale_selected_element(el, 0.01)
    show_message("Object scaled down 100x", 3000)


main()
