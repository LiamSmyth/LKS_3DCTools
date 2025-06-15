# Clone active element, parent it underneath original, expand with voxel extrude, and set to boolean intersection
import coat

active_element: coat.SceneElement = coat.Scene.current()

print("Creating intersection volume for: ", active_element.name())

def create_intersection_volume(el: coat.SceneElement):
    # Clone the active element
    cloned_element : coat.SceneElement = el.duplicate()
    coat.io.step(4)
    if cloned_element.childCount() > 0:
        ## Remove all children of the cloned element
        cloned_element.removeSubtree()
        coat.io.step(4)
    cloned_element.selectOne()


    cloned_element.rename(el.name() + "_Intersect")
    coat.io.step(4)
    cloned_element.selectOne()
    coat.io.step(4)
    cloned_element.changeParent(el)
    
    
    def extrude_cmd():
        # Set the extrude parameters
        coat.io.step(4)
        coat.ui.setSliderValue("$ExtrudeParams::Extrusion", 0.2)
        coat.io.step(4)
        coat.ui.cmd("$DialogButton#1")
    # Expand the cloned element using voxel extrude
    # This uses the UI command for voxel extrude operation
    coat.ui.cmd("$ExtrudeVO", extrude_cmd)
    
    vo : coat.Volume = cloned_element.Volume()
    vo.assignLiveBooleans(2)

    print(f"Created intersection volume: {cloned_element.name()}")
# Create the intersection volume

create_intersection_volume(active_element)

print("Intersection volume creation complete")