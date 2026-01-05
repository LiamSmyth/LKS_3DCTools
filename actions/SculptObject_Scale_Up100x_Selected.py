"""
Scale selected object up by 100x.

Room: Sculpt
Action: Apply 100x scale factor to selected object
"""
from utils.action_base import action


@action
def main() -> None:
    """Scale current object up by 100x (scale factor 100.0)."""
    from ops.SculptObject_Scale import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT, scale_factor=100.0)




main()
