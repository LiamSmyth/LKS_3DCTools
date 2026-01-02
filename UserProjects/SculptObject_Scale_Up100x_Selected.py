"""
Scale selected object up by 100x.

Room: Sculpt
Action: Apply 100.0 scale factor to selected object
"""
import coat

from _utils.object_utils import ObjectUtils
from _utils.coat_ui_utils import show_message


def main() -> None:
    """Scale current object up by 100x (scale factor 100.0)."""
    el: coat.SceneElement = coat.Scene.current()
    if not el:
        show_message("No object selected", 3000)
        return

    ObjectUtils.scale_selected_element(el, 100.0)
    show_message("Object scaled up 100x", 3000)


main()
