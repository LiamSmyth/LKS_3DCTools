
import coat
import math

RESAMPLE_SCALE = 4.0


def remesh_resymm_safe(el: coat.SceneElement):
    coat.SceneElement.selectOne(el)

    if not el.isSculptObject():
        return False

    el.selectOne()

    vol: coat.Volume = el.Volume()
    target_polycount: int = vol.getPolycount()

    def remesh_command():
        # The resampling scale should preserve details
        coat.ui.setSliderValue(
            "$ResampleParams::ResamplingScale", RESAMPLE_SCALE)
        coat.ui.cmd("$DialogButton#1")

    print(f"Remeshing {el.name()} to {target_polycount} polys")
    if not vol.isVoxelized():
        coat.ui.cmd("$Resample", remesh_command)
        vol.toVoxels()

    coat.ui.cmd("$MakeSymm")

    vol.toSurface()
    new_polycount = vol.getPolycount()

    needs_decimate = new_polycount > target_polycount

    while needs_decimate:

        # The reduction percent is how much to _reduce_ by so we need
        # the difference between 100% and the new polycount percentage

        # The new polycount could be 2.5x the target polycount
        new_polycount_ratio: int = (new_polycount / target_polycount)
        # We want to get down to 1.0 ratio, so the reduction ratio is the inverse
        reduction_ratio: float = 1.0 / new_polycount_ratio

        # Then to convert to a percentage
        reduction_percent: float = 100 - (reduction_ratio * 100.0)

        print(
            f"Reducing to {target_polycount}, or {reduction_percent} % of the original polycount")

        def decimate_command():
            coat.ui.wait('$DecimationParams::ReducedPolycount', 1)
            coat.ui.setEditBoxValue(
                "$DecimationParams::ReducedPolycount", target_polycount)
            coat.ui.setSliderValue(
                "$DecimationParams::ReductionPercent", reduction_percent)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$Decimate", decimate_command)
        new_polycount = vol.getPolycount()
        lay_0_indx = coat.Scene.getLayer("Layer 0")
        coat.Scene.setActiveLayer(lay_0_indx)
        coat.Scene.removeEmptyLayers()

        # Check if the new polycount is still too high
        needs_decimate = new_polycount > target_polycount + 1000
        if needs_decimate:
            print("Decimate failed, retrying")
        else:
            print("Decimate succeeded")

    # todo: get selected and iterate over them


active_element: coat.SceneElement = coat.Scene.current()

active_element.iterateSubtree(remesh_resymm_safe)
remesh_resymm_safe(active_element)

lay_0_indx = coat.Scene.getLayer("Layer 0")
coat.Scene.setActiveLayer(lay_0_indx)
coat.Scene.removeEmptyLayers()
coat.SceneElement.visi
