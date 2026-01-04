"""
Toggle ghost state for selected object and all children.

Room: Sculpt
Action: Toggle ghost on subtree (invert current state)
"""
from ops.SculptObject_SetGhost import main as op_main, GhostMode
from utils.scope_utils import Scope


def main() -> None:
    """Toggle ghost state for current element and its subtree."""
    op_main(scope=Scope.TREE, mode=GhostMode.INVERT)


main()
