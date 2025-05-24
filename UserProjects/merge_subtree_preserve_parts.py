"""
Merge the subtree of the active element, preserving the parts of the elements in the subtree. in surface mode.

"""
import coat
import math


def process_element(el: coat.SceneElement):
    if not el.Volume().isSurface():
        el.Volume().toSurface()

    return False  # To continue iteration


def main():

    active_element: coat.SceneElement = coat.Scene.current()

    el: coat.SceneElement = coat.Scene.current()
    vol: coat.Volume = el.Volume()

    if not vol.isSurface():
        vol.toSurface()

    el.iterateSubtree(process_element)

    active_element.selectOne()
    active_element.mergeSubtree()


main()
