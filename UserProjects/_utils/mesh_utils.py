"""
Mesh Utilities - Mesh modification operations for sculpt objects.

Provides dataclasses and functions for mesh operations like resample,
decimate, voxelize, and subdivide. These operate on SculptObjects.

Pattern:
    params = ResampleParams(target_polycount=50000, scale=0.5)
    execute_resample(params)
"""
import coat
from dataclasses import dataclass
from typing import Callable

from _utils.coat_ui_utils import (
    CMD_DIALOG_OK,
    wait_frames,
    show_message,
    show_error,
)

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
CMD_DECIMATE_16X: str = "$Decimate16X"
SETTING_DECIMATE_POLYCOUNT: str = "$DecimationParams::ReducedPolycount"
SETTING_DECIMATE_PERCENT: str = "$DecimationParams::ReductionPercent"

# =============================================================================
# VOXELIZE MAGIC UI STRINGS
# =============================================================================

CMD_VOXELIZE: str = "$ToVoxels"
CMD_TO_SURFACE: str = "$ToSurface"
SETTING_VOXELIZE_POLYCOUNT: str = "$VoxelizeParams::SuggestedPolycount"

# =============================================================================
# SUBDIVIDE MAGIC UI STRINGS
# =============================================================================

CMD_SUBDIVIDE: str = "$VoxTreeBranch.IncRes_HINT.Root"
CMD_MAKE_SYMMETRICAL: str = "$MakeSymm"

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_RESAMPLE_SCALE: float = 0.5
DEFAULT_REDUCTION_PERCENT: float = 50.0
DEFAULT_VOXELIZE_POLYCOUNT: int = 100000

# Timing
MESH_OP_WAIT_FRAMES: int = 2


# =============================================================================
# RESAMPLE DATACLASS & FUNCTIONS
# =============================================================================

@dataclass
class ResampleParams:
    """Parameters for resample operation on a SculptObject."""
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
    Execute resample on current SculptObject with given parameters.

    Args:
        params: ResampleParams dataclass
    """
    coat.ui.cmd(CMD_RESAMPLE, configure_resample_dialog(params))
    wait_frames(MESH_OP_WAIT_FRAMES)


def resample_to_half(current_polycount: int) -> None:
    """Resample current SculptObject to half polycount."""
    params = ResampleParams(
        target_polycount=current_polycount // 2,
        scale=DEFAULT_RESAMPLE_SCALE
    )
    execute_resample(params)


def resample_to_target(initial_polycount: int, target_polycount: int) -> None:
    """Resample current SculptObject from initial to target polycount."""
    ratio: float = target_polycount / initial_polycount
    # Add buffer to target and scale for better results
    params = ResampleParams(
        target_polycount=target_polycount + 1000,
        scale=ratio * 1.1
    )
    execute_resample(params)
    print(
        f"Resampled: {initial_polycount:,} -> {target_polycount:,} (ratio: {ratio:.2f})")


# =============================================================================
# DECIMATE DATACLASS & FUNCTIONS
# =============================================================================

@dataclass
class DecimateParams:
    """Parameters for decimate operation on a SculptObject."""
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
    Execute decimate on current SculptObject with given parameters.

    Args:
        params: DecimateParams dataclass
    """
    coat.ui.cmd(CMD_DECIMATE, configure_decimate_dialog(params))
    wait_frames(MESH_OP_WAIT_FRAMES)


def decimate_by_percent(reduction_percent: float = DEFAULT_REDUCTION_PERCENT) -> None:
    """Decimate current SculptObject by percentage reduction."""
    params = DecimateParams(reduction_percent=reduction_percent)
    execute_decimate(params)


def decimate_to_target(target_polycount: int) -> None:
    """Decimate current SculptObject to target polycount."""
    params = DecimateParams(target_polycount=target_polycount)
    execute_decimate(params)


def decimate_to_half() -> None:
    """Decimate current SculptObject to approximately half (50% reduction)."""
    decimate_by_percent(50.0)


def decimate_16x() -> None:
    """Decimate current SculptObject to 1/16th (quick proxy)."""
    coat.ui.cmd(CMD_DECIMATE_16X)
    wait_frames(MESH_OP_WAIT_FRAMES)


# =============================================================================
# VOXELIZE DATACLASS & FUNCTIONS
# =============================================================================

@dataclass
class VoxelizeParams:
    """Parameters for voxelize operation on a SculptObject."""
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
    Execute voxelize on current SculptObject with given parameters.

    Args:
        params: VoxelizeParams dataclass
    """
    coat.ui.cmd(CMD_VOXELIZE, configure_voxelize_dialog(params))
    wait_frames(MESH_OP_WAIT_FRAMES)


def voxelize_to_polycount(target_polycount: int) -> None:
    """Voxelize current SculptObject to target polycount."""
    params = VoxelizeParams(suggested_polycount=target_polycount)
    execute_voxelize(params)


# =============================================================================
# SURFACE/VOXEL CONVERSION FUNCTIONS
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
        polycount: Target polycount (uses default if None)
    """
    if volume.isSurface():
        if polycount is not None:
            voxelize_to_polycount(polycount)
        else:
            volume.toVoxels()


def ensure_surface_mode(volume: coat.Volume) -> None:
    """Ensure volume is in surface mode (convert from voxels if needed)."""
    convert_to_surface(volume)


# =============================================================================
# SUBDIVIDE FUNCTIONS
# =============================================================================

def subdivide_once() -> None:
    """Subdivide current SculptObject once (doubles polycount approximately)."""
    coat.ui.cmd(CMD_SUBDIVIDE)
    wait_frames(MESH_OP_WAIT_FRAMES)


