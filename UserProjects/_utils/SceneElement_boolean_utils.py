"""
SceneElement Boolean Utilities - Live boolean operations on SceneElements.

Creates child boolean volumes for sculpt objects. Requires parent to be in voxel mode.

Pattern:
    from _utils.SceneElement_boolean_utils import create_boolean_child, BooleanMode
    
    create_boolean_child(parent_element, BooleanMode.SUBTRACT)
"""
import coat
from enum import IntEnum

from _utils.coat_ui_utils import wait_frames, show_message, CMD_DIALOG_OK


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

    Args:
        parent: The parent SceneElement to create boolean child for
        mode: The boolean mode (SUBTRACT, INTERSECT, UNION)
        apply_extrusion: Whether to apply voxel extrusion (useful for INTERSECT)
        extrusion_amount: Amount of extrusion if apply_extrusion is True
        clear_child: Whether to clear the child's geometry (for SUBTRACT/UNION)

    Returns:
        The created boolean child element, or None if failed
    """
    if not parent:
        show_message("No parent element provided", 3000)
        return None

    # Duplicate parent
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

    # Apply extrusion if requested (typically for INTERSECT)
    if apply_extrusion:
        _apply_voxel_extrusion(extrusion_amount)
    elif clear_child:
        # Clear geometry for subtract/union (user will sculpt new geometry)
        child.clear()

    # Set boolean mode on the volume
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
