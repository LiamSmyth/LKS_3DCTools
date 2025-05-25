# Iterate over the sculpt tree, show the basic stats - square, volume
import coat
import math

active_element: coat.SceneElement = coat.Scene.current()

print("Start Subdivide: ", active_element.name())


def double_polycount(el: coat.SceneElement):
    el.selectOne()
    if el.isSculptObject():
        vol: coat.Volume = el.Volume()
        if not vol.isSurface():
            vol.toSurface()

        ratio = 2.0
        cur_polycount: int = vol.getPolycount()
        tgt_poylcount: int = math.floor(cur_polycount * ratio)

        coat.ui.cmd("$VoxTreeBranch.IncRes_HINT.Root")

        print("Divicded $s from $s polys to $s polys",
              [el.name(), cur_polycount, tgt_poylcount])

        return False


double_polycount(active_element)

active_element.iterateSubtree(double_polycount)

active_element.selectOne()

# Show summary message to user
coat.ui.showInfoMessage(
    "Subtree subdivision complete (doubled polycount)", 3000)
