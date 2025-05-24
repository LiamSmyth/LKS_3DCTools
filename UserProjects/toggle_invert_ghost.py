
import coat
import math


def invert_ghost(el: coat.SceneElement):
    el.setGhost(not el.ghost())
    return False  # To continue iteration


scene_root: coat.SceneElement = coat.Scene.sculptRoot()

scene_root.iterateSubtree(invert_ghost)
