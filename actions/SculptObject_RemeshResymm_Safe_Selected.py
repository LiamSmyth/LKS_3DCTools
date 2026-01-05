"""
Safely remesh and re-symmetrize the selected sculpt object.

Preserves the original polycount by resampling first, converting to voxels,
making symmetrical, converting back to surface, then decimating if needed.

Room: Sculpt
Action: Remesh, symmetrize, and restore polycount on selected object
"""
from utils.action_base import action


@action
def main() -> None:
    """Remesh and symmetrize the currently selected object."""
    from ops.SculptObject_RemeshResymm import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT)


main()
