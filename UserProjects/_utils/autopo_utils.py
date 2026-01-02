"""
Autopo Utilities - Workflow automation for autopo operations.

Provides dataclasses and functions to run autopo with typed parameters
and import results back to sculpt room in various configurations.

Pattern:
    params = AutopoParams(target_polycount=10000, bypass_density_modal=True)
    execute_autopo(params)
"""
import coat
from dataclasses import dataclass
from typing import Callable

from _utils.coat_ui_utils import (
    switch_to_room,
    ensure_sculpt_room,
    show_message,
    show_error,
    wait_frames,
    ROOM_SCULPT,
    ROOM_RETOPO,
    CMD_DIALOG_OK,
)

# =============================================================================
# AUTOPO MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
# =============================================================================

# Command to open autopo dialog (Quadrangulate opens the dialog)
CMD_AUTOPO: str = "$Quadrangulate"

# Import commands
CMD_RETOPO_TO_SCULPT: str = "$GetObjectFromRetopoRoom"
CMD_IMPORT_MULTIRES: str = "$MultiresControl::AddLowMultiresolutionLevelFromRetopo[1]"
CMD_CLEAR_RETOPO: str = "$ClearTM"

# Dialog OK button
CMD_DIALOG_OK_LOCAL: str = "$DialogButton#1"

# Autopo parameter settings (QuadragulationTask namespace)
SETTING_REQUIRED_POLYCOUNT: str = "$QuadragulationTask::RequiredPolycount"
SETTING_CAPTURE_DETAILS: str = "$QuadragulationTask::CaptureDetails"
SETTING_HARDSURFACE: str = "$QuadragulationTask::HardsurfaceRetopology"
SETTING_AUTO_DENSITY: str = "$QuadragulationTask::AutoDensityInfluence"
SETTING_VOXELIZE: str = "$QuadragulationTask::Voxelize"
SETTING_VOXELIZE_POLYCOUNT: str = "$QuadragulationTask::VoxelizedObjectPolycount1"
SETTING_DECIMATE_IF_ABOVE: str = "$QuadragulationTask::DecimateIfAbove"
SETTING_DECIMATION_LIMIT: str = "$QuadragulationTask::DecimationLimit1"
SETTING_TANGENT_SMOOTH: str = "$QuadragulationTask::TangentSmoothRes"
SETTING_BYPASS_DENSITY_MODAL: str = "$QuadragulationTask::BypassDensityAndStrokes"
# Quality dropdown (draft, intermediate, best)
COMBOBOX_QUAD_QUALITY: str = "COMBOBOX_QuadQuality"

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_TARGET_POLYCOUNT: int = 10000
DEFAULT_CAPTURE_DETAILS: float = 1.0  # 0.0-1.0 (1.0 = 100%)
DEFAULT_AUTO_DENSITY: float = 0.5  # 0.0-2.0 (painted density influence)
DEFAULT_HARDSURFACE: bool = False
DEFAULT_VOXELIZE: bool = False
# x1000 polys (1000 = 1M) - voxelize target polycount
DEFAULT_VOXELIZE_POLYCOUNT: int = 1000
DEFAULT_DECIMATE_IF_ABOVE: bool = False
# x1000 polys (10 = 10k) - decimate if exceeds
DEFAULT_DECIMATION_LIMIT: int = 10
DEFAULT_TANGENT_SMOOTH: bool = True
DEFAULT_BYPASS_DENSITY_MODAL: bool = True

# Timing defaults
AUTOPO_WAIT_FRAMES: int = 8
IMPORT_WAIT_FRAMES: int = 4


# =============================================================================
# AUTOPO DATACLASS & CONFIGURATOR
# =============================================================================

