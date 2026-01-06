"""
LKS UI - Visibility Tools Section.

Collapsible section for show/hide visibility operations with label + scope button pattern.

Usage:
    from ui.ui_collapsible_visibility_tools import create_visibility_section
    section = create_visibility_section(log_success, log_error, refresh_tree)
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


def create_visibility_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create visibility tools section with label + scope button pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="👁️ Visibility", color="#90a4ae", collapsed=True)

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

    def on_invert() -> None:
        try:
            from ops.SculptObject_Visibility import main as op_visibility, VisibilityMode
            from utils.scope_utils import Scope
            count = op_visibility(scope=Scope.ALL, mode=VisibilityMode.INVERT)
            log_success(f"Inverted visibility on {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Invert visibility failed: {e}")

    def on_isolate_visible() -> None:
        """Isolate visibility: show selection + parents, hide everything else."""
        try:
            from utils.scene_api import SceneAPI
            from utils.SceneElement_visibility_utils import isolate_visible_with_parents
            selection = SceneAPI.get_selected_elements()
            if not selection:
                log_error("No objects selected to isolate")
                return
            all_elements = SceneAPI.collect_all_sculpt_objects()
            count = isolate_visible_with_parents(all_elements, selection)
            log_success(f"Isolated {len(selection)}, hid {count} others")
            refresh_tree()
        except Exception as e:
            log_error(f"Isolate visible failed: {e}")

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

    layout = section.content_layout

    # --- Hide row: Label + [Sel][Tree][All] ---
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
    layout.addWidget(hide_container)

    # --- Show row: Label + [Sel][Tree][All] ---
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
    layout.addWidget(show_container)

    # --- Special buttons: [Invert][Isolate][Toggle] ---
    special_grid = ButtonGrid(columns=3)
    special_grid.add_button("🔄 Invert", on_invert,
                            "Invert all visibility states")
    special_grid.add_button("Isolate", on_isolate_visible,
                            "Hide all except selection + parents")
    special_grid.add_button("Toggle", on_toggle_isolate_visible,
                            "Toggle isolation (show all / isolate)")
    layout.addWidget(special_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_visibility_section(*args, **kwargs):  # type: ignore
        return None
