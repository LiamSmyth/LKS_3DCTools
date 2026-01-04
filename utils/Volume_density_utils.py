"""
Volume Density Utilities - Uniform density calculations and matching.

Low-level primitives with RAW ARGUMENTS ONLY (no dataclasses).
Operators in `_ops/` own Config dataclasses and call these functions.
"""
import coat
import math

from utils.coat_ui_utils import wait_frames
from utils.Volume_decimate_utils import decimate_by_percent
from utils.Volume_resample_utils import execute_resample, resample_to_target
from utils.Volume_subdivide_utils import subdivide_once

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_DENSITY_TOLERANCE: float = 0.2
MESH_OP_WAIT_FRAMES: int = 2


# =============================================================================
# DENSITY CALCULATION (pure function)
# =============================================================================

def calculate_target_polycount_by_scale(
    reference_volume: coat.Volume,
    target_volume: coat.Volume,
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


# =============================================================================
# DENSITY MATCHING FUNCTIONS
# =============================================================================

def resample_to_match_density(
    element: coat.SceneElement,
    reference_volume: coat.Volume,
) -> None:
    """
    Resample a SculptObject to match the polygon density of a reference.

    The element will be selected and resampled to have similar polygon
    size (density) as the reference volume.

    Args:
        element: The SceneElement to resample
        reference_volume: The reference volume whose density to match
    """
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
    execute_resample(
        target_polycount=target_polycount,
        scale=resample_ratio,
    )

    print(
        f"Resampled '{element.name()}': {current_polycount:,} -> {target_polycount:,}")


def smart_match_density(
    element: coat.SceneElement,
    reference_volume: coat.Volume,
    tolerance: float = DEFAULT_DENSITY_TOLERANCE,
) -> str:
    """
    Smart density matching using subdivide, decimate, or resample.

    Strategy:
    - If target is much higher (>4x): subdivide to overshoot, then decimate to exact
    - If target is higher (1.5x-4x): resample up
    - If within tolerance: skip
    - If target is lower: decimate to target

    Args:
        element: The SceneElement to adjust
        reference_volume: The reference volume whose density to match
        tolerance: How close is "close enough" (0.2 = within 20%)

    Returns:
        Action taken: "subdivided", "decimated", "resampled", or "skipped"
    """
    element.selectOne()

    if not element.isSculptObject():
        print(
            f"[SmartDensity] '{element.name()}' is not a sculpt object, skipping")
        return "skipped"

    vol: coat.Volume = element.Volume()

    # Ensure surface mode
    if not vol.isSurface():
        vol.toSurface()
        wait_frames(MESH_OP_WAIT_FRAMES)

    target_polycount: int = calculate_target_polycount_by_scale(
        reference_volume, vol)
    current_polycount: int = vol.getPolycount()

    print(
        f"[SmartDensity] '{element.name()}': current={current_polycount:,}, target={target_polycount:,}")

    if target_polycount <= 0 or current_polycount <= 0:
        print("[SmartDensity] Invalid polycount, skipping")
        return "skipped"

    polycount_ratio: float = target_polycount / current_polycount
    print(f"[SmartDensity] Ratio: {polycount_ratio:.2f} (target/current)")

    # Check if within tolerance (e.g., 0.8 to 1.2 for 20% tolerance)
    if (1.0 - tolerance) <= polycount_ratio <= (1.0 + tolerance):
        print(
            f"[SmartDensity] Skipped '{element.name()}' - ratio {polycount_ratio:.2f} within tolerance")
        return "skipped"

    if polycount_ratio < 1.0:
        # Need to reduce - use decimate
        reduction_percent: float = (1.0 - polycount_ratio) * 100.0
        print(
            f"[SmartDensity] Decimating by {reduction_percent:.1f}% (keeping {polycount_ratio*100:.1f}%)")

        decimate_by_percent(reduction_percent)
        wait_frames(MESH_OP_WAIT_FRAMES)

        final_polycount: int = vol.getPolycount()
        print(
            f"[SmartDensity] Decimated '{element.name()}': {current_polycount:,} -> {final_polycount:,} (target was {target_polycount:,})")
        return "decimated"

    elif polycount_ratio > 4.0:
        # Need to increase significantly - subdivide then decimate to exact target
        subdivide_count: int = int(math.ceil(math.log(polycount_ratio, 4)))
        subdivide_count = min(subdivide_count, 4)  # Cap at 4 subdivisions
        subdivide_count = max(subdivide_count, 1)

        print(
            f"[SmartDensity] Subdividing {subdivide_count}x to increase from {current_polycount:,}")

        for i in range(subdivide_count):
            subdivide_once()
            wait_frames(MESH_OP_WAIT_FRAMES)
            print(
                f"[SmartDensity] After subdivide {i+1}: {vol.getPolycount():,} polys")

        # Now we likely overshot - decimate to exact target
        new_polycount: int = vol.getPolycount()
        if new_polycount > target_polycount:
            reduction_ratio: float = target_polycount / new_polycount
            reduction_percent: float = (1.0 - reduction_ratio) * 100.0
            print(
                f"[SmartDensity] Decimating by {reduction_percent:.1f}% to reach {target_polycount:,}")
            decimate_by_percent(reduction_percent)
            wait_frames(MESH_OP_WAIT_FRAMES)
            final_polycount: int = vol.getPolycount()
            print(
                f"[SmartDensity] Subdivided+decimated '{element.name()}': {current_polycount:,} -> {final_polycount:,}")
        else:
            print(
                f"[SmartDensity] Subdivided '{element.name()}' {subdivide_count}x: {current_polycount:,} -> {new_polycount:,}")
        return "subdivided"

    else:
        # Moderate increase (1x to 4x) - use resample
        print(
            f"[SmartDensity] Resampling up from {current_polycount:,} to {target_polycount:,}")
        resample_to_target(current_polycount, target_polycount)
        wait_frames(MESH_OP_WAIT_FRAMES)
        final_polycount: int = vol.getPolycount()
        print(
            f"[SmartDensity] Resampled '{element.name()}': {current_polycount:,} -> {final_polycount:,}")
        return "resampled"
