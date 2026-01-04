"""
Volume Mode Utilities - Surface/Voxel conversion on Volumes.

Low-level primitives with RAW ARGUMENTS ONLY (no dataclasses).
Operators in `_ops/` own Config dataclasses and call these functions.
"""
import coat
from typing import Callable

from _utils.coat_ui_utils import CMD_DIALOG_OK, wait_frames

# =============================================================================
# MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
# =============================================================================

CMD_VOXELIZE: str = "$ToVoxels"
CMD_TO_SURFACE: str = "$ToSurface"
SETTING_VOXELIZE_POLYCOUNT: str = "$VoxelizeParams::SuggestedPolycount"

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_VOXELIZE_POLYCOUNT: int = 100000
MESH_OP_WAIT_FRAMES: int = 2


# =============================================================================
# CONFIGURATOR (returns closure with raw args captured)
# =============================================================================

def configure_voxelize_dialog(
    suggested_polycount: int = DEFAULT_VOXELIZE_POLYCOUNT,
) -> Callable[[], None]:
    """
    Create a callback to configure the voxelize dialog.

    Args:
        suggested_polycount: Target polycount for voxelization

    Returns:
        Closure that configures dialog and clicks OK
    """
    def configurator() -> None:
        coat.ui.setEditBoxValue(
            SETTING_VOXELIZE_POLYCOUNT, suggested_polycount)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


# =============================================================================
# EXECUTE FUNCTIONS (raw args)
# =============================================================================

def execute_voxelize(suggested_polycount: int = DEFAULT_VOXELIZE_POLYCOUNT) -> None:
    """
    Execute voxelize on current Volume.

    Args:
        suggested_polycount: Target polycount for voxelization
    """
    callback: Callable[[], None] = configure_voxelize_dialog(
        suggested_polycount)
    coat.ui.cmd(CMD_VOXELIZE, callback)
    wait_frames(MESH_OP_WAIT_FRAMES)


# =============================================================================
# CONVERSION FUNCTIONS (operate on Volume directly)
# =============================================================================

def convert_to_surface(volume: coat.Volume) -> None:
    """Convert a volume from voxels to surface mode."""
    if volume.isVoxelized():
        volume.toSurface()


def convert_to_voxels(volume: coat.Volume, polycount: int | None = None) -> None:
    """
    Convert a volume from surface to voxels.

    Args:
        volume: The volume to convert
        polycount: Target polycount (uses Volume.toVoxels() default if None)
    """
    if volume.isSurface():
        if polycount is not None:
            execute_voxelize(polycount)
        else:
            volume.toVoxels()


def ensure_surface_mode(volume: coat.Volume) -> None:
    """Ensure volume is in surface mode (convert from voxels if needed)."""
    convert_to_surface(volume)


def voxelize_to_polycount(target_polycount: int) -> None:
    """Voxelize current Volume to target polycount."""
    execute_voxelize(target_polycount)


# =============================================================================
# RESAMPLE + VOXELIZE WORKFLOW
# =============================================================================

def resample_and_voxelize(volume: coat.Volume, multiplier: float) -> int:
    """
    Resample a surface volume to Nx polycount, then convert to voxels.

    If already voxelized, converts back to surface.

    Args:
        volume: The volume to process
        multiplier: Polycount multiplier (2.0 = 2x, 4.0 = 4x, etc.)

    Returns:
        New polycount after operation
    """
    # Import here to avoid circular dependency
    from _utils.Volume_resample_utils import execute_resample

    if volume.isVoxelized():
        # Already voxel - convert to surface
        volume.toSurface()
        return volume.getPolycount()

    # Surface mode - resample and voxelize
    current_polycount: int = volume.getPolycount()
    if current_polycount <= 0:
        return 0

    target_polycount: int = int(current_polycount * multiplier)

    # Resample to target
    execute_resample(target_polycount=target_polycount, scale=multiplier)

    # Convert to voxels
    volume.toVoxels()

    return volume.getPolycount()
