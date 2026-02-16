"""
Show selected object.

Room: Sculpt
Action: Show the currently selected object (makes it visible)
"""
from utils.action_base import action


@action
def main() -> None:
    """Show selected object."""
    from ops.SculptObject_Visibility import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT, visible=True)


main()
