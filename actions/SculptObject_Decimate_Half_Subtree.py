"""
Decimate selected object and all children to half polycount.

Room: Sculpt
Action: Decimate 50% on subtree
"""
from _ops.SculptObject_Decimate import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Decimate subtree to half polycount."""
    op_main(scope=Scope.TREE, reduction_percent=50.0)


main()


main()
