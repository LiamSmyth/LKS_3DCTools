"""
Scale selected object down by 100x.

Room: Sculpt
Action: Apply 0.01 scale factor to selected object
"""
from ops.SculptObject_Scale import main as op_main
from utils.scope_utils import Scope


def main() -> None:
    """Scale current object down by 100x (scale factor 0.01)."""
    op_main(scope=Scope.CURRENT, scale_factor=0.01)


main()
