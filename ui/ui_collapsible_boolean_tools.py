"""
LKS UI - Boolean Tools Collapsible Section.

A collapsible section containing voxel boolean operations:
- Create boolean children (Subtract, Intersect, Union)

Usage:
    from ui.ui_collapsible_boolean_tools import create_boolean_section
    section = create_boolean_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# BOOLEAN TOOLS SECTION FACTORY
# =============================================================================

def create_boolean_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible boolean tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with boolean tools
    """
    section = CollapsibleSection(
        title="Booleans", collapsed=True, state_key="section_booleans")
    layout = section.content_layout

    # --- VoxBool Operations ---
    def voxbool_subtract() -> None:
        try:
            from ops.SculptObject_VoxBool import subtract
            child = subtract()
            if child:
                log_success(f"Created subtract: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create subtract child")
        except Exception as e:
            log_error(f"VoxBool subtract failed: {e}")

    def voxbool_intersect() -> None:
        try:
            from ops.SculptObject_VoxBool import intersect
            child = intersect()
            if child:
                log_success(f"Created intersect: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create intersect child")
        except Exception as e:
            log_error(f"VoxBool intersect failed: {e}")

    def voxbool_union() -> None:
        try:
            from ops.SculptObject_VoxBool import union
            child = union()
            if child:
                log_success(f"Created union: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create union child")
        except Exception as e:
            log_error(f"VoxBool union failed: {e}")

    grid = ButtonGrid(columns=3)
    grid.add_button("Subtract", voxbool_subtract,
                    "Create subtract boolean child")
    grid.add_button("Intersect", voxbool_intersect,
                    "Create intersect boolean child")
    grid.add_button("Union", voxbool_union,
                    "Create union boolean child")
    layout.addWidget(grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_boolean_section(*args, **kwargs):  # type: ignore
        return None
