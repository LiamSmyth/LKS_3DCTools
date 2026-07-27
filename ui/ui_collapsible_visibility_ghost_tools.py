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
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QSizePolicy, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ScopeButtonRow, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.badge_button import _make_icon_from_svg
    from utils.ui.widgets.grid_row_table import GridRowTable, Align
    from utils.menu_action_tooltip import action_menu_tooltip
    from pathlib import Path
    _ICONS_DIR: Path = Path(__file__).resolve().parent.parent / "utils" / "ui" / "data"
    _INVERT_ICON: QIcon = _make_icon_from_svg("invert")
    _VISIBILITY_ICON: QIcon = _make_icon_from_svg("visibility")
    _GHOST_ICON: QIcon = _make_icon_from_svg("ghost")
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 70
_TT_VIS_HIDE = MarkdownFileResource("data/tooltips/visibility_hide.md", base_dir=__file__)
_TT_VIS_SHOW = MarkdownFileResource("data/tooltips/visibility_show.md", base_dir=__file__)
_TT_GHOST_MODE = MarkdownFileResource("data/tooltips/ghost_mode.md", base_dir=__file__)
_TT_GHOST_UNGHOST = MarkdownFileResource("data/tooltips/ghost_unghost.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_visibility_ghost.md", base_dir=__file__)


def create_visibility_ghost_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create merged visibility + ghost section with 2-column layout.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="Visibility & Ghost", icon_name="visibility", collapsed=False, state_key="section_visibility_ghost",
        help_text=_HELP.text,
    )
    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

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
            from utils.hot_reload import reload_if_dev; reload_if_dev()
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
            from utils.hot_reload import reload_if_dev; reload_if_dev()
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

    # Visibility rows (GridRowTable)
    vis_table = GridRowTable()

    hide_scope_row = ScopeButtonRow()
    hide_scope_row.set_callback("sel", lambda: on_visibility("CURRENT", False))
    hide_scope_row.set_callback("tree", lambda: on_visibility("TREE", False))
    hide_scope_row.set_callback("all", lambda: on_visibility("ALL", False))
    hide_scope_row.set_tooltips(
        sel=action_menu_tooltip(
            "Hide selected",
            "SculptObject_Hide_Selected.py",
        ),
        tree="Hide subtree",
        all=action_menu_tooltip(
            "Hide all",
            "SculptObject_Hide_All.py",
        ),
    )
    vis_hide_label = QLabel("Hide:")
    vis_hide_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(vis_hide_label, _TT_VIS_HIDE)
    vis_table.add_cell(0, 0, vis_hide_label, Align.LEFT)
    vis_table.add_cell(0, 1, hide_scope_row)

    show_scope_row = ScopeButtonRow()
    show_scope_row.set_callback("sel", lambda: on_visibility("CURRENT", True))
    show_scope_row.set_callback("tree", lambda: on_visibility("TREE", True))
    show_scope_row.set_callback("all", lambda: on_visibility("ALL", True))
    show_scope_row.set_tooltips(
        sel=action_menu_tooltip(
            "Show selected",
            "SculptObject_Show_Selected.py",
        ),
        tree="Show subtree",
        all=action_menu_tooltip(
            "Show all",
            "SculptObject_Show_All.py",
        ),
    )
    vis_show_label = QLabel("Show:")
    vis_show_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(vis_show_label, _TT_VIS_SHOW)
    vis_table.add_cell(1, 0, vis_show_label, Align.LEFT)
    vis_table.add_cell(1, 1, show_scope_row)

    vis_table.finalize()
    vis_table.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    left_layout.addWidget(vis_table)

    # Special buttons: [Invert][Toggle Isolate]
    special_grid = ButtonGrid(columns=2)
    special_grid.add_button("Invert", on_invert_visibility,
                            "Invert all visibility states", icon=_INVERT_ICON)
    special_grid.add_button(
        "Toggle Isolate",
        on_toggle_isolate_visible,
        action_menu_tooltip(
            "Toggle isolation (show all / isolate)",
            "SculptObject_ToggleIsolateVisible_Selected.py",
        ),
        icon=_VISIBILITY_ICON,
    )
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
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_SetGhost import main as set_ghost
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            action = "Ghosting" if ghosted else "Unghosting"
            ctx = make_iteration_context(action, _log_info, log_success)
            set_ghost(scope=scope, ghost=ghosted,
                      progress_callback=ctx.on_progress)
            action: str = "Ghosted" if ghosted else "Unghosted"
            log_success(f"{action} {scope_name.lower()}")
            refresh_tree()
        except Exception as e:
            log_error(f"Ghost failed: {e}")

    # Ghost rows (GridRowTable)
    ghost_table = GridRowTable()

    ghost_scope_row = ScopeButtonRow()
    ghost_scope_row.set_callback("sel", lambda: ghost("CURRENT", True))
    ghost_scope_row.set_callback("tree", lambda: ghost("TREE", True))
    ghost_scope_row.set_callback("all", lambda: ghost("ALL", True))
    ghost_scope_row.set_tooltips(
        sel=action_menu_tooltip(
            "Ghost selected",
            "SculptObject_Ghost_Selected.py",
        ),
        tree="Ghost subtree",
        all="Ghost all",
    )
    ghost_label = QLabel("Ghost:")
    ghost_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(ghost_label, _TT_GHOST_MODE)
    ghost_table.add_cell(0, 0, ghost_label, Align.LEFT)
    ghost_table.add_cell(0, 1, ghost_scope_row)

    unghost_scope_row = ScopeButtonRow()
    unghost_scope_row.set_callback("sel", lambda: ghost("CURRENT", False))
    unghost_scope_row.set_callback("tree", lambda: ghost("TREE", False))
    unghost_scope_row.set_callback("all", lambda: ghost("ALL", False))
    unghost_scope_row.set_tooltips(
        sel=action_menu_tooltip(
            "Unghost selected",
            "SculptObject_Unghost_Selected.py",
        ),
        tree="Unghost subtree",
        all=action_menu_tooltip(
            "Unghost all",
            "SculptObject_Unghost_All.py",
        ),
    )
    unghost_label = QLabel("Unghost:")
    unghost_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(unghost_label, _TT_GHOST_UNGHOST)
    ghost_table.add_cell(1, 0, unghost_label, Align.LEFT)
    ghost_table.add_cell(1, 1, unghost_scope_row)

    ghost_table.finalize()
    ghost_table.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    right_layout.addWidget(ghost_table)

    # Special row: [Invert][Toggle Isolate]
    def invert_ghost() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Inverting ghost", _log_info, log_success)
            set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT,
                      progress_callback=ctx.on_progress)
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
    ghost_special_grid.add_button(
        "Invert",
        invert_ghost,
        action_menu_tooltip(
            "Invert ghost states",
            "SculptObject_Ghost_Invert_All.py",
        ),
        icon=_INVERT_ICON,
    )
    ghost_special_grid.add_button(
        "Toggle Isolate",
        toggle_isolate_ghost,
        action_menu_tooltip(
            "Toggle ghost isolation (unghost all / isolate)",
            "SculptObject_ToggleIsolateGhost_Selected.py",
        ),
        icon=_GHOST_ICON,
    )
    right_layout.addWidget(ghost_special_grid)

    columns_layout.addWidget(right_column)
    columns_layout.addStretch()

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
