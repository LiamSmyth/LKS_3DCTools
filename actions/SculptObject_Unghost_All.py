"""
Unghost all objects in scene.

Room: Sculpt
Action: Remove ghost state from all objects
"""
from _ops.SculptObject_SetGhost import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Unghost all objects in sculpt tree."""
    op_main(scope=Scope.ALL, ghost=False)


main()
