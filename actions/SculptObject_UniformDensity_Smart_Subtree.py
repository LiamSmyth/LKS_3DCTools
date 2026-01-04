"""
Smart uniform density adjustment for subtree using subdivide/decimate.

Unlike resample-based density matching, this method uses:
- Subdivision for increases > 2x (better shape preservation)
- Decimation for decreases
- Skip for objects close to target

This prevents meshes from being merged and preserves shape better.

Room: Sculpt
Action: Subdivide or decimate children to match parent's polygon density
"""
import coat
from utils.scene_api import SceneAPI
from utils.Volume_density_utils import smart_match_density
from utils.coat_ui_utils import show_message, show_error


def main() -> None:
    """Smart density matching for all subtree objects."""
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
        show_message("No child objects to process", 2000)
        return

    # Process each child
    subdivided: int = 0
    decimated: int = 0
    skipped: int = 0

    for child in children:
        result: str = smart_match_density(child, ref_vol)
        if result == "subdivided":
            subdivided += 1
        elif result == "decimated":
            decimated += 1
        else:
            skipped += 1

    # Restore selection
    reference.selectOne()

    show_message(
        f"Done: {subdivided} subdivided, {decimated} decimated, {skipped} skipped",
        3000
    )


main()
