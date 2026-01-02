# Iterate over the sculpt tree, show the basic stats - square, volume
import coat
import math

active_element: coat.SceneElement = coat.Scene.current()

print("Start Reduce: ", active_element.name())


def reduce_element_half(el: coat.SceneElement):
    el.selectOne()
    if el.isSculptObject():
        vol: coat.Volume = el.Volume()
        if not vol.isSurface():
            vol.toSurface()

        ratio = 0.5
        cur_polycount: int = vol.getPolycount()
        tgt_poylcount: int = math.floor(cur_polycount * ratio)

        # Must produce the ui command ahead of time so that it can be passeed into the resample window
        def ui_command():
            coat.ui.setEditBoxValue(
                "$DecimationParams::ReducedPolycount", tgt_poylcount)
            coat.ui.setSliderValue(
                "$DecimationParams::ReductionPercent", ratio * 100.0)
            coat.ui.cmd("$DialogButton#1")

        # With the resmaple window, call ui_command (sets parms)
        coat.ui.cmd("$Decimate", ui_command)

        print("Resampled $s from $s polys to $s polys",
              [el.name(), cur_polycount, tgt_poylcount])

        return False


reduce_element_half(active_element)

active_element.iterateSubtree(reduce_element_half)

active_element.selectOne()

"""
// cmd - based script:
cmd("$DecimationParams::ReductionPercent");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$DecimationParams::ReductionPercent");


// cmd - based script:
cmd("$DecimationParams::ReducedPolycount");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$DecimationParams::ReducedPolycount");


"""
