# Clone active element, parent it underneath original, expand with voxel extrude, and set to boolean intersection
import coat

active_element: coat.SceneElement = coat.Scene.current()

print("Creating Union volume for: ", active_element.name())

def create_union_volume(el: coat.SceneElement):
    # Clone the active element
    cloned_element : coat.SceneElement = el.duplicate()
    coat.io.step(4)
    if cloned_element.childCount() > 0:
        ## Remove all children of the cloned element
        cloned_element.removeSubtree()
        coat.io.step(4)
    cloned_element.selectOne()


    cloned_element.rename(el.name() + "_Union")
    coat.io.step(4)
    cloned_element.selectOne()
    coat.io.step(4)
    cloned_element.changeParent(el)
    cloned_element.clear()
    


    vo : coat.Volume = cloned_element.Volume()
    vo.assignLiveBooleans(3)

    print(f"Created union volume: {cloned_element.name()}")
# Create the intersection volume

create_union_volume(active_element)

print("union volume creation complete")