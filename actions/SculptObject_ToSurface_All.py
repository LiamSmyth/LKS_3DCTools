"""
Convert all sculpt objects to surface mode.

Room: Sculpt
Action: Convert all voxel objects to surface mode
"""
from ops.SculptObject_ModeConvert import main as op_main, ConvertMode
from utils.scope_utils import Scope


def main() -> None:
    """Convert all sculpt objects to surface mode."""
    op_main(scope=Scope.ALL, mode=ConvertMode.TO_SURFACE)


main()
