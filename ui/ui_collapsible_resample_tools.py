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
    half_grid.add_button("Sel", lambda: resample_scope(
        "CURRENT", 0.5), "Resample to half")
    half_grid.add_button("Tree", lambda: resample_scope(
        "TREE", 0.5), "Resample subtree")
    half_grid.add_button("All", lambda: resample_scope(
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
    double_grid.add_button("Sel", lambda: resample_scope(
        "CURRENT", 2.0), "Resample to 2x")
    double_grid.add_button("Tree", lambda: resample_scope(
        "TREE", 2.0), "Resample subtree to 2x")
    double_grid.add_button("All", lambda: resample_scope(
        "ALL", 2.0), "Resample all to 2x")
    double_row.addWidget(double_grid)

    double_container = QWidget()
    double_container.setLayout(double_row)
    double_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(double_container)

    # --- Smart Resample ---
    def smart_resample_tree() -> None:
        try:
            from utils.scene_api import SceneAPI
            from utils.Volume_density_utils import resample_to_match_density
            current = SceneAPI.get_current_element()
            if not current:
                log_error("No selection")
                return
            subtree = SceneAPI.collect_subtree(current)
            ref_vol = current.Volume()
            count: int = 0
            for el in subtree:
                if el != current and el.isSculptObject():
                    resample_to_match_density(el, ref_vol)
                    count += 1
            log_success(f"Resampled {count} to match density")
            refresh_tree()
        except Exception as e:
            log_error(f"Smart resample failed: {e}")

    smart_grid = ButtonGrid(columns=1)
    smart_grid.add_button("🧠 Match",
                          smart_resample_tree, "Match density to root element")
    layout.addWidget(smart_grid)

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
