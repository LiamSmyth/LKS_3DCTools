"""
Add FFD Blob (sphere + FFD) to the sculpt scene.

Opens the parametric primitive tool and selects Blob FFD shape.

Room: Sculpt
Action: Open primitive tool and activate Blob FFD primitive
"""
from utils.action_base import action


@action
def main() -> None:
    from ops.Scene_AddPrimitive import add_ffd_primitive
    from utils.primitives_constants import CMD_FFD_BLOB
    add_ffd_primitive(CMD_FFD_BLOB, "FFD Blob")


main()
