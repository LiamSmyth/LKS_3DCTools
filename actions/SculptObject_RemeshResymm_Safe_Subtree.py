"""
Safely remesh and re-symmetrize all objects in the selected subtree.

Applies the safe remesh+symmetrize process to each sculpt object in the
subtree, preserving original polycounts.

Room: Sculpt
Action: Remesh, symmetrize all objects in subtree
"""
from utils.action_base import action


@action
def main() -> None:
    """Remesh and symmetrize all objects in subtree."""
    from ops.SculptObject_RemeshResymm import main as op_main
    from utils.scope_utils import Scope

    op_main(scope=Scope.TREE)


main()
