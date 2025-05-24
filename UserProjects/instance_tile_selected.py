# This example demonstrate adding prumitives into the mesh, then we merge the mesh into the scene
import coat
from coat import vec3
from coat import Mesh

# add the new sculpt volume named "meshes"


####################
# Base constants for the tiling plane - could later make these set with initialization popup menu
####################
BASE_SIZE: int = 64
THICKNESS: int = 16
border: int = BASE_SIZE // 4
size = BASE_SIZE + border


####################
# Prepare base plane
####################
# Disable symmetry so we don't start with a duplicated plane
coat.ui.cmd("$SYMMETRY")
coat.ui.setBoolValue("$SymmetryParams::EnableSymmetry", False)

root: coat.SceneElement = coat.Scene.current()

# sculpt_plane: coat.SceneElement = root.addChild(
#     f"Center Plane ({BASE_SIZE}x{BASE_SIZE}) ")
# sculpt_plane_volume = sculpt_plane.Volume()
# sculpt_plane_volume.toSurface()

# # mesh: coat.Mesh = coat.Mesh.box(size=vec3(size, THICKNESS, size), yAxis=vec3(
# #     0, 1, 0), center=vec3(0, -float(THICKNESS) / 2.0, 0), detail_size=1, fillet=0)

# mesh = Mesh.plane(center=vec3(0, 0, 0), sizeX=size, sizeY=size,
#                   divisionsX=size, divisionsY=size, xAxis=vec3.AxisX, yAxis=vec3.AxisZ)

# sculpt_plane_volume.mergeMesh(mesh)


####################
# Duplicate the sculpt plane and move it to the instance locations
####################

# Make vec3's for top-left, top, top-right, left, right, bottom-left, bottom, bottom-right
instance_locations = [
    vec3(-BASE_SIZE, 0, BASE_SIZE), vec3(0, 0,
                                         BASE_SIZE), vec3(BASE_SIZE, 0, BASE_SIZE),
    vec3(-BASE_SIZE, 0, 0), vec3(BASE_SIZE, 0, 0),
    vec3(-BASE_SIZE, 0, -BASE_SIZE), vec3(0, 0, -
                                          BASE_SIZE), vec3(BASE_SIZE, 0, -BASE_SIZE)
]


def duplicateAsInstance(src: coat.SceneElement, loc: vec3) -> coat.SceneElement:

    inst: coat.SceneElement = src.duplicateAsInstance()
    inst_m: coat.mat4 = inst.getTransform()
    inst_m.SetTranslation(loc)
    inst.setTransform(inst_m)
    inst.rename(f"Instance {loc.x}, {loc.y}, {loc.z}")
    # inst.setGhost(True)

    return inst


instances: [coat.SceneElement] = []

for loc in instance_locations:
    instances.append(duplicateAsInstance(root, loc))

for inst in instances:
    inst: coat.SceneElement = inst
    inst.changeParent(root)

# Select the sculpt plane
root.selectOne()


####################
# Set symmetry mode to match the instance plane
####################

# coat.ui.cmd("$SYMMETRY")
# coat.ui.setBoolValue("$SymmetryParams::EnableSymmetry", True)
# coat.ui.cmd("$COMBOBOX_SymmetryTypeTranslation")
# coat.ui.setSliderValue("$SymmetryParams::tNumX", 1)
# coat.ui.setSliderValue("$SymmetryParams::tNumY", 0)
# coat.ui.setSliderValue("$SymmetryParams::tNumZ", 1)
# coat.ui.setSliderValue("$SymmetryParams::tStepX", float(BASE_SIZE))
# coat.ui.setSliderValue("$SymmetryParams::tStepZ", float(BASE_SIZE))
# coat.ui.cmd("$COMBOBOX_CoordSystemXYZXYZ_axis")


"""1
// cmd - based script:
cmd("$SymmetryParams::tStepX");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$SymmetryParams::tStepX");

// cmd - based script:
cmd("$SymmetryParams::tStepX");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$SymmetryParams::tStepX");
// cmd - based script:
cmd("$COMBOBOX_CoordSystemXYZXYZ_axis");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$COMBOBOX_CoordSystemXYZXYZ_axis");


// cmd - based script:
cmd("$SymmetryParams::tNumY");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$SymmetryParams::tNumY");

// cmd - based script:
cmd("$SymmetryParams::EnableSymmetry");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$SymmetryParams::EnableSymmetry");

// cmd - based script:
cmd("ViewGizmo");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("ViewGizmo");
// cmd - based script:
cmd("COMBOBOX_SymmetryType");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("COMBOBOX_SymmetryType");
// cmd - based script:
cmd("$COMBOBOX_SymmetryTypeXYZ_Mirror");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$COMBOBOX_SymmetryTypeXYZ_Mirror");
// cmd - based script:
cmd("$COMBOBOX_SymmetryTypeTranslation");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$COMBOBOX_SymmetryTypeTranslation");

"""
