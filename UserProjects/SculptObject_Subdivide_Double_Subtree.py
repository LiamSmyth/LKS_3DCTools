"""
Subdivide selected object and all children (double polycount).

Room: Sculpt
Action: Subdivide subtree (approximately 2x polycount)
"""
from _ops.SculptObject_Subdivide import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Subdivide current object and subtree."""
    op_main(scope=Scope.TREE, subdivisions=1)


main()
