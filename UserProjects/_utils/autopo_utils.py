"""
Autopo Utilities - Workflow automation for autopo operations.

Provides functions to run autopo with cached settings and import
results back to sculpt room in various configurations.
"""
import coat
from _utils.lks_settings import get_settings
from _utils.coat_ui_utils import (
    switch_to_room,
    command_with_confirm,
    show_message,
    wait_frames,
    ROOM_SCULPT,
    ROOM_RETOPO,
)

# =============================================================================
# AUTOPO COMMANDS
# =============================================================================

CMD_AUTOPO = "$AutoRetopo"
CMD_IMPORT_MULTIRES = "$RetopoBuildMR"
CMD_RETOPO_TO_SCULPT = "$RetopoToSculpt"

# Autopo setting paths (discovered through experimentation)
SETTING_AUTOPO_DENSITY = "$AutoRetopo::TargetPolycount"
SETTING_AUTOPO_OPTIMIZE = "$AutoRetopo::OptimizeMesh"
SETTING_AUTOPO_KEEP_CREASES = "$AutoRetopo::KeepCreases"
SETTING_AUTOPO_ADD_TO_SCENE = "$AutoRetopo::AddToScene"


# =============================================================================
# AUTOPO FUNCTIONS
# =============================================================================

def run_autopo_with_settings() -> None:
    """
    Run autopo using cached LKS settings.

    Reads autopo_density, autopo_optimize_mesh, autopo_keep_creases,
    and autopo_add_to_scene from the settings cache.
    """
    settings = get_settings()

    # Set autopo parameters from cache
    # Note: setEditBoxValue works for int/float/str values
    coat.ui.setEditBoxValue(SETTING_AUTOPO_DENSITY, settings.autopo_density)
    coat.ui.setBoolValue(SETTING_AUTOPO_OPTIMIZE,
                         settings.autopo_optimize_mesh)
    coat.ui.setBoolValue(SETTING_AUTOPO_KEEP_CREASES,
                         settings.autopo_keep_creases)
    coat.ui.setBoolValue(SETTING_AUTOPO_ADD_TO_SCENE,
                         settings.autopo_add_to_scene)

    # Run autopo with auto-confirm
    command_with_confirm(CMD_AUTOPO)

    show_message(
        f"Autopo started (target: {settings.autopo_density} polys)", 2000)


def autopo_to_sculpt() -> None:
    """
    Run autopo, import result to sculpt, and hide original.

    Workflow:
    1. Cache original object info
    2. Run autopo with settings
    3. Switch to retopo, then sculpt
    4. Import retopo to sculpt
    5. Ghost (hide) original object
    """
    # Cache original object info
    try:
        original = coat.Scene.current().Volume()
        original_element = original.inScene()
        original_name = original_element.name()
    except Exception:
        show_message("Error: No valid sculpt object selected", 3000)
        return

    # Run autopo
    run_autopo_with_settings()
    wait_frames(4)

    # Switch to retopo, then back to sculpt
    switch_to_room(ROOM_RETOPO, 4)
    switch_to_room(ROOM_SCULPT, 4)

    # Import retopo to sculpt
    command_with_confirm(CMD_RETOPO_TO_SCULPT)
    wait_frames(4)

    # Hide original (ghost it)
    try:
        original_element.ghost(True)
        show_message(f"Imported retopo, hid '{original_name}'", 3000)
    except Exception:
        show_message("Imported retopo (could not hide original)", 3000)


def autopo_to_multiresolution() -> None:
    """
    Run autopo and import as multiresolution lowest level.

    Workflow:
    1. Run autopo with settings
    2. Ensure we're in Sculpt room
    3. Import as multiresolution
    """
    # Run autopo
    run_autopo_with_settings()
    wait_frames(4)

    # Must be in Sculpt room for multires import
    switch_to_room(ROOM_SCULPT, 4)

    # Import as multiresolution
    command_with_confirm(CMD_IMPORT_MULTIRES)
    wait_frames(4)

    show_message("Imported as multiresolution", 3000)


def clear_retopo_mesh() -> None:
    """Clear all retopo mesh data."""
    switch_to_room(ROOM_RETOPO, 4)
    coat.ui.cmd("$ClearTM")
    show_message("Retopo mesh cleared", 2000)
