"""
Set live boolean mode to UNION on selected object.

Sets the live boolean UNION flag on the currently selected sculpt object.
Does NOT create a new child — use NewVoxBool for that.

Room: Sculpt
Action: Assign live bool UNION mode to selected element
"""
from utils.action_base import action


@action
def main() -> None:
    """Set live boolean mode to UNION on the current element."""
    from ops.SculptObject_LiveBool import main as op_main
    from utils.SceneElement_boolean_utils import BooleanMode
    from utils.scope_utils import Scope

    op_main(mode=BooleanMode.UNION, scope=Scope.CURRENT)


main()
