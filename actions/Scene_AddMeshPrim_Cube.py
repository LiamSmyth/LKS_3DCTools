"""
Add Cube mesh primitive to the sculpt scene.

Loads the SculptModel .obj file via the Merge tool.

Room: Sculpt
Action: Open Merge tool and select Cube.obj
"""
from utils.action_base import action


@action
def main() -> None:
    from ops.Scene_AddPrimitive import add_mesh_primitive
    from utils.primitives_constants import CMD_MESH_CUBE
    add_mesh_primitive(CMD_MESH_CUBE, "Cube")


main()
