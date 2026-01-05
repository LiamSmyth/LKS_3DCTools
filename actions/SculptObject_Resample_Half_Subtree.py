"""
Resample selected object and all children to half polycount.

Room: Sculpt
Action: Resample 50% on subtree
"""
from utils.action_base import action


@action
def main() -> None:
    """Resample current object and subtree to half polycount."""
    from ops.SculptObject_Resample import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.TREE, use_half=True)




main()
