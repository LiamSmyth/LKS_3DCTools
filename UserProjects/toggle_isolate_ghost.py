"""
Toggle Isolate Ghost

Toggle ghost state for all objects except the current one (isolate mode).
If isolate is already active, unghost all objects.
"""
import coat
from _utils.scene_iteration_utils import SceneIterationUtils


def main():
    """Toggle isolation mode (ghost all except current)"""
    print("Toggling isolation mode...")
    SceneIterationUtils.toggle_ghost_all_except_current()
    print("Isolation mode toggled")

    # Show summary message to user
    coat.ui.showInfoMessage("Isolation mode toggled", 3000)


# 3DCoat executes script content directly, so call main() here
main()
