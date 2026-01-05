"""
Convert all sculpt objects to voxel mode.

Room: Sculpt
Action: Convert all surface objects to voxel mode
"""
from utils.action_base import action


@action
def main() -> None:
    """Convert all sculpt objects to voxel mode."""
    from ops.SculptObject_ModeConvert import main as op_main, ConvertMode
    from utils.scope_utils import Scope

    op_main(scope=Scope.ALL, mode=ConvertMode.TO_VOXELS)




main()
