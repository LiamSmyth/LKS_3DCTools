"""
Toggle Decimate 16X proxy mode for selected object.

Room: Sculpt
Action: Toggle 16X decimation proxy for faster viewport performance
"""
from ops.SculptObject_Proxy import main as op_main
from utils.scope_utils import Scope
from utils.Volume_proxy_utils import ProxyType


def main() -> None:
    """Toggle Decimate 16X proxy on selected object."""
    op_main(scope=Scope.CURRENT, proxy_type=ProxyType.DECIMATE_16X)


main()
