"""
LKS UI - Mode Conversion Tools Section.

Collapsible section for converting between surface and voxel modes.

Usage:
    from ui.ui_collapsible_mode_tools import create_mode_section
    section = create_mode_section(log_success, log_error, refresh_tree)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


def create_mode_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create mode conversion section with label + scope buttons pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="⚙️ Mode Convert", collapsed=True, state_key="section_mode")

    def on_convert(scope_name: str, to_voxels: bool) -> None:
        try:
            from ops.SculptObject_ModeConvert import main as op_mode, ConvertMode
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            mode = ConvertMode.TO_VOXELS if to_voxels else ConvertMode.TO_SURFACE
            op_mode(scope=scope, mode=mode)
            mode_str = "voxels" if to_voxels else "surface"
            log_success(f"Converted {scope_name.lower()} to {mode_str}")
            refresh_tree()
        except Exception as e:
            log_error(f"Mode convert failed: {e}")

    # --- To Surface row ---
    surf_row = QHBoxLayout()
    surf_row.setContentsMargins(0, 0, 0, 0)
    surf_label = QLabel("To Surface:")
    surf_label.setMinimumWidth(80)
    surf_row.addWidget(surf_label)

    surf_grid = ButtonGrid(columns=3)
    surf_grid.add_button("Sel", lambda: on_convert(
        "CURRENT", False), "Convert selected to surface")
    surf_grid.add_button("Tree", lambda: on_convert(
        "TREE", False), "Convert subtree to surface")
    surf_grid.add_button("All", lambda: on_convert(
        "ALL", False), "Convert all to surface")
    surf_row.addWidget(surf_grid)

    surf_container = QWidget()
    surf_container.setLayout(surf_row)
    surf_container.setContentsMargins(0, 0, 0, 0)
    section.content_layout.addWidget(surf_container)

    # --- To Voxels row ---
    vox_row = QHBoxLayout()
    vox_row.setContentsMargins(0, 0, 0, 0)
    vox_label = QLabel("To Voxels:")
    vox_label.setMinimumWidth(80)
    vox_row.addWidget(vox_label)

    vox_grid = ButtonGrid(columns=3)
    vox_grid.add_button("Sel", lambda: on_convert(
        "CURRENT", True), "Convert selected to voxels")
    vox_grid.add_button("Tree", lambda: on_convert(
        "TREE", True), "Convert subtree to voxels")
    vox_grid.add_button("All", lambda: on_convert(
        "ALL", True), "Convert all to voxels")
    vox_row.addWidget(vox_grid)

    vox_container = QWidget()
    vox_container.setLayout(vox_row)
    vox_container.setContentsMargins(0, 0, 0, 0)
    section.content_layout.addWidget(vox_container)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_mode_section(*args, **kwargs):  # type: ignore
        return None
