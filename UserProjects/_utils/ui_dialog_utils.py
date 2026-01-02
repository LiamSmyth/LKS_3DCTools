"""
UI Dialog Utilities

Provides dataclasses and configurators for common 3DCoat dialog operations.
Users of this module don't need to know magic strings - just use the dataclasses
and configurator functions.

Pattern:
    1. Dataclass defines the dialog's parameters with typed defaults
    2. Configurator function returns a closure to inject values into dialog
    3. All magic strings are constants at the top

Example:
    params = ResampleParams(target_polycount=50000, scale=0.5)
    coat.ui.cmd(CMD_RESAMPLE, configure_resample_dialog(params))
"""
import coat
from dataclasses import dataclass
from typing import Callable

# =============================================================================
# RESAMPLE MAGIC UI STRINGS
# =============================================================================

CMD_RESAMPLE: str = "$Resample"
SETTING_RESAMPLE_POLYCOUNT: str = "$ResampleParams::RequiredPolycount"
SETTING_RESAMPLE_SCALE: str = "$ResampleParams::ResamplingScale"

# =============================================================================
# DECIMATE MAGIC UI STRINGS
# =============================================================================

CMD_DECIMATE: str = "$Decimate"
SETTING_DECIMATE_POLYCOUNT: str = "$DecimationParams::ReducedPolycount"
SETTING_DECIMATE_PERCENT: str = "$DecimationParams::ReductionPercent"

# =============================================================================
# VOXELIZE MAGIC UI STRINGS
# =============================================================================

CMD_VOXELIZE: str = "$ToVoxels"
SETTING_VOXELIZE_POLYCOUNT: str = "$VoxelizeParams::SuggestedPolycount"

# =============================================================================
# DIALOG BUTTONS
# =============================================================================

CMD_DIALOG_OK: str = "$DialogButton#1"
CMD_DIALOG_CANCEL: str = "$DialogButton#2"

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_RESAMPLE_SCALE: float = 0.5
DEFAULT_REDUCTION_PERCENT: float = 50.0
DEFAULT_VOXELIZE_POLYCOUNT: int = 100000


# =============================================================================
# RESAMPLE DATACLASS & CONFIGURATOR
# =============================================================================

@dataclass
class ResampleParams:
    """Parameters for resample operation."""
    target_polycount: int
    scale: float = DEFAULT_RESAMPLE_SCALE


def configure_resample_dialog(params: ResampleParams) -> Callable[[], None]:
    """
    Create a callback to configure the resample dialog.

    Args:
        params: ResampleParams with target polycount and scale

    Returns:
        Closure that configures dialog and clicks OK
    """
    def configurator() -> None:
        coat.ui.setEditBoxValue(
            SETTING_RESAMPLE_POLYCOUNT, params.target_polycount)
        coat.ui.setSliderValue(SETTING_RESAMPLE_SCALE, params.scale)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


def execute_resample(params: ResampleParams) -> None:
    """
    Execute resample with given parameters.

    Args:
        params: ResampleParams dataclass
    """
    coat.ui.cmd(CMD_RESAMPLE, configure_resample_dialog(params))


# =============================================================================
# DECIMATE DATACLASS & CONFIGURATOR
# =============================================================================

@dataclass
class DecimateParams:
    """Parameters for decimate operation."""
    target_polycount: int | None = None
    reduction_percent: float | None = None


def configure_decimate_dialog(params: DecimateParams) -> Callable[[], None]:
    """
    Create a callback to configure the decimate dialog.

    Args:
        params: DecimateParams with target polycount and/or reduction percent

    Returns:
        Closure that configures dialog and clicks OK
    """
    def configurator() -> None:
        if params.target_polycount is not None:
            coat.ui.setEditBoxValue(
                SETTING_DECIMATE_POLYCOUNT, params.target_polycount)
        if params.reduction_percent is not None:
            coat.ui.setSliderValue(
                SETTING_DECIMATE_PERCENT, params.reduction_percent)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


def execute_decimate(params: DecimateParams) -> None:
    """
    Execute decimate with given parameters.

    Args:
        params: DecimateParams dataclass
    """
    coat.ui.cmd(CMD_DECIMATE, configure_decimate_dialog(params))


# =============================================================================
# VOXELIZE DATACLASS & CONFIGURATOR
# =============================================================================

@dataclass
class VoxelizeParams:
    """Parameters for voxelize operation."""
    suggested_polycount: int = DEFAULT_VOXELIZE_POLYCOUNT


