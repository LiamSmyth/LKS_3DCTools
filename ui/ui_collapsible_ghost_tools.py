"""
LKS UI - Ghost Tools Collapsible Section.

A collapsible section containing ghost operations with:
- Ghost scope buttons (Sel/Tree/All)
- Unghost scope buttons
- Special operations (Invert, Isolate, Toggle)

Usage:
    from ui.ui_collapsible_ghost_tools import create_ghost_section
    section = create_ghost_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
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


# =============================================================================
# GHOST SECTION FACTORY
# =============================================================================

def create_ghost_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible ghost tools section with label + scope button pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with ghost tools
    """
    section = CollapsibleSection(
        title="👻 Ghost", color="#b0bec5", collapsed=True)
    layout = section.content_layout

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

    # --- Ghost row: Label + [Sel][Tree][All] ---
    ghost_row = QHBoxLayout()
    ghost_row.setContentsMargins(0, 0, 0, 0)
    ghost_label = QLabel("Ghost:")
    ghost_label.setMinimumWidth(60)
    ghost_row.addWidget(ghost_label)

    ghost_grid = ButtonGrid(columns=3)
    ghost_grid.add_button("Sel", lambda: ghost(
        "CURRENT", True), "Ghost selected")
    ghost_grid.add_button("Tree", lambda: ghost("TREE", True), "Ghost subtree")
    ghost_grid.add_button("All", lambda: ghost("ALL", True), "Ghost all")
    ghost_row.addWidget(ghost_grid)

    ghost_container = QWidget()
    ghost_container.setLayout(ghost_row)
    ghost_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(ghost_container)

    # --- Unghost row: Label + [Sel][Tree][All] ---
    unghost_row = QHBoxLayout()
    unghost_row.setContentsMargins(0, 0, 0, 0)
    unghost_label = QLabel("Unghost:")
    unghost_label.setMinimumWidth(60)
    unghost_row.addWidget(unghost_label)

    unghost_grid = ButtonGrid(columns=3)
    unghost_grid.add_button("Sel", lambda: ghost(
        "CURRENT", False), "Unghost selected")
    unghost_grid.add_button("Tree", lambda: ghost(
        "TREE", False), "Unghost subtree")
    unghost_grid.add_button("All", lambda: ghost("ALL", False), "Unghost all")
    unghost_row.addWidget(unghost_grid)

    unghost_container = QWidget()
    unghost_container.setLayout(unghost_row)
    unghost_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(unghost_container)

    # --- Special row: [Invert][Isolate][Toggle] ---
    def invert_ghost() -> None:
        try:
            from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
            from utils.scope_utils import Scope
            set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT)
            log_success("Inverted ghost states")
            refresh_tree()
        except Exception as e:
            log_error(f"Invert ghost failed: {e}")

    def isolate_ghost() -> None:
        try:
            from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
            from utils.scope_utils import Scope
            set_ghost(scope=Scope.CURRENT, mode=GhostMode.ISOLATE)
            log_success("Ghost isolated selected")
            refresh_tree()
        except Exception as e:
            log_error(f"Isolate ghost failed: {e}")

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

    special_grid = ButtonGrid(columns=3)
    special_grid.add_button("Invert", invert_ghost, "Invert ghost states")
    special_grid.add_button("Isolate", isolate_ghost,
                            "Ghost all except selected")
    special_grid.add_button("Toggle", toggle_isolate_ghost,
                            "Toggle ghost isolation (unghost all / isolate)")
    layout.addWidget(special_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_ghost_section(*args, **kwargs):  # type: ignore
        return None

if not HAS_QT:
    def create_ghost_section(*args, **kwargs):  # type: ignore
        return None
