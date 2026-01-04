"""
Fill each part in the subtree with a random ID color.

Useful for generating ID maps for texture baking. Each object in the
subtree gets a unique random color.

Room: Sculpt
Action: Fill each subtree object with unique random color
"""
from _ops.SculptObject_IdColors import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Fill subtree with ID colors using operator."""
    op_main(scope=Scope.TREE)


main()
