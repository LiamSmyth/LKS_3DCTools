"""
SculptObject_RemeshResymm Operator

Safely remesh and symmetrize sculpt objects while preserving polycount.

Process:
1. Resample at higher detail if surface mode (4x scale)
2. Convert to voxels
3. Make symmetrical
4. Convert back to surface
5. Decimate back to original polycount if needed

Uses scope resolution to determine which elements to process.
"""
import coat
from utils.scene_api import SceneAPI
from utils.scope_utils import Scope, resolve_scope
from utils.Volume_resample_utils import execute_resample
from utils.Volume_decimate_utils import decimate_to_target
from utils.Volume_subdivide_utils import make_symmetrical
from utils.Scene_cleanup_utils import cleanup_after_mesh_operation
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_RESAMPLE_SCALE: float = 4.0
MAX_DECIMATE_ATTEMPTS: int = 3
POLYCOUNT_TOLERANCE: int = 1000


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    resample_scale: float = DEFAULT_RESAMPLE_SCALE,
    preserve_selection: bool = True,
) -> int:
    """
    Remesh and symmetrize sculpt objects.

    Args:
        scope: Which objects to operate on
        resample_scale: Scale factor for resampling before voxelization
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects processed
    """
    from utils.scene_api import SelectionAPI

    # Save selection
    saved_selection: list[coat.SceneElement] = []
    if preserve_selection:
        saved_selection = SelectionAPI.save_selection()

    # Get elements to process
    elements: list[coat.SceneElement] = resolve_scope(scope)
    if not elements:
        show_error("No object selected", 2000)
        return 0

    # Filter to sculpt objects only
    sculpt_objects: list[coat.SceneElement] = [
        el for el in elements if el.isSculptObject()
    ]

    if not sculpt_objects:
        show_error("No sculpt objects in scope", 2000)
        return 0

    count: int = 0
    for element in sculpt_objects:
        success: bool = _remesh_resymm_element(element, resample_scale)
        if success:
            count += 1

    cleanup_after_mesh_operation()

    # Restore selection
    if preserve_selection and saved_selection:
        SelectionAPI.restore_selection(saved_selection)

    show_message(f"Remesh+symm {count} objects", 2000)
    return count


def _remesh_resymm_element(
    element: coat.SceneElement,
    resample_scale: float = DEFAULT_RESAMPLE_SCALE
) -> bool:
    """
    Remesh and symmetrize a single element.

    Args:
        element: The element to process
        resample_scale: Scale factor for resampling

    Returns:
        True if successful
    """
    element.selectOne()
    vol: coat.Volume = element.Volume()
    target_polycount: int = vol.getPolycount()

    if target_polycount <= 0:
        return False

    # Resample to preserve detail if surface (4x scale)
    if not vol.isVoxelized():
        resample_target: int = int(target_polycount * resample_scale)
        execute_resample(target_polycount=resample_target,
                         scale=resample_scale)
        vol.toVoxels()

    # Make symmetrical in voxel mode
    make_symmetrical()

    # Convert back to surface
    vol.toSurface()
    new_polycount: int = vol.getPolycount()

    # Decimate back to target if polycount increased significantly
    attempt: int = 0
    while new_polycount > target_polycount + POLYCOUNT_TOLERANCE and attempt < MAX_DECIMATE_ATTEMPTS:
        # Calculate actual reduction percent needed
        reduction_percent: float = 100.0 * \
            (1.0 - target_polycount / new_polycount)
        # Use percent-based decimation for accuracy
        from utils.Volume_decimate_utils import execute_decimate
        execute_decimate(
            target_polycount=target_polycount,
            reduction_percent=reduction_percent
        )
        new_polycount = vol.getPolycount()
        attempt += 1

    return True
