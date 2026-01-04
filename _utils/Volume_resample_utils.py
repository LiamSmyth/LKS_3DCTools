"""
Volume Resample Utilities - Resample operations on Volumes.

Low-level primitives with RAW ARGUMENTS ONLY (no dataclasses).
Operators in `_ops/` own Config dataclasses and call these functions.
"""
import coat
from typing import Callable

from _utils.coat_ui_utils import CMD_DIALOG_OK, wait_frames

# =============================================================================
# MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
# =============================================================================

CMD_RESAMPLE: str = "$Resample"
SETTING_RESAMPLE_POLYCOUNT: str = "$ResampleParams::RequiredPolycount"
SETTING_RESAMPLE_SCALE: str = "$ResampleParams::ResamplingScale"

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_RESAMPLE_SCALE: float = 0.5
MESH_OP_WAIT_FRAMES: int = 2


# =============================================================================
# CONFIGURATOR (returns closure with raw args captured)
# =============================================================================

def configure_resample_dialog(
    target_polycount: int,
    scale: float = DEFAULT_RESAMPLE_SCALE,
) -> Callable[[], None]:
    """
    Create a callback to configure the resample dialog.

    Args:
        target_polycount: Target polycount for resample
        scale: Resampling scale factor

    Returns:
        Closure that configures dialog and clicks OK
    """
    def configurator() -> None:
        coat.ui.setEditBoxValue(SETTING_RESAMPLE_POLYCOUNT, target_polycount)
        coat.ui.setSliderValue(SETTING_RESAMPLE_SCALE, scale)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


# =============================================================================
# EXECUTE FUNCTIONS (raw args)
# =============================================================================

def execute_resample(
    target_polycount: int,
    scale: float = DEFAULT_RESAMPLE_SCALE,
) -> None:
    """
    Execute resample on current Volume.

    Args:
        target_polycount: Target polycount for resample
        scale: Resampling scale factor
    """
    callback: Callable[[], None] = configure_resample_dialog(
        target_polycount=target_polycount,
        scale=scale,
    )
    coat.ui.cmd(CMD_RESAMPLE, callback)
    wait_frames(MESH_OP_WAIT_FRAMES)


# =============================================================================
# CONVENIENCE FUNCTIONS (thin wrappers with raw args)
# =============================================================================

def resample_to_half(current_polycount: int) -> None:
    """Resample current Volume to half polycount."""
    execute_resample(
        target_polycount=current_polycount // 2,
        scale=DEFAULT_RESAMPLE_SCALE,
    )


def resample_to_target(initial_polycount: int, target_polycount: int) -> None:
    """
    Resample current Volume from initial to target polycount.

    Args:
        initial_polycount: Current polycount before resample
        target_polycount: Desired polycount after resample
    """
    ratio: float = target_polycount / initial_polycount
    # Add buffer to target and scale for better results
    execute_resample(
        target_polycount=target_polycount + 1000,
        scale=ratio * 1.1,
    )
    print(
        f"Resampled: {initial_polycount:,} -> {target_polycount:,} (ratio: {ratio:.2f})")
