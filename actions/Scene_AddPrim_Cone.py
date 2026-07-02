"""
Add built-in Cone primitive to the sculpt scene.

Opens the parametric primitive tool and selects Cone.

Room: Sculpt
Action: Open primitive tool and activate Cone primitive
"""
from utils.action_base import action


@action
def main() -> None:
    from ops.Scene_AddPrimitive import add_builtin_primitive
    from utils.primitives_constants import CMD_PRIM_CONE
    add_builtin_primitive(CMD_PRIM_CONE, "Cone")


main()
