"""
Remesh a surface object while preserving its parts.
A single scene element will first be split to 

"""
import coat
import math

REMESH_RATIO = 4  # A remesh ratio of 4 will preserve most details usually

active_element: coat.SceneElement = coat.Scene.current()

print(f"Start Reduce: {active_element.name()} \n\n")


def remesh_element(el: coat.SceneElement):

    el.selectOne()
    if el.isSculptObject():
        vol: coat.Volume = el.Volume()
        if not vol.isSurface():
            vol.toSurface()

        cur_polycount: int = vol.getPolycount()
        tgt_poylcount: int = math.floor(cur_polycount * REMESH_RATIO)

        # Must produce the ui command ahead of time so that it can be passeed into the resample window
        def resample_command():
            coat.ui.setEditBoxValue(
                "$ResampleParams::RequiredPolycount", tgt_poylcount)
            coat.ui.setSliderValue(
                "$ResampleParams::ResamplingScale", REMESH_RATIO)
            coat.ui.cmd("$DialogButton#1")

        # With the resmaple window, call ui_command (sets parms)
        coat.ui.cmd("$Resample", resample_command)

        print("Resampled $s from $s polys to $s polys",
              [el.name(), cur_polycount, tgt_poylcount])

        return False


def process_element(_el: coat.SceneElement):
    _el.Volume().toVoxels()
    # _el.Volume().toSurface()
    return False  # To continue iteration


def main():
    el: coat.SceneElement = coat.Scene.current()

    def decompose_ui():
        coat.ui.cmd("$DialogButton#1")

    # Opens a modal so we have to pass in a function to close it
    coat.ui.cmd("$Decompose", decompose_ui)

    active_element.iterateSubtree(remesh_element)

    active_element.selectOne()

    vol: coat.Volume = el.Volume()
    if not vol.isSurface():
        vol.toSurface()

    vol.toVoxels()
    vol.toSurface()

    active_element.mergeSubtree()
    coat.ui.cmd("$ToGlobalSpace")


main()
