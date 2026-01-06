"""
LKS UI - Decimate Tools Collapsible Section.

A collapsible section containing decimate operations with:
- Reduction percentage slider
- Label + scope buttons (Apply: [Sel][Tree][All])
- Smart density matching

Uses label + scope button pattern for compact layout.

Usage:
    from ui.ui_collapsible_decimate_tools import create_decimate_section
    section = create_decimate_section(log_callback, refresh_callback)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QVBoxLayout

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    )
    from PySide6.QtCore import Qt

    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# DECIMATE SECTION FACTORY
# =============================================================================

def create_decimate_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible decimate tools section with label + scope button pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with decimate tools
    """
    section = CollapsibleSection(title="🔻 Decimate", state_key="section_decimate")
    layout: QVBoxLayout = section.content_layout

    # --- State ---
    state = {"slider_value": 50}

    # --- Quick Decimate: [50%][80%] applied to selected ---
    def quick_decimate(percent: float) -> None:
        try:
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            decimate(scope=Scope.CURRENT, reduction_percent=percent)
            log_success(f"Decimated selected to {int(percent)}%")
            refresh_tree()
        except Exception as e:
            log_error(f"Quick decimate failed: {e}")

    quick_row = QHBoxLayout()
    quick_row.setContentsMargins(0, 0, 0, 0)
    quick_label = QLabel("Quick:")
    quick_label.setMinimumWidth(60)
    quick_row.addWidget(quick_label)

    quick_grid = ButtonGrid(columns=2)
    quick_grid.add_button("50%", lambda: quick_decimate(
        50.0), "Decimate selected to 50%")
    quick_grid.add_button("80%", lambda: quick_decimate(
        80.0), "Decimate selected to 80%")
    quick_row.addWidget(quick_grid)

    quick_container = QWidget()
    quick_container.setLayout(quick_row)
    quick_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(quick_container)

    # --- Reduction % Slider ---
    slider_row = QHBoxLayout()
    slider_row.setContentsMargins(0, 0, 0, 0)

    slider_label = QLabel("Reduction:")
    slider_label.setMinimumWidth(60)
    slider_row.addWidget(slider_label)

    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(5)
    slider.setMaximum(95)
    slider.setValue(50)
    slider.setSingleStep(5)
    slider.setPageStep(10)
    slider_row.addWidget(slider)

    value_label = QLabel("50%")
    value_label.setFixedWidth(35)
    slider_row.addWidget(value_label)

    def on_slider_changed(value: int) -> None:
        # Snap to 5% increments
        snapped = (value // 5) * 5
        if snapped != value:
            slider.setValue(snapped)
        state["slider_value"] = snapped
        value_label.setText(f"{snapped}%")

    slider.valueChanged.connect(on_slider_changed)

    slider_container = QWidget()
    slider_container.setLayout(slider_row)
    slider_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(slider_container)

    # --- Apply row: Label + [Sel][Tree][All] ---
    def decimate_scope(scope_name: str) -> None:
        try:
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            percent = state["slider_value"]
            decimate(scope=scope, reduction_percent=float(percent))
            log_success(f"Decimated {scope_name.lower()} to {percent}%")
            refresh_tree()
        except Exception as e:
            log_error(f"Decimate failed: {e}")

    apply_row = QHBoxLayout()
    apply_row.setContentsMargins(0, 0, 0, 0)
    apply_label = QLabel("Apply:")
    apply_label.setMinimumWidth(60)
    apply_row.addWidget(apply_label)

    scope_grid = ButtonGrid(columns=3)
    scope_grid.add_button("☝️", lambda: decimate_scope(
        "CURRENT"), "Decimate selected")
    scope_grid.add_button(
        "🌳", lambda: decimate_scope("TREE"), "Decimate subtree")
    scope_grid.add_button("🌎", lambda: decimate_scope("ALL"), "Decimate all")
    apply_row.addWidget(scope_grid)

    apply_container = QWidget()
    apply_container.setLayout(apply_row)
    apply_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(apply_container)

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

    density_row = QHBoxLayout()
    density_row.setContentsMargins(0, 0, 0, 0)
    density_label = QLabel("Match Density:")
    density_label.setMinimumWidth(100)
    density_row.addWidget(density_label)

    density_grid = ButtonGrid(columns=2)
    density_grid.add_button("🌳", match_density_tree,
                            "Smart match density on subtree")
    density_grid.add_button("🌎", match_density_all,
                            "Smart match density on all objects")
    density_row.addWidget(density_grid)

    density_container = QWidget()
    density_container.setLayout(density_row)
    density_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(density_container)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_decimate_section(*args, **kwargs):  # type: ignore
        return None
