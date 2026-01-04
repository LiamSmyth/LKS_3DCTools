"""
Resample subtree objects to match the polygon density of the selected object.

Useful for evening out triangle sizes after using split tools, or preparing
for export with uniform mesh density.

Room: Sculpt
Action: Resamples all children to match parent's polygon density
"""
import coat
from _utils.scene_api import SceneAPI
from _utils.Volume_density_utils import resample_to_match_density
from _utils.coat_ui_utils import show_message, show_error


def main() -> None:
    """Resample all subtree objects to match reference density."""
    reference: coat.SceneElement | None = SceneAPI.get_current_element()
    if not reference:
        show_error("No object selected", 2000)
        return

    if not reference.isSculptObject():
        show_error("Selected element is not a sculpt object", 2000)
        return

    ref_vol: coat.Volume = reference.Volume()
    ref_polycount: int = ref_vol.getPolycount()

    if ref_polycount <= 0:
        show_error("Reference object has no polygons", 2000)
        return

    # Collect subtree elements (excluding the reference itself)
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(reference)
    children: list[coat.SceneElement] = [
        el for el in subtree
        if el != reference and el.isSculptObject()
    ]

    if not children:
        show_message("No child objects to resample", 2000)
        return

    # Process each child
    count: int = 0
    for child in children:
        resample_to_match_density(child, ref_vol)
        count += 1

    # Restore selection
    reference.selectOne()

    show_message(f"Resampled {count} objects to uniform density", 2000)


main()