@dataclass
class AutopoParams:
    """
    Parameters for autopo (automatic retopology) operation.

    Users don't need to know magic strings - just set these typed fields.
    """
    target_polycount: int = DEFAULT_TARGET_POLYCOUNT
    capture_details: float = DEFAULT_CAPTURE_DETAILS  # 0.0-1.0 (1.0 = 100%)
    auto_density: float = DEFAULT_AUTO_DENSITY  # 0.0-2.0 (painted density)
    hardsurface: bool = DEFAULT_HARDSURFACE
    voxelize: bool = DEFAULT_VOXELIZE
    voxelize_polycount: int = DEFAULT_VOXELIZE_POLYCOUNT  # x1000 polys
    decimate_if_above: bool = DEFAULT_DECIMATE_IF_ABOVE
    decimation_limit: int = DEFAULT_DECIMATION_LIMIT  # x1000 polys
    tangent_smooth: bool = DEFAULT_TANGENT_SMOOTH
    bypass_density_modal: bool = DEFAULT_BYPASS_DENSITY_MODAL


def configure_autopo(params: AutopoParams) -> None:
    """
    Configure autopo settings before execution.

    This sets all the UI values without executing the command.

    Args:
        params: AutopoParams with all settings
    """
    coat.ui.setEditBoxValue(SETTING_REQUIRED_POLYCOUNT,
                            params.target_polycount)
    coat.ui.setSliderValue(SETTING_CAPTURE_DETAILS, params.capture_details)
    coat.ui.setSliderValue(SETTING_AUTO_DENSITY, params.auto_density)
    coat.ui.setBoolValue(SETTING_HARDSURFACE, params.hardsurface)
    coat.ui.setBoolValue(SETTING_VOXELIZE, params.voxelize)
    coat.ui.setEditBoxValue(SETTING_VOXELIZE_POLYCOUNT,
                            params.voxelize_polycount)
    coat.ui.setBoolValue(SETTING_DECIMATE_IF_ABOVE, params.decimate_if_above)
    coat.ui.setEditBoxValue(SETTING_DECIMATION_LIMIT, params.decimation_limit)
    coat.ui.setBoolValue(SETTING_TANGENT_SMOOTH, params.tangent_smooth)
    coat.ui.setBoolValue(SETTING_BYPASS_DENSITY_MODAL,
                         params.bypass_density_modal)


def create_autopo_configurator(params: AutopoParams) -> Callable[[], None]:
    """
    Create a callback that configures autopo dialog and clicks OK.

    The dialog must be open when this callback runs.

    Args:
        params: AutopoParams with all settings

    Returns:
        Callback function to pass to coat.ui.cmd()
    """
    def configurator() -> None:
        # Wait for dialog to be fully ready
        wait_frames(2)
        # Set all dialog values
        configure_autopo(params)
        # Click OK to execute
        coat.ui.cmd(CMD_DIALOG_OK_LOCAL)
    return configurator


def execute_autopo(params: AutopoParams) -> bool:
    """
    Execute autopo with given parameters.

    Opens the Quadrangulate dialog, configures it with params,
    and clicks OK to start the autopo process.

    Args:
        params: AutopoParams dataclass with all settings

    Returns:
        True if autopo started successfully, False on error
    """
    # Ensure we're in Sculpt room (switch if needed)
    ensure_sculpt_room()

    # Validate we have something selected
    current = coat.Scene.current()
    if not current:
        show_error("No object selected for autopo", 3000)
        return False

    # Configure autopo settings BEFORE opening the dialog
    # (3DCoat remembers these settings even when dialog is closed)
    configure_autopo(params)
    wait_frames(2)

    # Now open dialog and just click OK
    def click_ok() -> None:
        wait_frames(2)
        coat.ui.cmd(CMD_DIALOG_OK_LOCAL)

    result: bool = coat.ui.cmd(CMD_AUTOPO, click_ok)

    if result:
        show_message(
            f"Autopo started (target: {params.target_polycount:,} polys)", 2000)
        # Wait for autopo to complete
        wait_frames(AUTOPO_WAIT_FRAMES)
        # Return to sculpt room
        ensure_sculpt_room()
    else:
        show_error("Failed to start autopo", 3000)

    return result


