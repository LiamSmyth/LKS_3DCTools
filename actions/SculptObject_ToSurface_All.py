"""
Convert all sculpt objects to surface mode.

Room: Sculpt
Action: Convert all voxel objects to surface mode
"""
from utils.action_base import action


@action
def main() -> None:
    """Convert all sculpt objects to surface mode."""
    from ops.SculptObject_ModeConvert import main as op_main, ConvertMode
    from utils.scope_utils import Scope

    op_main(scope=Scope.ALL, mode=ConvertMode.TO_SURFACE)




main()
