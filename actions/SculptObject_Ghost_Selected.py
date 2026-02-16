"""
Ghost selected object.

Room: Sculpt
Action: Ghost the currently selected object (makes it semi-transparent)
"""
from utils.action_base import action


@action
def main() -> None:
    """Ghost selected object."""
    from ops.SculptObject_SetGhost import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.CURRENT, ghost=True)


main()
