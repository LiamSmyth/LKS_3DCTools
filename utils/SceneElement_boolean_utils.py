"""
SceneElement Boolean Utilities - Live boolean operations on SceneElements.

Creates child boolean volumes for sculpt objects. Requires parent to be in voxel mode.

Pattern:
    from utils.SceneElement_boolean_utils import create_boolean_child, BooleanMode
    
    create_boolean_child(parent_element, BooleanMode.SUBTRACT)
"""
import coat
from enum import IntEnum

from utils.coat_ui_utils import wait_frames, show_message, show_error, CMD_DIALOG_OK
from utils.Volume_mode_utils import ensure_voxel_mode


# =============================================================================
# BOOLEAN MAGIC UI STRINGS
# =============================================================================

CMD_EXTRUDE_VO: str = "$ExtrudeVO"
SETTING_EXTRUSION: str = "$ExtrudeParams::Extrusion"


# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_EXTRUSION: float = 0.2
BOOLEAN_WAIT_FRAMES: int = 4


# =============================================================================
# BOOLEAN MODE ENUM
# =============================================================================

class BooleanMode(IntEnum):
    """Live boolean operation modes (matches coat Volume.assignLiveBooleans)."""
    NONE = 0       # Stop live booleans
    SUBTRACT = 1   # Subtract from parent
    INTERSECT = 2  # Intersect with parent
    UNION = 3      # Union with parent


# Mode to suffix mapping
BOOLEAN_SUFFIXES: dict[BooleanMode, str] = {
    BooleanMode.NONE: "",
    BooleanMode.SUBTRACT: "_Subtract",
    BooleanMode.INTERSECT: "_Intersect",
    BooleanMode.UNION: "_Union",
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def create_boolean_child(
    parent: coat.SceneElement,
    mode: BooleanMode,
    apply_extrusion: bool = False,
    extrusion_amount: float = DEFAULT_EXTRUSION,
    clear_child: bool = True,
) -> coat.SceneElement | None:
    """
    Create a child element with live boolean applied.

    Duplicates the parent, parents the clone under it, and sets up live boolean.
    Parent must be in voxel mode for booleans to work.

    CRITICAL: For INTERSECT, extrusion MUST be applied BEFORE setting boolean mode
    to prevent 3DCoat crash. For SUBTRACT/UNION, we clear child content first.

    Args:
        parent: The parent SceneElement to create boolean child for
        mode: The boolean mode (SUBTRACT, INTERSECT, UNION)
        apply_extrusion: Whether to apply voxel extrusion (required for INTERSECT)
        extrusion_amount: Amount of extrusion if apply_extrusion is True
        clear_child: Whether to clear the child's geometry (for SUBTRACT/UNION)

    Returns:
        The created boolean child element, or None if failed
    """
    if not parent:
        show_message("No parent element provided", 3000)
        return None

    # Ensure parent is a sculpt object
    if not parent.isSculptObject():
        show_error("Parent must be a sculpt object", 3000)
        return None

    # Ensure parent is in voxel mode (required for live booleans)
    parent_vol: coat.Volume = parent.Volume()
    if parent_vol.isSurface():
        show_message("Converting parent to voxel mode...", 2000)
        ensure_voxel_mode(parent_vol)
        wait_frames(BOOLEAN_WAIT_FRAMES)

    # Duplicate parent (child inherits voxel mode from parent)
    child: coat.SceneElement = parent.duplicate()
    wait_frames(BOOLEAN_WAIT_FRAMES)

    # Remove any children of the cloned element
    if child.childCount() > 0:
        child.removeSubtree()
        wait_frames(BOOLEAN_WAIT_FRAMES)

    # Rename with suffix
    suffix: str = BOOLEAN_SUFFIXES.get(mode, "")
    child.rename(f"{parent.name()}{suffix}")
    wait_frames(BOOLEAN_WAIT_FRAMES)

    # Select and parent under original
    child.selectOne()
    wait_frames(BOOLEAN_WAIT_FRAMES)
    child.changeParent(parent)
    wait_frames(BOOLEAN_WAIT_FRAMES)

    # For INTERSECT: extrusion MUST be applied BEFORE setting boolean mode
    # For SUBTRACT/UNION: clear content first
    if apply_extrusion:
        # Apply extrusion first (CRITICAL: before assignLiveBooleans to avoid crash)
        _apply_voxel_extrusion(extrusion_amount)
        wait_frames(BOOLEAN_WAIT_FRAMES)
    elif clear_child:
        # Clear geometry for subtract/union (user will sculpt new geometry)
        child.clear()
        wait_frames(BOOLEAN_WAIT_FRAMES)

    # Now set boolean mode (after extrusion/clear to avoid crash)
    vol: coat.Volume = child.Volume()
    vol.assignLiveBooleans(int(mode))

    return child


def _apply_voxel_extrusion(amount: float = DEFAULT_EXTRUSION) -> None:
    """
    Apply voxel extrusion to current selection.

    Args:
        amount: Extrusion amount
    """
    def extrude_configurator() -> None:
        wait_frames(BOOLEAN_WAIT_FRAMES)
        coat.ui.setSliderValue(SETTING_EXTRUSION, amount)
        wait_frames(BOOLEAN_WAIT_FRAMES)
        coat.ui.cmd(CMD_DIALOG_OK)

    coat.ui.cmd(CMD_EXTRUDE_VO, extrude_configurator)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_subtract_child(parent: coat.SceneElement) -> coat.SceneElement | None:
    """Create a subtract boolean child (empty, ready for sculpting)."""
    return create_boolean_child(parent, BooleanMode.SUBTRACT, clear_child=True)


def create_intersect_child(
    parent: coat.SceneElement,
    extrusion: float = DEFAULT_EXTRUSION
) -> coat.SceneElement | None:
    """Create an intersect boolean child with extrusion applied."""
    return create_boolean_child(
        parent,
        BooleanMode.INTERSECT,
        apply_extrusion=True,
        extrusion_amount=extrusion
    )


def create_union_child(parent: coat.SceneElement) -> coat.SceneElement | None:
    """Create a union boolean child (empty, ready for sculpting)."""
    return create_boolean_child(parent, BooleanMode.UNION, clear_child=True)


def stop_boolean(element: coat.SceneElement) -> None:
    """Remove live boolean from an element."""
    vol: coat.Volume = element.Volume()
    vol.assignLiveBooleans(int(BooleanMode.NONE))
