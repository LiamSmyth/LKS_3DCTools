
import coat
import math


def set_ghost(el: coat.SceneElement):
    el.selectOne()
    el.setGhost(new_ghost)

    # coat.ui.cmd("$Decimate", decimate_ui)
    return False  # To continue iteration


active_element: coat.SceneElement = coat.Scene.current()
ghost = active_element.ghost()
new_ghost = not ghost

set_ghost(active_element)
active_element.iterateSubtree(set_ghost)

coat.SceneElement.selectOne(active_element)
