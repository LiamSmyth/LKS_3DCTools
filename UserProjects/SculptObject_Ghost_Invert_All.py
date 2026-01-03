"""
Invert ghost state for all objects in scene.

Room: Sculpt
Action: Invert ghost state (ghosted→unghosted, unghosted→ghosted)
"""
from _ops.SculptObject_SetGhost import main as op_main, GhostMode
from _utils.scope_utils import Scope


def main() -> None:
    """Invert ghost state for all objects."""
    op_main(scope=Scope.ALL, mode=GhostMode.INVERT)


main()
