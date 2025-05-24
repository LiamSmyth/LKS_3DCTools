"""
Remesh a surface object while preserving its parts.
A single scene element will first be split to

"""
import coat
import math
import random

MIN_COLOR = 0


def fill_element_with_random_color(el: coat.SceneElement):

    el.selectOne()
    # Isolate visibility on the current voxlayer

    el.setVisibility(True)

    print(f"Setting Color: {el.name()} \n\n")

    r = random.uniform(MIN_COLOR, 255)
    g = random.uniform(MIN_COLOR, 255)
    b = random.uniform(MIN_COLOR, 255)

    coat.Volume.color(r, g, b)

    coat.ui.cmd("$FILLLAYER1")

    el.setVisibility(False)

    return False


def enable_visibility(el: coat.SceneElement):
    el.selectOne()
    el.setVisibility(True)
    return False


def disable_visibility(el: coat.SceneElement):
    el.selectOne()
    el.setVisibility(False)
    return False


def main():

    active_element: coat.SceneElement = coat.Scene.current()

    print(f"Setting Color: {active_element.name()} \n\n")

    original_pen_depth = coat.ui.getSliderValue("$PEN_DEPTH")
    coat.ui.setSliderValue("$PEN_DEPTH", 0)
    layer1_id = coat.Scene.getLayer("IDMap")
    coat.Scene.setActiveLayer(layer1_id)
    coat.Scene.setLayerDepthOpacity(layer1_id, 0)

    scene_root: coat.sceneElement = coat.Scene.sculptRoot()

    scene_root.iterateSubtree(disable_visibility)

    fill_element_with_random_color(active_element)

    active_element.iterateSubtree(fill_element_with_random_color)

    scene_root.iterateSubtree(enable_visibility)

    active_element.selectOne()

    coat.Scene.setActiveLayer(coat.Scene.getLayer("Layer 0"))

    coat.ui.setSliderValue("$PEN_DEPTH", original_pen_depth)


main()
