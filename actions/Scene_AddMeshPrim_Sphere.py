"""
Add Sphere mesh primitive to the sculpt scene.

Loads the SculptModel .obj file via the Merge tool.

Room: Sculpt
Action: Open Merge tool and select Sphere.obj
"""
from utils.action_base import action


@action
def main() -> None:
    from ops.Scene_AddPrimitive import add_mesh_primitive
    from utils.primitives_constants import CMD_MESH_SPHERE
    add_mesh_primitive(CMD_MESH_SPHERE, "Sphere")


main()
