"""
Convert all sculpt objects to voxel mode.

Room: Sculpt
Action: Convert all surface objects to voxel mode
"""
from _ops.SculptObject_ModeConvert import main as op_main, ConvertMode
from _utils.scope_utils import Scope


def main() -> None:
    """Convert all sculpt objects to voxel mode."""
    op_main(scope=Scope.ALL, mode=ConvertMode.TO_VOXELS)


main()
