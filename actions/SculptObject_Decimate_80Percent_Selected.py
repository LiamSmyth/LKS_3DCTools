"""
Decimate selected object to 20% of its original polycount (80% reduction).

Room: Sculpt
Action: Decimate 80% on selected object
"""
from utils.action_base import action


@action
def main() -> None:
    """Decimate selected object by 80% (to 20% of original polycount)."""
    from ops.SculptObject_Decimate import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT, reduction_percent=80.0)


main()
