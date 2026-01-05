"""
Unghost all objects in scene.

Room: Sculpt
Action: Remove ghost state from all objects
"""
from utils.action_base import action


@action
def main() -> None:
    """Unghost all objects in sculpt tree."""
    from ops.SculptObject_SetGhost import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.ALL, ghost=False)




main()
