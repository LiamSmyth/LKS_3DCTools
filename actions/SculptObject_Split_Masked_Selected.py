"""
Split the frozen/masked area of the current object into a new object.

There is no built-in way to split masked geometry in one step.
This script hides the frozen area, separates hidden geometry, and
cleans up the resulting meshes.

Room: Sculpt
Action: Split frozen geometry into new object
"""
import coat
from utils.object_utils import ObjectUtils
from utils.Volume_mode_utils import ensure_surface_mode
from utils.coat_ui_utils import (
    CMD_HIDE_FROZEN_AREA,
    CMD_SEPARATE_HIDDEN,
    CMD_SMOOTH_OBJECT,
    CMD_DIALOG_OK,
    SETTING_SMOOTH_DEGREE,
    wait_frames,
    show_message,
    show_error,
)


def smooth_object_once() -> None:
    """Apply light smoothing to current object."""
    def smooth_command() -> None:
        coat.ui.setSliderValue(SETTING_SMOOTH_DEGREE, 1.0)
        coat.ui.cmd(CMD_DIALOG_OK)
    coat.ui.cmd(CMD_SMOOTH_OBJECT, smooth_command)


def split_frozen_area() -> None:
    """Split the frozen area of the current object into a new object."""
    current_object: coat.SceneElement | None = ObjectUtils.get_current_sculpt_object()

    if not current_object:
        show_error("No object selected", 3000)
        return

    # Cache the original parent and existing children
    original_parent: coat.SceneElement = current_object.parent()
    existing_children: list[coat.SceneElement] = []

    # Store references to existing children
    for i in range(original_parent.childCount()):
        existing_children.append(original_parent.child(i))

    # Ensure the object is selected and in surface mode
    current_object.selectOne()

    vol: coat.Volume = current_object.Volume()
    ensure_surface_mode(vol)

    print(f"Splitting frozen area from: {current_object.name()}")

    # Hide the frozen area, then separate hidden geometry
    coat.ui.cmd(CMD_HIDE_FROZEN_AREA)
    coat.ui.cmd(CMD_SEPARATE_HIDDEN)
    wait_frames(4)

    vol.closeHoles(8192)
    wait_frames(4)

    # Find any new children created by the split
    new_children: list[coat.SceneElement] = []
    current_child_count: int = original_parent.childCount()

    for i in range(current_child_count):
        child: coat.SceneElement = original_parent.child(i)
        if child not in existing_children:
            new_children.append(child)
            print(f"New child created: {child.name()}")

    # Close holes and smooth all affected objects
    all_objects: list[coat.SceneElement] = [current_object] + new_children

    for obj in all_objects:
        if obj.isSculptObject():
            obj_vol: coat.Volume = obj.Volume()
            if obj_vol.isSurface():
                obj.selectOne()
                wait_frames(4)
                obj_vol.closeHoles(8192)
                smooth_object_once()
                print(f"Closed holes for {obj.name()}")

    show_message(
        f"Frozen area split - {len(new_children)} new objects created",
        3000
    )


def main() -> None:
    """Entry point."""
    split_frozen_area()


main()
