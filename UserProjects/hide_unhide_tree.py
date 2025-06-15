import coat
import math

print("Hiding and unhiding the scene tree elements")
def set_hidden(el: coat.SceneElement):
    print(f"Setting visibility of {el.name()} to {el.visible()}")
    el.selectOne()
    el.setVisibility(new_hide)
    return False  # To continue iteration

scene_root = coat.Scene.sculptRoot()
scene_root.selectOne()
new_hide = not scene_root.visible()
print(f"Scene root visibility: {scene_root.visible()}, new visibility: {new_hide}")
print("Collecting selected elements")
selection = coat.SceneElement.collectSelected(scene_root)
active: coat.SceneElement = coat.Scene.current()
print(f"Active element: {active.name()}")
print(f"Selected elements: {[el.name() for el in selection]}")  


print(f"Setting visibility of scene root to {new_hide}")
set_hidden(scene_root)
scene_root.iterateSubtree(set_hidden)

for el in selection:
    coat.SceneElement.select(el)

active.select()