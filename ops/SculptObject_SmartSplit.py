"""
SculptObject_SmartSplit Operator

Smart split operator that adapts based on object mode:
- Voxel mode: Separates hidden geometry directly
- Surface mode: Hides masked/frozen area, then separates hidden geometry

Closes holes on both original and newly created elements in both modes.
Uses scope resolution to determine which element(s) to split.
"""
import coat
from utils.scene_api import SceneAPI, SelectionAPI
from utils.scope_utils import Scope, resolve_scope
from utils.coat_ui_utils import wait_frames, show_message, show_error


# =============================================================================
# MAGIC UI STRINGS
# =============================================================================

CMD_HIDE_FROZEN_AREA: str = "$HideFrozenArea"
CMD_SEPARATE_HIDDEN: str = "$SeparateHidden"
CMD_DELETE_HIDDEN: str = "$DeleteHidden"
CMD_CLOSE_HOLES: str = "$CloseSurfHoles"
CMD_DIALOG_OK: str = "$DialogButton#1"
SETTING_MAX_CONTOUR_LENGTH: str = "$InputContourLength::MaxContourLength"


# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_WAIT_FRAMES: int = 4
DEFAULT_MAX_CONTOUR_LENGTH: int = 999999  # Large value to close all holes


# =============================================================================
# DIALOG CONFIGURATORS
# =============================================================================

def _configure_close_holes_dialog() -> None:
    """Configure and confirm the close holes dialog."""
    coat.ui.setEditBoxValue(SETTING_MAX_CONTOUR_LENGTH,
                            DEFAULT_MAX_CONTOUR_LENGTH)
    coat.ui.cmd(CMD_DIALOG_OK)


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    close_holes: bool = True,
    preserve_selection: bool = True,
) -> int:
    """
    Smart split: adapts based on voxel vs surface mode.

    Voxel mode: Separates hidden geometry directly
    Surface mode: Hides masked/frozen area first, then separates

    Args:
        scope: Which object(s) to operate on
        close_holes: Whether to close holes on both original and new elements
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of new elements created
    """
    # Save selection for restoration
    saved_selection: list[coat.SceneElement] = []
    if preserve_selection:
        saved_selection = SelectionAPI.save_selection()

    # Get elements to process
    elements: list[coat.SceneElement] = resolve_scope(scope)
    if not elements:
        show_error("No object selected", 2000)
        return 0

    total_new: int = 0
    voxel_count: int = 0
    surface_count: int = 0

    for element in elements:
        if not element.isSculptObject():
            continue

        vol: coat.Volume = element.Volume()

        # Determine mode and call appropriate split method
        if vol.isVoxelized():
            new_count: int = _split_voxel_element(element, close_holes)
            voxel_count += 1
        elif vol.isSurface():
            new_count: int = _split_surface_element(element, close_holes)
            surface_count += 1
        else:
            # Unknown mode, skip
            continue

        total_new += new_count

    # Restore selection
    if preserve_selection and saved_selection:
        SelectionAPI.restore_selection(saved_selection)

    # Generate informative message based on what was processed
    if total_new > 0:
        mode_info: str = ""
        if voxel_count > 0 and surface_count > 0:
            mode_info = " (mixed: voxel split hidden, surface split masked/hidden + closed holes)"
        elif voxel_count > 0:
            mode_info = " (voxel mode: split hidden volumes)"
        elif surface_count > 0:
            mode_info = " (surface mode: split masked/hidden + closed holes)"
        
        show_message(f"Smart split created {total_new} new object(s){mode_info}", 3000)
    else:
        show_message("No hidden/masked area to split", 2000)

    return total_new


# =============================================================================
# MODE-SPECIFIC SPLIT FUNCTIONS
# =============================================================================

def _split_voxel_element(element: coat.SceneElement, close_holes: bool) -> int:
    """
    Split voxel mode element (separates hidden geometry directly).

    Args:
        element: The voxel element to split
        close_holes: Whether to close holes on resulting elements

    Returns:
        Number of new elements created
    """
    # Cache parent and existing children BEFORE split
    parent: coat.SceneElement = element.parent()

    existing_children: list[coat.SceneElement] = []
    for i in range(parent.childCount()):
        existing_children.append(parent.child(i))

    # Ensure element is selected
    element.selectOne()

    # In voxel mode: separate hidden, then delete hidden from original
    coat.ui.cmd(CMD_SEPARATE_HIDDEN)
    wait_frames(DEFAULT_WAIT_FRAMES)

    # Delete the hidden geometry from the original object
    # (it's now a separate object but still hidden in the source)
    element.selectOne()
    coat.ui.cmd(CMD_DELETE_HIDDEN)
    wait_frames(DEFAULT_WAIT_FRAMES)

    # Find newly created elements
    new_elements: list[coat.SceneElement] = []
    for i in range(parent.childCount()):
        child: coat.SceneElement = parent.child(i)
        is_existing: bool = False
        for existing in existing_children:
            if child == existing:
                is_existing = True
                break
        if not is_existing:
            new_elements.append(child)

    # Close holes on original element and new elements if requested
    if close_holes and new_elements:
        # Close holes on original element
        element.selectOne()
        wait_frames(1)
        coat.ui.cmd(CMD_CLOSE_HOLES, _configure_close_holes_dialog)
        wait_frames(DEFAULT_WAIT_FRAMES)

        # Close holes on each new element
        for new_elem in new_elements:
            new_elem.selectOne()
            wait_frames(1)
            coat.ui.cmd(CMD_CLOSE_HOLES, _configure_close_holes_dialog)
            wait_frames(DEFAULT_WAIT_FRAMES)

    return len(new_elements)


def _split_surface_element(element: coat.SceneElement, close_holes: bool) -> int:
    """
    Split surface mode element (hides masked/frozen, then separates hidden).

    Args:
        element: The surface element to split
        close_holes: Whether to close holes on resulting elements

    Returns:
        Number of new elements created
    """
    # Cache parent and existing children BEFORE split
    parent: coat.SceneElement = element.parent()

    existing_children: list[coat.SceneElement] = []
    for i in range(parent.childCount()):
        existing_children.append(parent.child(i))

    # Ensure element is selected (already in surface mode)
    element.selectOne()

    # In surface mode: hide frozen/masked area first, then separate
    coat.ui.cmd(CMD_HIDE_FROZEN_AREA)
    coat.ui.cmd(CMD_SEPARATE_HIDDEN)
    wait_frames(DEFAULT_WAIT_FRAMES)

    # Find newly created elements
    new_elements: list[coat.SceneElement] = []
    for i in range(parent.childCount()):
        child: coat.SceneElement = parent.child(i)
        is_existing: bool = False
        for existing in existing_children:
            if child == existing:
                is_existing = True
                break
        if not is_existing:
            new_elements.append(child)

    # Close holes on original element and new elements if requested
    if close_holes:
        # Close holes on original element
        element.selectOne()
        wait_frames(1)
        coat.ui.cmd(CMD_CLOSE_HOLES, _configure_close_holes_dialog)
        wait_frames(DEFAULT_WAIT_FRAMES)

        # Close holes on each new element
        for new_elem in new_elements:
            new_elem.selectOne()
            wait_frames(1)
            coat.ui.cmd(CMD_CLOSE_HOLES, _configure_close_holes_dialog)
            wait_frames(DEFAULT_WAIT_FRAMES)

    return len(new_elements)
