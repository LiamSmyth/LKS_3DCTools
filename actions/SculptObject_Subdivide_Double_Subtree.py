"""
Subdivide selected object and all children (double polycount).

Room: Sculpt
Action: Subdivide subtree (approximately 2x polycount)
"""
from utils.action_base import action


@action
def main() -> None:
    """Subdivide current object and subtree."""
    from ops.SculptObject_Subdivide import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.TREE, subdivisions=1)




main()
