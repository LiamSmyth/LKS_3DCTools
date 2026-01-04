"""
Scale selected object up by 100x.

Room: Sculpt
Action: Apply 100x scale factor to selected object
"""
from ops.SculptObject_Scale import main as op_main
from utils.scope_utils import Scope


def main() -> None:
    """Scale current object up by 100x (scale factor 100.0)."""
    op_main(scope=Scope.CURRENT, scale_factor=100.0)


main()