def make_symmetrical() -> None:
    """Make the current SculptObject symmetrical along its symmetry axis."""
    coat.ui.cmd(CMD_MAKE_SYMMETRICAL)
    wait_frames(MESH_OP_WAIT_FRAMES)


# =============================================================================
# RESAMPLE + VOXELIZE WORKFLOW
# =============================================================================

def resample_and_voxelize(
    volume: coat.Volume,
    multiplier: float
) -> int:
    """
    Resample a surface volume to Nx polycount, then convert to voxels.

    If already voxelized, converts back to surface.

    Args:
        volume: The volume to process
        multiplier: Polycount multiplier (2.0 = 2x, 4.0 = 4x, etc.)

    Returns:
        New polycount after operation
    """
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
    params = ResampleParams(
        target_polycount=target_polycount,
        scale=multiplier
    )
    execute_resample(params)

    # Convert to voxels
    volume.toVoxels()

    return volume.getPolycount()


# =============================================================================
# LAYER CLEANUP (mesh operations often create unwanted layers)
# =============================================================================

def cleanup_after_mesh_operation() -> None:
    """
    Clean up after destructive mesh operations.

    Mesh operations like decimate often create unwanted layers.
    This removes empty layers and reactivates layer 0.
    """
    coat.Scene.removeEmptyLayers()
    coat.Scene.setActiveLayer(0)


# =============================================================================
# UNIFORM DENSITY CALCULATIONS
# =============================================================================

def calculate_target_polycount_by_scale(
    reference_volume: coat.Volume,
    target_volume: coat.Volume
) -> int:
    """
    Calculate target polycount for a volume to match a reference's polygon density.

    Uses the average bounding box dimensions to calculate scale ratio.
    Polycount scales with the square of size (surface area).

    Args:
        reference_volume: The volume whose density to match
        target_volume: The volume to calculate target polycount for

    Returns:
        Target polycount to match the reference density
    """
    import math

    # Get bounding boxes
    ref_aabb: coat.boundbox = reference_volume.calcWorldSpaceAABB()
    tgt_aabb: coat.boundbox = target_volume.calcWorldSpaceAABB()

    # Calculate average dimensions
    ref_size: coat.vec3 = ref_aabb.GetSize()
    ref_dimension: float = (ref_size.x + ref_size.y + ref_size.z) / 3.0

    tgt_size: coat.vec3 = tgt_aabb.GetSize()
    tgt_dimension: float = (tgt_size.x + tgt_size.y + tgt_size.z) / 3.0

    # Polycount scales with square of size ratio
    scale_ratio: float = tgt_dimension / ref_dimension
    polycount_ratio: float = scale_ratio ** 2

    ref_polycount: int = reference_volume.getPolycount()
    target_polycount: int = math.floor(ref_polycount * polycount_ratio)

    return target_polycount


def resample_to_match_density(
    element: coat.SceneElement,
    reference_volume: coat.Volume
) -> None:
    """
    Resample a SculptObject to match the polygon density of a reference.

    The element will be selected and resampled to have similar polygon
    size (density) as the reference volume.

    Args:
        element: The SceneElement to resample
        reference_volume: The reference volume whose density to match
    """
    import math

    element.selectOne()

    if not element.isSculptObject():
        return

    vol: coat.Volume = element.Volume()

    # Ensure surface mode
    if not vol.isSurface():
        vol.toSurface()

    target_polycount: int = calculate_target_polycount_by_scale(
        reference_volume, vol)
    current_polycount: int = vol.getPolycount()

    if target_polycount <= 0 or current_polycount <= 0:
        return

    # Calculate resample ratio
    resample_ratio: float = math.sqrt(target_polycount / current_polycount)

    # Resample
    params = ResampleParams(
        target_polycount=target_polycount,
        scale=resample_ratio
    )
    execute_resample(params)

    print(
        f"Resampled '{element.name()}': {current_polycount:,} -> {target_polycount:,}")


def smart_match_density(
    element: coat.SceneElement,
    reference_volume: coat.Volume
) -> str:
    """
    Smart density matching using subdivide or decimate (not resample).

    Uses subdivision for increases > 2x (preserves shape better than resample)
    and decimation for decreases. Skips objects within 2x of target.

    Args:
        element: The SceneElement to adjust
        reference_volume: The reference volume whose density to match

    Returns:
        Action taken: "subdivided", "decimated", or "skipped"
    """
    import math

    element.selectOne()

    if not element.isSculptObject():
        return "skipped"

    vol: coat.Volume = element.Volume()

    # Ensure surface mode
    if not vol.isSurface():
        vol.toSurface()

    target_polycount: int = calculate_target_polycount_by_scale(
        reference_volume, vol)
    current_polycount: int = vol.getPolycount()

    if target_polycount <= 0 or current_polycount <= 0:
        return "skipped"

    polycount_ratio: float = target_polycount / current_polycount

    if polycount_ratio < 1.0:
        # Need to reduce - use decimate
        decimate_to_target(target_polycount)
        print(
            f"Decimated '{element.name()}': {current_polycount:,} -> {target_polycount:,}")
        return "decimated"

    elif polycount_ratio > 2.0:
        # Need to increase significantly - use subdivide
        # Each subdivide roughly quadruples polycount
        resample_ratio: float = math.sqrt(polycount_ratio)
        subdivide_count: int = min(math.ceil(math.log2(resample_ratio)), 5)
        subdivide_count = max(subdivide_count, 1)

        for _ in range(subdivide_count):
            subdivide_once()

        print(f"Subdivided '{element.name()}' {subdivide_count}x")
        return "subdivided"

    else:
        # Close enough - skip
        print(f"Skipped '{element.name()}' - close to target")
        return "skipped"
