"""
Convert surface to voxels with 2x polycount (or back to surface).

Room: Sculpt
Action: Resample to 2x polycount and convert to voxels
"""
from ops.SculptObject_ModeConvert import main as op_main, ConvertMode
from utils.scope_utils import Scope


def main() -> None:
    """Toggle between surface and voxels with 2x polycount."""
    op_main(scope=Scope.CURRENT,
            mode=ConvertMode.RESAMPLE_VOXELIZE, multiplier=2.0)


main()
