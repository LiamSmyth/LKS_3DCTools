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
    from ui.ui_widget_sub_header import create_sub_header

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
    section = CollapsibleSection(title="Decimate", color="#ffb74d")
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
    scope_grid.add_button("Sel", lambda: decimate_scope(
        "CURRENT"), "Decimate selected")
    scope_grid.add_button(
        "Tree", lambda: decimate_scope("TREE"), "Decimate subtree")
    scope_grid.add_button("All", lambda: decimate_scope("ALL"), "Decimate all")
    apply_row.addWidget(scope_grid)

    apply_container = QWidget()
    apply_container.setLayout(apply_row)
    apply_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(apply_container)

    # --- Smart Density ---
    def smart_density() -> None:
        try:
            from ops.SculptObject_UniformDensity import main as uniform_density, DensityMode
            count = uniform_density(mode=DensityMode.SMART)
            log_success(f"Smart matched {count}")
            refresh_tree()
        except Exception as e:
            log_error(f"Smart density failed: {e}")

    density_grid = ButtonGrid(columns=1)
    density_grid.add_button("Smart Density Match (Tree)", smart_density,
                            "Match density using tolerance")
    layout.addWidget(density_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_decimate_section(*args, **kwargs):  # type: ignore
        return None
