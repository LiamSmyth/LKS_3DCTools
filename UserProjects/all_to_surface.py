
import coat
import math


def convert_to_surface(el: coat.SceneElement):
    el.selectOne()
    vol: coat.Volume = el.Volume()
    if not vol.isSurface():
        vol.toSurface()

    return False  # To continue iteration


active_element: coat.SceneElement = coat.Scene.current()

scene_root: coat.SceneElement = coat.Scene.sculptRoot()

scene_root.iterateSubtree(convert_to_surface)

active_element.selectOne()
