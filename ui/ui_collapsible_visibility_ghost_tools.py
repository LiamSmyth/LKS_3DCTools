"""
LKS UI - Visibility & Ghost Tools Section (Merged).

Collapsible section combining visibility and ghost operations in a 2-column layout.

Usage:
    from ui.ui_collapsible_visibility_ghost_tools import create_visibility_ghost_section
    section = create_visibility_ghost_section(log_success, log_error, refresh_tree)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


def create_visibility_ghost_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create merged visibility + ghost section with 2-column layout.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="👁️👻 Visibility & Ghost", collapsed=False, state_key="section_visibility_ghost")

    # Two-column container
    columns_layout = QHBoxLayout()
    columns_layout.setContentsMargins(0, 0, 0, 0)
    columns_layout.setSpacing(8)

    # --- LEFT COLUMN: Visibility ---
    left_column = QFrame()
    left_column.setStyleSheet("""
        QFrame {
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
        }
    """)
    left_layout = QVBoxLayout(left_column)
    left_layout.setContentsMargins(6, 6, 6, 6)
    left_layout.setSpacing(4)

    # Visibility header
    vis_header = QLabel("Visibility")
    vis_header.setStyleSheet("font-weight: bold; color: #90caf9; background: transparent;")
    left_layout.addWidget(vis_header)

    def on_visibility(scope_name: str, visible: bool) -> None:
        try:
            from ops.SculptObject_Visibility import main as op_visibility
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            count = op_visibility(scope=scope, visible=visible)
            action = "Showed" if visible else "Hid"
            log_success(f"{action} {count} objects ({scope_name.lower()})")
            refresh_tree()
        except Exception as e:
            log_error(f"Visibility operation failed: {e}")

    def on_invert_visibility() -> None:
        try:
            from ops.SculptObject_Visibility import main as op_visibility, VisibilityMode
            from utils.scope_utils import Scope
            count = op_visibility(scope=Scope.ALL, mode=VisibilityMode.INVERT)
            log_success(f"Inverted visibility on {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Invert visibility failed: {e}")

    def on_toggle_isolate_visible() -> None:
        """Toggle visibility isolation: if isolated, show all; else isolate."""
        try:
            from utils.scene_api import SceneAPI
            from utils.SceneElement_visibility_utils import toggle_visibility_isolation
            selection = SceneAPI.get_selected_elements()
            if not selection:
                log_error("No objects selected for toggle isolate")
                return
            all_elements = SceneAPI.collect_all_sculpt_objects()
            is_isolated, count = toggle_visibility_isolation(
                all_elements, selection)
            if is_isolated:
                log_success(f"Isolated visibility, hid {count} objects")
            else:
                log_success(f"Restored visibility on {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Toggle isolate failed: {e}")

    # Hide row
    hide_row = QHBoxLayout()
    hide_row.setContentsMargins(0, 0, 0, 0)
    hide_label = QLabel("Hide:")
    hide_label.setMinimumWidth(45)
    hide_row.addWidget(hide_label)

    hide_grid = ButtonGrid(columns=3)
    hide_grid.add_button("☝️", lambda: on_visibility(
        "CURRENT", False), "Hide selected")
    hide_grid.add_button("🌳", lambda: on_visibility(
        "TREE", False), "Hide subtree")
    hide_grid.add_button(
        "🌎", lambda: on_visibility("ALL", False), "Hide all")
    hide_row.addWidget(hide_grid)

    hide_container = QWidget()
    hide_container.setLayout(hide_row)
    hide_container.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(hide_container)

    # Show row
    show_row = QHBoxLayout()
    show_row.setContentsMargins(0, 0, 0, 0)
    show_label = QLabel("Show:")
    show_label.setMinimumWidth(45)
    show_row.addWidget(show_label)

    show_grid = ButtonGrid(columns=3)
    show_grid.add_button("☝️", lambda: on_visibility(
        "CURRENT", True), "Show selected")
    show_grid.add_button("🌳", lambda: on_visibility(
        "TREE", True), "Show subtree")
    show_grid.add_button("🌎", lambda: on_visibility("ALL", True), "Show all")
    show_row.addWidget(show_grid)

    show_container = QWidget()
    show_container.setLayout(show_row)
    show_container.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(show_container)

    # Special buttons: [Invert][Toggle Isolate]
    special_grid = ButtonGrid(columns=2)
    special_grid.add_button("Invert", on_invert_visibility,
                            "Invert all visibility states")
    special_grid.add_button("Toggle Isolate", on_toggle_isolate_visible,
                            "Toggle isolation (show all / isolate)")
    left_layout.addWidget(special_grid)

    columns_layout.addWidget(left_column)

    # --- RIGHT COLUMN: Ghost ---
    right_column = QFrame()
    right_column.setStyleSheet("""
        QFrame {
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
        }
    """)
    right_layout = QVBoxLayout(right_column)
    right_layout.setContentsMargins(6, 6, 6, 6)
    right_layout.setSpacing(4)

    # Ghost header
    ghost_header = QLabel("Ghost")
    ghost_header.setStyleSheet("font-weight: bold; color: #90caf9; background: transparent;")
    right_layout.addWidget(ghost_header)

    def ghost(scope_name: str, ghosted: bool) -> None:
        try:
            from ops.SculptObject_SetGhost import main as set_ghost
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            set_ghost(scope=scope, ghost=ghosted)
            action: str = "Ghosted" if ghosted else "Unghosted"
            log_success(f"{action} {scope_name.lower()}")
            refresh_tree()
        except Exception as e:
            log_error(f"Ghost failed: {e}")

    # Ghost row
    ghost_row = QHBoxLayout()
    ghost_row.setContentsMargins(0, 0, 0, 0)
    ghost_label = QLabel("Ghost:")
    ghost_label.setMinimumWidth(60)
    ghost_row.addWidget(ghost_label)

    ghost_grid = ButtonGrid(columns=3)
    ghost_grid.add_button("☝️", lambda: ghost(
        "CURRENT", True), "Ghost selected")
    ghost_grid.add_button("🌳", lambda: ghost("TREE", True), "Ghost subtree")
    ghost_grid.add_button("🌎", lambda: ghost("ALL", True), "Ghost all")
    ghost_row.addWidget(ghost_grid)

    ghost_container = QWidget()
    ghost_container.setLayout(ghost_row)
    ghost_container.setContentsMargins(0, 0, 0, 0)
    right_layout.addWidget(ghost_container)

    # Unghost row
    unghost_row = QHBoxLayout()
    unghost_row.setContentsMargins(0, 0, 0, 0)
    unghost_label = QLabel("Unghost:")
    unghost_label.setMinimumWidth(60)
    unghost_row.addWidget(unghost_label)

    unghost_grid = ButtonGrid(columns=3)
    unghost_grid.add_button("☝️", lambda: ghost(
        "CURRENT", False), "Unghost selected")
    unghost_grid.add_button("🌳", lambda: ghost(
        "TREE", False), "Unghost subtree")
    unghost_grid.add_button("🌎", lambda: ghost("ALL", False), "Unghost all")
    unghost_row.addWidget(unghost_grid)

    unghost_container = QWidget()
    unghost_container.setLayout(unghost_row)
    unghost_container.setContentsMargins(0, 0, 0, 0)
    right_layout.addWidget(unghost_container)

    # Special row: [Invert][Toggle Isolate]
    def invert_ghost() -> None:
        try:
            from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
            from utils.scope_utils import Scope
            set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT)
            log_success("Inverted ghost states")
            refresh_tree()
        except Exception as e:
            log_error(f"Invert ghost failed: {e}")

    def toggle_isolate_ghost() -> None:
        """Toggle ghost isolation: if isolated, unghost all; else ghost isolate."""
        try:
            from utils.scene_api import SceneAPI
            from utils.SceneElement_visibility_utils import toggle_ghost_isolation
            selection = SceneAPI.get_selected_elements()
            if not selection:
                log_error("No objects selected for toggle isolate")
                return
            all_elements = SceneAPI.collect_all_sculpt_objects()
            is_isolated, count = toggle_ghost_isolation(
                all_elements, selection)
            if is_isolated:
                log_success(f"Ghost isolated, ghosted {count} objects")
            else:
                log_success(f"Unghosted {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Toggle isolate ghost failed: {e}")

    ghost_special_grid = ButtonGrid(columns=2)
    ghost_special_grid.add_button("🔄", invert_ghost, "Invert ghost states")
    ghost_special_grid.add_button("Toggle Isolate", toggle_isolate_ghost,
                                  "Toggle ghost isolation (unghost all / isolate)")
    right_layout.addWidget(ghost_special_grid)

    columns_layout.addWidget(right_column)

    # Add columns to section
    columns_container = QWidget()
    columns_container.setLayout(columns_layout)
    columns_container.setContentsMargins(0, 0, 0, 0)
    section.content_layout.addWidget(columns_container)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_visibility_ghost_section(*args, **kwargs):  # type: ignore
        return None
