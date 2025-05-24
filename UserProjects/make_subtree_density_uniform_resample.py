"""
This script will iterate over a subtree of the selected sculpt object, subdividing or reducing the polycount of each
sub-object to match the polygon density of the reference object.

This is useful when you have used the split tool a lot and your subtree has become dense, or if you are 
trying to even out your triangle size before exporting to a game engine.

"""

import coat
import math

active_element: coat.SceneElement = coat.Scene.current()

print(f"Start Reduce: {active_element.name()} \n\n")


def calculate_target_polycount(reference_object: coat.SceneElement, target_object: coat.SceneElement) -> int:

    src_aabb: coat.boundbox = reference_object.Volume().calcWorldSpaceAABB()
    # Get the largest dimension of the source object
    # src_dimension = src_aabb.GetSize()[src_aabb.GetLargestAxis()]

    # Instead of using the largest axis, lets take the average of the axes
    src_size: coat.vec3 = src_aabb.GetSize()

    src_dimension = (src_size.x + src_size.y + src_size.z) / 3

    tgt_aabb: coat.boundbox = target_object.Volume().calcWorldSpaceAABB()
    # Get the largest dimension of the target object
    # tgt_dimension = tgt_aabb.GetSize()[tgt_aabb.GetLargestAxis()]

    # Instead of using the largest axis, lets take the average of the axes
    tgt_size: coat.vec3 = tgt_aabb.GetSize()

    tgt_dimension = (tgt_size.x + tgt_size.y + tgt_size.z) / 3

    # Polycount increases with the square of the scale increase. So a scale increase of s will result in a polycount increase of s^2
    scale_ratio: float = tgt_dimension / src_dimension
    polycount_ratio: float = scale_ratio ** 2

    src_polycount = reference_object.Volume().getPolycount()

    # This is the polycount of a box with the dimensions of the target object, and the polygon size of the source object
    target_polycount = math.floor(src_polycount * polycount_ratio)
    print("Calculating the target polycount for ", target_object.name())

    print(
        f"The largest axis of the source object is {src_dimension}, the largest axis of the target object is {tgt_dimension}")
    print(
        f"The scale factor is {scale_ratio}, the polycount ratio is {polycount_ratio}")

    return target_polycount


def adjust_polycount_to_uniform_size(obj: coat.SceneElement, ref_obj: coat.SceneElement):
    """
    This function will attempt to match the triangle size of an object to a reference object based on world
    scale. This method will always resample the object to match the target polycount.
    """
    obj.selectOne()
    if obj.isSculptObject():
        vol: coat.Volume = obj.Volume()
        if not vol.isSurface():
            vol.toSurface()

        tgt_polycount = calculate_target_polycount(
            ref_obj, obj)

        cur_polycount: int = vol.getPolycount()

        polycount_ratio = tgt_polycount / cur_polycount

        resample_ratio: float = math.sqrt(tgt_polycount / cur_polycount)

        # print(
        # 	f"Adjusting {obj.name()} from {cur_polycount} to {tgt_polycount} polys, a ratio of {polycount_ratio}")

        # If ratio is less than 1, we need to reduce the polycount. Use decimate to reduce polycount

        # elif resample_ratio > 1 and polycount_ratio < 3:

        def ui_command():
            coat.ui.setSliderValue(
                "$ResampleParams::ResamplingScale", resample_ratio)
            coat.ui.setEditBoxValue(
                "$ResampleParams::RequiredPolycount", tgt_polycount)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$Resample", ui_command)

        print(
            f"Resampled \" {obj.name()} \" from {cur_polycount} polys to {tgt_polycount} polys, a resample ratio of {resample_ratio} \n")

        return False


# Define your reference object here
# Placeholder for reference object
reference_element: coat.SceneElement = coat.Scene.current()
ref_vol: coat.Volume = reference_element.Volume()
ref_square = ref_vol.getSquare()
ref_polycount = ref_vol.getPolycount()
# Calculate average polygon size for the reference object
ref_avg_poly_size = ref_square / ref_polycount if ref_polycount else 0


# If size is 0, we can't proceed
if ref_avg_poly_size == 0:
    print("Reference object has no polygons")


def process_element(el: coat.SceneElement):
    adjust_polycount_to_uniform_size(el, reference_element)
    return False  # To continue iteration


if not ref_avg_poly_size == 0:
    active_element.iterateSubtree(process_element)
    active_element.selectOne()
