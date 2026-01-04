"""
Decimate selected object to 50% of its original polycount.

Room: Sculpt
Action: Decimate 50% on selected object
"""
from _ops.SculptObject_Decimate import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Decimate selected object to half its polycount."""
    op_main(scope=Scope.CURRENT, reduction_percent=50.0)


main()
