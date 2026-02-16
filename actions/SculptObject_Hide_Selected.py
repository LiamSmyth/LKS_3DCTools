"""
Hide selected object.

Room: Sculpt
Action: Hide the currently selected object (makes it invisible)
"""
from utils.action_base import action


@action
def main() -> None:
    """Hide selected object."""
    from ops.SculptObject_Visibility import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT, visible=False)


main()
