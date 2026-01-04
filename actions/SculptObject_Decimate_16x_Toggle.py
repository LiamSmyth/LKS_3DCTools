"""
Toggle 16x decimation proxy for selected object.

Room: Sculpt
Action: Toggle 16x decimation cache (proxy mode)
"""
from _ops.SculptObject_Decimate import main as op_main
from _utils.scope_utils import Scope


def main() -> None:
    """Toggle 16x decimation proxy."""
    op_main(scope=Scope.CURRENT, use_16x=True)


main()
