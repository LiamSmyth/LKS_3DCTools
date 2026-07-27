"""
LKS UI - Boolean Tools Collapsible Section.

Three rows covering the full boolean action suite:
    Create child:    Union | Subtract | Intersect          (NewVoxBool - clones parent)
    Set Mode:  Union | Subtract | Intersect | Clear  (LiveBool   - in-place)
    Apply:     Apply | Apply (keep)                  (ApplyBoolean - collapse tree)

Imports happen inside callbacks so hot-reload picks up operator edits.

Usage:
    from ui.ui_collapsible_boolean_tools import create_boolean_section
    section = create_boolean_section(log_success, log_error, refresh_tree)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QSizePolicy, QWidget, QLabel
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QPixmap, QPainter
    from PySide6.QtSvg import QSvgRenderer

    from utils.ui.widgets import CollapsibleSection, ButtonGrid, add_tooltip
    from utils.menu_action_tooltip import action_menu_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.grid_row_table import GridRowTable, Align

    from pathlib import Path

    _ICONS_DIR: Path = Path(__file__).resolve().parent.parent / "utils" / "ui" / "data"
    _ACCENT: str = "#90caf9"

    def _svg_icon(name: str) -> QIcon:
        """Load an SVG, replacing currentColor with the accent color."""
        svg_path: Path = _ICONS_DIR / f"{name}.svg"
        content: str = svg_path.read_text(encoding="utf-8")
        content = content.replace("currentColor", _ACCENT)
        renderer: QSvgRenderer = QSvgRenderer(content.encode("utf-8"))
        pixmap: QPixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter: QPainter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    _UNION_ICON: QIcon = _svg_icon("boolean_union")
    _SUBTRACT_ICON: QIcon = _svg_icon("boolean_subtract")
    _INTERSECT_ICON: QIcon = _svg_icon("boolean_intersect")
    _CLEAR_ICON: QIcon = _svg_icon("boolean_clear")
    _APPLY_ICON: QIcon = _svg_icon("boolean_apply")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_TT_BOOLEAN_CREATE = MarkdownFileResource("data/tooltips/boolean_create.md", base_dir=__file__)
_TT_BOOLEAN_SET_MODE = MarkdownFileResource("data/tooltips/boolean_set_mode.md", base_dir=__file__)
_TT_BOOLEAN_APPLY = MarkdownFileResource("data/tooltips/boolean_apply.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_boolean.md", base_dir=__file__)


# =============================================================================
# SECTION FACTORY
# =============================================================================

def create_boolean_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Build the Booleans collapsible section.

    Args:
        log_success: Callback for success log entries
        log_error:   Callback for error log entries
        refresh_tree: Callback to refresh the Outliner tree after structural ops
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget ready to add to a parent layout.
    """
    section = CollapsibleSection(
        title="Booleans", icon_name="booleans", collapsed=True, state_key="section_booleans",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    # -------------------------------------------------------------------------
    # CALLBACKS
    # -------------------------------------------------------------------------
    def on_new(mode_name: str) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_NewVoxBool import main as op_new
            from utils.SceneElement_boolean_utils import BooleanMode
            mode = getattr(BooleanMode, mode_name)
            child = op_new(mode=mode)
            if child:
                log_success(f"Created {mode_name.lower()}: {child.name()}")
                refresh_tree()
            else:
                log_error(f"Failed to create {mode_name.lower()} child")
        except Exception as e:
            log_error(f"New {mode_name.lower()} failed: {e}")

    def on_set_mode(mode_name: str) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_LiveBool import main as op_set
            from utils.SceneElement_boolean_utils import BooleanMode
            from utils.scope_utils import Scope
            mode = getattr(BooleanMode, mode_name)
            ctx = make_iteration_context(f"Setting {mode_name.lower()} bool", _log_info)
            count = op_set(mode=mode, scope=Scope.CURRENT,
                           progress_callback=ctx.on_progress)
            if count:
                log_success(f"Set {mode_name.lower()} on {count} object(s)")
                refresh_tree()
            else:
                log_error(f"Set {mode_name.lower()} affected nothing")
        except Exception as e:
            log_error(f"Set {mode_name.lower()} failed: {e}")

    def on_apply(keep_original: bool) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_ApplyBoolean import main as op_apply
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Applying booleans", _log_info, log_success)
            count = op_apply(scope=Scope.CURRENT, keep_original=keep_original,
                             progress_callback=ctx.on_progress)
            if count:
                verb = "Applied (kept original)" if keep_original else "Applied"
                log_success(f"{verb} on {count} object(s)")
                refresh_tree()
            else:
                log_error("Apply affected nothing")
        except Exception as e:
            log_error(f"Apply failed: {e}")

    # -------------------------------------------------------------------------
    # GRID ROW TABLE — auto-aligned label column + ButtonGrid rows
    # -------------------------------------------------------------------------
    table = GridRowTable()

    # ROW 0 — CREATE NEW BOOLEAN CHILD (clones parent under itself)
    new_grid = ButtonGrid(columns=3)
    new_grid.add_button(
        "Union", lambda: on_new("UNION"),
        action_menu_tooltip(
            "Clone selected → parent under it → Union mode",
            "SculptObject_NewVoxBool_Union.py",
        ),
        icon=_UNION_ICON)
    new_grid.add_button(
        "Subtract", lambda: on_new("SUBTRACT"),
        action_menu_tooltip(
            "Clone selected → parent under it → Subtract mode",
            "SculptObject_NewVoxBool_Subtract.py",
        ),
        icon=_SUBTRACT_ICON)
    new_grid.add_button(
        "Intersect", lambda: on_new("INTERSECT"),
        action_menu_tooltip(
            "Clone selected → extrude → parent under it → Intersect mode",
            "SculptObject_NewVoxBool_Intersect.py",
        ),
        icon=_INTERSECT_ICON)

    create_label = QLabel("Create child:")
    add_tooltip(create_label, _TT_BOOLEAN_CREATE)
    table.add_cell(0, 0, create_label, Align.LEFT)
    table.add_cell(0, 1, new_grid)

    # ROW 1 — SET LIVE BOOLEAN MODE (in-place on selection, no cloning)
    set_grid = ButtonGrid(columns=4)
    set_grid.add_button(
        "Union", lambda: on_set_mode("UNION"),
        action_menu_tooltip(
            "Set selected to Union (auto-voxelises self + parent)",
            "SculptObject_LiveBool_Union.py",
        ),
        icon=_UNION_ICON)
    set_grid.add_button(
        "Subtract", lambda: on_set_mode("SUBTRACT"),
        action_menu_tooltip(
            "Set selected to Subtract (auto-voxelises self + parent)",
            "SculptObject_LiveBool_Subtract.py",
        ),
        icon=_SUBTRACT_ICON)
    set_grid.add_button(
        "Intersect", lambda: on_set_mode("INTERSECT"),
        action_menu_tooltip(
            "Set selected to Intersect (auto-voxelises self + parent)",
            "SculptObject_LiveBool_Intersect.py",
        ),
        icon=_INTERSECT_ICON)
    set_grid.add_button(
        "Clear", lambda: on_set_mode("NONE"),
        action_menu_tooltip(
            "Disable live booleans on selected, strip boolean suffix",
            "SculptObject_LiveBool_None.py",
        ),
        icon=_CLEAR_ICON)

    set_mode_label = QLabel("Set Mode:")
    add_tooltip(set_mode_label, _TT_BOOLEAN_SET_MODE)
    table.add_cell(1, 0, set_mode_label, Align.LEFT)
    table.add_cell(1, 1, set_grid)

    # ROW 2 — APPLY (collapse boolean subtree)
    apply_grid = ButtonGrid(columns=2)
    apply_grid.add_button(
        "Apply", lambda: on_apply(False),
        action_menu_tooltip(
            "Collapse boolean subtree on selected (in-place)",
            "SculptObject_ApplyBoolean_Selected.py",
        ),
        icon=_APPLY_ICON)
    apply_grid.add_button(
        "Apply (keep)", lambda: on_apply(True),
        action_menu_tooltip(
            "Duplicate selected, collapse on duplicate, hide original (<base>_Applied)",
            "SculptObject_ApplyBoolean_KeepOriginal_Selected.py",
        ),
        icon=_APPLY_ICON)

    apply_label = QLabel("Apply:")
    add_tooltip(apply_label, _TT_BOOLEAN_APPLY)
    table.add_cell(2, 0, apply_label, Align.LEFT)
    table.add_cell(2, 1, apply_grid)

    table.finalize()
    table.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    layout.addWidget(table)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_boolean_section(*args, **kwargs):  # type: ignore
        return None
