"""
Hide all objects in scene.

Room: Sculpt
Action: Hide all objects in the sculpt tree
"""
from utils.action_base import action


@action
def main() -> None:
    """Hide all objects in sculpt tree."""
    from ops.SculptObject_Visibility import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.ALL, visible=False)


main()
