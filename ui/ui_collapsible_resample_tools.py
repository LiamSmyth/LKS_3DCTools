"""
LKS UI - Resample Tools Collapsible Section.

A collapsible section containing resample operations with:
- Half (0.5x) scope buttons
- Double (2x) scope buttons
- Smart resample (match density)

Uses label + scope button pattern for compact layout.

Usage:
    from ui.ui_collapsible_resample_tools import create_resample_section
    section = create_resample_section(log_success, log_error, refresh_tree)
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
# RESAMPLE SECTION FACTORY
# =============================================================================

def create_resample_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible resample tools section with label + scope button pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with resample tools
    """
    section = CollapsibleSection(
        title="🔄 Resample", collapsed=True, state_key="section_resample")
    layout = section.content_layout

    def resample_scope(scope_name: str, scale: float) -> None:
        try:
            from ops.SculptObject_Resample import main as resample
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            resample(scope=scope, scale=scale)
            log_success(f"Resampled {scope_name.lower()} to {scale}x")
            refresh_tree()
        except Exception as e:
            log_error(f"Resample failed: {e}")

    # --- Half row: Label + [Sel][Tree][All] ---
    half_row = QHBoxLayout()
    half_row.setContentsMargins(0, 0, 0, 0)
    half_label = QLabel("Half (0.5x):")
    half_label.setMinimumWidth(70)
    half_row.addWidget(half_label)

    half_grid = ButtonGrid(columns=3)
    half_grid.add_button("☝️", lambda: resample_scope(
        "CURRENT", 0.5), "Resample selection to half")
    half_grid.add_button("🌳", lambda: resample_scope(
        "TREE", 0.5), "Resample subtree")
    half_grid.add_button("🌎", lambda: resample_scope(
        "ALL", 0.5), "Resample all")
    half_row.addWidget(half_grid)

    half_container = QWidget()
    half_container.setLayout(half_row)
    half_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(half_container)

    # --- Double row: Label + [Sel][Tree][All] ---
    double_row = QHBoxLayout()
    double_row.setContentsMargins(0, 0, 0, 0)
    double_label = QLabel("Double (2x):")
    double_label.setMinimumWidth(70)
    double_row.addWidget(double_label)

    double_grid = ButtonGrid(columns=3)
    double_grid.add_button("☝️", lambda: resample_scope(
        "CURRENT", 2.0), "Resample selection to 2x")
    double_grid.add_button("🌳", lambda: resample_scope(
        "TREE", 2.0), "Resample subtree to 2x")
    double_grid.add_button("🌎", lambda: resample_scope(
        "ALL", 2.0), "Resample all to 2x")
    double_row.addWidget(double_grid)

    double_container = QWidget()
    double_container.setLayout(double_row)
    double_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(double_container)

    # --- Match Density (Smart) ---
    def match_density_tree() -> None:
        """Smart-match density for subtree against selected reference."""
        try:
            from ops.SculptObject_UniformDensity import smart_match_tree
            count = smart_match_tree()
            log_success(f"Matched density on {count} subtree objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (subtree) failed: {e}")

    def match_density_all() -> None:
        """Smart-match density for all sculpt objects against selected reference."""
        try:
            from ops.SculptObject_UniformDensity import smart_match_all
            count = smart_match_all()
            log_success(f"Matched density on {count} objects (all)")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (all) failed: {e}")

    match_row = QHBoxLayout()
    match_row.setContentsMargins(0, 0, 0, 0)
    match_label = QLabel("Match Density:")
    match_label.setMinimumWidth(100)
    match_row.addWidget(match_label)

    match_grid = ButtonGrid(columns=2)
    match_grid.add_button("🌳", match_density_tree,
                          "Smart match density on subtree")
    match_grid.add_button("🌎", match_density_all,
                          "Smart match density on all objects")
    match_row.addWidget(match_grid)

    match_container = QWidget()
    match_container.setLayout(match_row)
    match_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(match_container)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_resample_section(*args, **kwargs):  # type: ignore
        return None
# =============================================================================

if not HAS_QT:
    def create_resample_section(*args, **kwargs):  # type: ignore
        return None
