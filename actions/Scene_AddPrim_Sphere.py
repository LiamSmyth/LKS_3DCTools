"""
Add built-in Sphere primitive to the sculpt scene.

Opens the parametric primitive tool and selects Sphere.

Room: Sculpt
Action: Open primitive tool and activate Sphere primitive
"""
from utils.action_base import action


@action
def main() -> None:
    from ops.Scene_AddPrimitive import add_builtin_primitive
    from utils.primitives_constants import CMD_PRIM_SPHERE
    add_builtin_primitive(CMD_PRIM_SPHERE, "Sphere")


main()
