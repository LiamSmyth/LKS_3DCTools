"""
Toggle visibility for selected object and all children.

Room: Sculpt
Action: Toggle visibility on subtree (invert current state)
"""
from ops.SculptObject_Visibility import main as op_main, VisibilityMode
from utils.scope_utils import Scope


def main() -> None:
    """Toggle visibility state for current element and its subtree."""
    op_main(scope=Scope.TREE, mode=VisibilityMode.INVERT)


main()
