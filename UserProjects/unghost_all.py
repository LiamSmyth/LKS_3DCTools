import coat
import math


def set_ghost(el: coat.SceneElement):
    el.selectOne()
    el.setGhost(False)
    return False  # To continue iteration


coat.Scene.sculptRoot().iterateSubtree(set_ghost)

active_element: coat.SceneElement = coat.Scene.current()
coat.SceneElement.selectOne(active_element)

# Show summary message to user
coat.ui.showInfoMessage("All objects unghosted", 3000)
