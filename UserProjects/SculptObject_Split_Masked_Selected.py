# There is no built in way to take a masked part of geomtery and split it off into a new mesh without several ui buttons.
# This script will try to split any masked geo in one step, map this script to a shortcut
# by LKS / Claude
"""
Split Frozen Area

This script takes the current object's frozen area and splits it into a new object.
It uses UI commands to hide the frozen area and then separate the hidden geometry.
The new objects will be placed at the same hierarchy level as the original object.
"""
import coat


def split_frozen_area():
    """Split the frozen area of the current object into a new object"""
    # Get the current object
    current_object: coat.SceneElement = coat.Scene.current()

    if not current_object:
        coat.ui.showInfoMessage("No object selected", 3000)
        return

    # Cache the original parent and existing children
    original_parent: coat.SceneElement = current_object.parent()
    existing_children: list = []

    # Store references to existing children
    for i in range(current_object.parent().childCount()):
        existing_children.append(current_object.parent().child(i))
        print("Existing child:", existing_children[-1].name())

    # Ensure the object is selected
    current_object.selectOne()

    if current_object.isSculptObject():
        vol: coat.Volume = current_object.Volume()
        if not vol.isSurface():
            vol.toSurface()

    print("Splitting frozen area from object:", current_object.name())

    # First, hide the frozen area using UI command
    coat.ui.cmd("$HideFrozenArea")

    # Then separate the hidden geometry into a new object
    coat.ui.cmd("$SeparateHidden")
    coat.io.step(4)
    vol.closeHoles(8192)

    coat.io.step(4)

    # Find any new children that were created by the split operation
    new_children: list = []
    current_child_count = current_object.parent().childCount()

    for i in range(current_child_count):
        print("Current child count:", current_child_count)
        child = current_object.parent().child(i)
        # If this child wasn't in our original list, it's a new one
        if child not in existing_children:
            new_children.append(child)
            print("New child created:", child.name())

    # Close all of the holes for the source object and the new children
    all_objects = [current_object] + new_children
    for obj in all_objects:
        if obj.isSculptObject():
            vol: coat.Volume = obj.Volume()
            if vol.isSurface():
                obj.selectOne()
                coat.io.step(4)
                vol.closeHoles(8192)
                # Prepare ui command to smooth object

                def smooth_command():
                    coat.ui.setSliderValue(
                        "$SmoothParams::SmoothingDegree", 1.0)
                    coat.ui.cmd("$DialogButton#1")

                coat.ui.cmd("$SmoothObject", smooth_command)
                print(f"Closed holes for {obj.name()}")

    coat.ui.showInfoMessage(
        f"Frozen area split - {len(new_children)} new objects created", 3000)


def main():
    split_frozen_area()


# 3DCoat executes script content directly, so call main() here
main()