# =============================================================================
# IMPORT CONFIGURATORS
# =============================================================================

def configure_import_dialog() -> Callable[[], None]:
    """Create a callback to confirm import dialog."""
    def configurator() -> None:
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


def import_retopo_to_sculpt() -> bool:
    """
    Import retopo mesh to sculpt room.

    Returns:
        True if successful
    """
    switch_to_room(ROOM_SCULPT, IMPORT_WAIT_FRAMES)
    result: bool = coat.ui.cmd(CMD_RETOPO_TO_SCULPT)
    wait_frames(IMPORT_WAIT_FRAMES)
    ensure_sculpt_room()
    return result


def import_as_multiresolution() -> bool:
    """
    Import retopo mesh as multiresolution lowest level.

    The retopo object name must match the selected sculpt object.
    Running autopo on a sculpt object produces a matching name by default.

    Returns:
        True if successful
    """
    switch_to_room(ROOM_SCULPT, IMPORT_WAIT_FRAMES)
    result: bool = coat.ui.cmd(CMD_IMPORT_MULTIRES)
    wait_frames(IMPORT_WAIT_FRAMES)
    ensure_sculpt_room()
    return result


def clear_retopo_mesh() -> None:
    """Clear all retopo mesh data."""
    switch_to_room(ROOM_RETOPO, IMPORT_WAIT_FRAMES)
    coat.ui.cmd(CMD_CLEAR_RETOPO)
    show_message("Retopo mesh cleared", 2000)


# =============================================================================
# HIGH-LEVEL WORKFLOW FUNCTIONS
# =============================================================================

def autopo_to_sculpt(params: AutopoParams | None = None) -> bool:
    """
    Run autopo, import result to sculpt, and ghost original.

    Args:
        params: AutopoParams (uses defaults if None)

    Returns:
        True if successful, False on error
    """
    if params is None:
        params = AutopoParams()

    # Cache original object info
    current = coat.Scene.current()
    if not current:
        show_error("No object selected", 3000)
        return False

    original_element: coat.SceneElement = current
    original_name: str = original_element.name()

    # Run autopo
    if not execute_autopo(params):
        return False

    # Wait for autopo to complete
    wait_frames(AUTOPO_WAIT_FRAMES)

    # Switch to retopo to access the result, then back to sculpt
    switch_to_room(ROOM_RETOPO, IMPORT_WAIT_FRAMES)

    # Import to sculpt
    if not import_retopo_to_sculpt():
        show_error("Failed to import retopo to sculpt", 3000)
        return False

    # Ghost the original object
    try:
        original_element.setGhost(True)
        show_message(f"Imported retopo, ghosted '{original_name}'", 3000)
    except Exception:
        show_message("Imported retopo (could not ghost original)", 3000)

    return True


def autopo_to_multiresolution(params: AutopoParams | None = None) -> bool:
    """
    Run autopo and import as multiresolution lowest level.

    Args:
        params: AutopoParams (uses defaults if None)

    Returns:
        True if successful, False on error
    """
    if params is None:
        params = AutopoParams()

    # Run autopo
    if not execute_autopo(params):
        return False

    wait_frames(AUTOPO_WAIT_FRAMES)

    # Import as multiresolution
    if not import_as_multiresolution():
        show_error("Failed to import as multiresolution", 3000)
        return False

    show_message("Imported as multiresolution", 3000)
    return True


# =============================================================================
# LEGACY FUNCTION (for backward compatibility with lks_settings)
# =============================================================================

def run_autopo_with_settings() -> bool:
    """
    Run autopo using cached LKS settings.

    Legacy function - prefer using execute_autopo(AutopoParams(...)) directly.
    """
    from _utils.lks_settings import get_settings
    settings = get_settings()

    params = AutopoParams(
        target_polycount=settings.autopo_density,
        bypass_density_modal=DEFAULT_BYPASS_DENSITY_MODAL
    )
    return execute_autopo(params)
