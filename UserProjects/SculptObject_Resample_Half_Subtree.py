"""
Resample selected object and all children to half polycount.

Room: Sculpt
Action: Resample 50% on subtree
"""
from _ops.SculptObject_Resample import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Resample current object and subtree to half polycount."""
    op_main(scope=Scope.TREE, use_half=True)


main()