def configure_voxelize_dialog(params: VoxelizeParams) -> Callable[[], None]:
    """
    Create a callback to configure the voxelize dialog.

    Args:
        params: VoxelizeParams with suggested polycount

    Returns:
        Closure that configures dialog and clicks OK
    """
    def configurator() -> None:
        coat.ui.setEditBoxValue(
            SETTING_VOXELIZE_POLYCOUNT, params.suggested_polycount)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator


def execute_voxelize(params: VoxelizeParams) -> None:
    """
    Execute voxelize with given parameters.

    Args:
        params: VoxelizeParams dataclass
    """
    coat.ui.cmd(CMD_VOXELIZE, configure_voxelize_dialog(params))


# =============================================================================
# CONVENIENCE FUNCTIONS (use the dataclasses internally)
# =============================================================================

def resample_to_half(current_polycount: int) -> None:
    """Resample to half the current polycount."""
    params = ResampleParams(
        target_polycount=current_polycount // 2,
        scale=DEFAULT_RESAMPLE_SCALE
    )
    execute_resample(params)


def resample_to_target(initial_polycount: int, target_polycount: int) -> None:
    """Resample from initial to target polycount."""
    ratio: float = target_polycount / initial_polycount
    # Add buffer to target and scale for better results
    params = ResampleParams(
        target_polycount=target_polycount + 1000,
        scale=ratio * 1.1
    )
    execute_resample(params)
    print(
        f"Resampling: {initial_polycount:,} -> {target_polycount:,} (ratio: {ratio:.2f})")


def decimate_by_percent(reduction_percent: float = DEFAULT_REDUCTION_PERCENT) -> None:
    """Decimate by percentage reduction."""
    params = DecimateParams(reduction_percent=reduction_percent)
    execute_decimate(params)


def decimate_to_target(target_polycount: int) -> None:
    """Decimate to target polycount."""
    params = DecimateParams(target_polycount=target_polycount)
    execute_decimate(params)


def decimate_to_half() -> None:
    """Decimate to approximately half (80% reduction)."""
    decimate_by_percent(80.0)


# =============================================================================
# LEGACY CLASS (for backward compatibility)
# =============================================================================

class UIDialogUtils:
    """
    Legacy static utility class - prefer using dataclasses directly.

    Deprecated: Use ResampleParams, DecimateParams, VoxelizeParams instead.
    """

    @staticmethod
    def execute_resample_dialog(target_polycount: int, resample_scale: float = DEFAULT_RESAMPLE_SCALE) -> None:
        """Deprecated: Use execute_resample(ResampleParams(...)) instead."""
        execute_resample(ResampleParams(target_polycount, resample_scale))

    @staticmethod
    def execute_decimation_dialog(target_polycount: int | None = None, reduction_percent: float | None = None) -> None:
        """Deprecated: Use execute_decimate(DecimateParams(...)) instead."""
        execute_decimate(DecimateParams(target_polycount, reduction_percent))

    @staticmethod
    def execute_voxel_conversion_dialog(suggested_polycount: int) -> None:
        """Deprecated: Use execute_voxelize(VoxelizeParams(...)) instead."""
        execute_voxelize(VoxelizeParams(suggested_polycount))

    @staticmethod
    def execute_decimate_to_half() -> None:
        """Deprecated: Use decimate_to_half() instead."""
        decimate_to_half()

    @staticmethod
    def execute_resample_to_half(current_polycount: int) -> None:
        """Deprecated: Use resample_to_half(polycount) instead."""
        resample_to_half(current_polycount)

    @staticmethod
    def execute_resample_to_polycount(initial_polycount: int, tgt_polycount: int) -> None:
        """Deprecated: Use resample_to_target(initial, target) instead."""
        resample_to_target(initial_polycount, tgt_polycount)

    @staticmethod
    def execute_resample_element_to_polycount(element: coat.SceneElement, tgt_polycount: int) -> None:
        """
        Execute resampling to half the current polycount.

        Args:
            current_polycount: Current polygon count
        """
        initial_polycount = element.Volume().getPolycount()
        ratio = tgt_polycount / initial_polycount

        # The 1000 polys and 1.1 are to avoid the resample being skipped
        # by 3dcoat
        UIDialogUtils.execute_resample_dialog(
            tgt_polycount + 1000, ratio * 1.1)

        print(" Resampling: Initial polycount: %s Target polycount: %s Ratio: %s" %
              (initial_polycount, tgt_polycount, ratio))
