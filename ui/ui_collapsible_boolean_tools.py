"""
LKS UI - Boolean Tools Collapsible Section.

Three rows covering the full boolean action suite:
    Create:    Union | Subtract | Intersect          (NewVoxBool - clones parent)
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
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# CONSTANTS
# =============================================================================

LABEL_WIDTH: int = 70


# =============================================================================
# SECTION FACTORY
# =============================================================================

def create_boolean_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Build the Booleans collapsible section.

    Args:
        log_success: Callback for success log entries
        log_error:   Callback for error log entries
        refresh_tree: Callback to refresh the Outliner tree after structural ops

    Returns:
        CollapsibleSection widget ready to add to a parent layout.
    """
    section = CollapsibleSection(
        title="🧮 Booleans", collapsed=True, state_key="section_booleans")
    layout = section.content_layout

    # -------------------------------------------------------------------------
    # ROW 1 — CREATE NEW BOOLEAN CHILD (clones parent under itself)
    # -------------------------------------------------------------------------
    def on_new(mode_name: str) -> None:
        try:
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

    new_row = QHBoxLayout()
    new_row.setContentsMargins(0, 0, 0, 0)
    new_label = QLabel("Create:")
    new_label.setMinimumWidth(LABEL_WIDTH)
    new_row.addWidget(new_label)

    new_grid = ButtonGrid(columns=3)
    new_grid.add_button(
        "➕ Union", lambda: on_new("UNION"),
        "Clone selected → parent under it → Union mode (parent voxelised, child cleared)")
    new_grid.add_button(
        "➖ Subtract", lambda: on_new("SUBTRACT"),
        "Clone selected → parent under it → Subtract mode (parent voxelised, child cleared)")
    new_grid.add_button(
        "✴️ Intersect", lambda: on_new("INTERSECT"),
        "Clone selected → extrude → parent under it → Intersect mode")
    new_row.addWidget(new_grid)

    new_container = QWidget()
    new_container.setLayout(new_row)
    new_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(new_container)

    # -------------------------------------------------------------------------
    # ROW 2 — SET LIVE BOOLEAN MODE (in-place on selection, no cloning)
    # -------------------------------------------------------------------------
    def on_set_mode(mode_name: str) -> None:
        try:
            from ops.SculptObject_LiveBool import main as op_set
            from utils.SceneElement_boolean_utils import BooleanMode
            from utils.scope_utils import Scope
            mode = getattr(BooleanMode, mode_name)
            count = op_set(mode=mode, scope=Scope.CURRENT)
            if count:
                log_success(f"Set {mode_name.lower()} on {count} object(s)")
                refresh_tree()
            else:
                log_error(f"Set {mode_name.lower()} affected nothing")
        except Exception as e:
            log_error(f"Set {mode_name.lower()} failed: {e}")

    set_row = QHBoxLayout()
    set_row.setContentsMargins(0, 0, 0, 0)
    set_label = QLabel("Set Mode:")
    set_label.setMinimumWidth(LABEL_WIDTH)
    set_row.addWidget(set_label)

    set_grid = ButtonGrid(columns=4)
    set_grid.add_button(
        "➕ Union", lambda: on_set_mode("UNION"),
        "Set selected to Union (auto-voxelises self + parent, renames _Union)")
    set_grid.add_button(
        "➖ Subtract", lambda: on_set_mode("SUBTRACT"),
        "Set selected to Subtract (auto-voxelises self + parent, renames _Subtract)")
    set_grid.add_button(
        "✴️ Intersect", lambda: on_set_mode("INTERSECT"),
        "Set selected to Intersect (auto-voxelises self + parent, renames _Intersect)")
    set_grid.add_button(
        "🚫 Clear", lambda: on_set_mode("NONE"),
        "Disable live booleans on selected, strip boolean suffix")
    set_row.addWidget(set_grid)

    set_container = QWidget()
    set_container.setLayout(set_row)
    set_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(set_container)

    # -------------------------------------------------------------------------
    # ROW 3 — APPLY (collapse boolean subtree)
    # -------------------------------------------------------------------------
    def on_apply(keep_original: bool) -> None:
        try:
            from ops.SculptObject_ApplyBoolean import main as op_apply
            from utils.scope_utils import Scope
            count = op_apply(scope=Scope.CURRENT, keep_original=keep_original)
            if count:
                verb = "Applied (kept original)" if keep_original else "Applied"
                log_success(f"{verb} on {count} object(s)")
                refresh_tree()
            else:
                log_error("Apply affected nothing")
        except Exception as e:
            log_error(f"Apply failed: {e}")

    apply_row = QHBoxLayout()
    apply_row.setContentsMargins(0, 0, 0, 0)
    apply_label = QLabel("Apply:")
    apply_label.setMinimumWidth(LABEL_WIDTH)
    apply_row.addWidget(apply_label)

    apply_grid = ButtonGrid(columns=2)
    apply_grid.add_button(
        "✅ Apply", lambda: on_apply(False),
        "Collapse boolean subtree on selected (in-place); strips boolean suffix")
    apply_grid.add_button(
        "📋 Apply (keep)", lambda: on_apply(True),
        "Duplicate selected, collapse on duplicate, hide original (<base>_Applied)")
    apply_row.addWidget(apply_grid)

    apply_container = QWidget()
    apply_container.setLayout(apply_row)
    apply_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(apply_container)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_boolean_section(*args, **kwargs):  # type: ignore
        return None
