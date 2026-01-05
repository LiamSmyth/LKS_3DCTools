"""
Toggle visibility for selected object and all children.

Room: Sculpt
Action: Toggle visibility on subtree (invert current state)
"""
from utils.action_base import action


@action
def main() -> None:
    """Toggle visibility state for current element and its subtree."""
    from ops.SculptObject_Visibility import main as op_main, VisibilityMode
    from utils.scope_utils import Scope

    op_main(scope=Scope.TREE, mode=VisibilityMode.INVERT)




main()
