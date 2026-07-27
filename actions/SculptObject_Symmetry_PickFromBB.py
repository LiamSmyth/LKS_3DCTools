"""
Set symmetry origin from selected object bounding box.

Room: Sculpt
Action: Open symmetry pane and pick pivot from object BB ($SymmetryParams::PickFromBB)
"""
from utils.action_base import action


@action
def main() -> None:
    """Set symmetry pivot to selected object bounding-box center."""
    from utils.symmetry_utils import pick_symmetry_from_bbox

    pick_symmetry_from_bbox()


main()
