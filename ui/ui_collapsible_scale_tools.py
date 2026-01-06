"""
LKS UI - Scale Tools Section.

Collapsible section for scale operations with slider and quick scale buttons.

Usage:
    from ui.ui_collapsible_scale_tools import create_scale_section
    section = create_scale_section(log_success, log_error, refresh_tree)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QDoubleSpinBox,
    )
    from PySide6.QtCore import Qt
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


def create_scale_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create scale tools section with slider and quick scale buttons.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="📏 Scale", collapsed=True, state_key="section_scale")
    layout = section.content_layout

    # State for custom scale factor
    state: dict = {"scale_factor": 1.0}

    def do_scale(scope_name: str, factor: float | None = None) -> None:
        """Execute scale with given or current factor."""
        try:
            from ops.SculptObject_Scale import main as op_scale
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            use_factor = factor if factor is not None else state["scale_factor"]
            op_scale(scope=scope, scale_factor=use_factor)
            if use_factor < 1.0:
                label = f"×{use_factor:.1f}" if use_factor >= 0.1 else f"×{use_factor:.2f}"
            else:
                label = f"×{int(use_factor)}" if use_factor == int(
                    use_factor) else f"×{use_factor:.1f}"
            log_success(f"Scaled {scope_name.lower()} {label}")
            refresh_tree()
        except Exception as e:
            log_error(f"Scale failed: {e}")

    # --- Quick Scale buttons (applied to TREE by default) ---
    layout.addWidget(create_sub_header("Quick Scale"))

    quick_grid = ButtonGrid(columns=4)
    quick_grid.add_button("×0.1", lambda: do_scale(
        "TREE", 0.1), "Scale tree down 10x")
    quick_grid.add_button("×0.5", lambda: do_scale(
        "TREE", 0.5), "Scale tree down 2x")
    quick_grid.add_button("×2", lambda: do_scale(
        "TREE", 2.0), "Scale tree up 2x")
    quick_grid.add_button("×10", lambda: do_scale(
        "TREE", 10.0), "Scale tree up 10x")
    layout.addWidget(quick_grid)

    # --- Custom Scale slider and apply buttons ---
    layout.addWidget(create_sub_header("Custom Scale"))

    # Slider row: Label + Slider + SpinBox
    slider_row = QHBoxLayout()
    slider_row.setContentsMargins(0, 0, 0, 0)

    scale_label = QLabel("Factor:")
    scale_label.setMinimumWidth(50)
    slider_row.addWidget(scale_label)

    # Slider: 0.01 to 100 (log scale approximation via steps)
    scale_slider = QSlider(Qt.Horizontal)
    scale_slider.setRange(-200, 200)  # -200 = 0.01x, 0 = 1x, 200 = 100x
    scale_slider.setValue(0)
    scale_slider.setToolTip("Drag to set scale factor")
    slider_row.addWidget(scale_slider)

    scale_spin = QDoubleSpinBox()
    scale_spin.setRange(0.001, 1000.0)
    scale_spin.setDecimals(3)
    scale_spin.setValue(1.0)
    scale_spin.setSingleStep(0.1)
    scale_spin.setMinimumWidth(70)
    slider_row.addWidget(scale_spin)

    def slider_to_factor(value: int) -> float:
        """Convert slider value to scale factor (log scale)."""
        if value == 0:
            return 1.0
        elif value > 0:
            return 1.0 + (value / 200.0) * 99.0  # 0-200 -> 1.0-100.0
        else:
            return 1.0 / (1.0 + (-value / 200.0) * 99.0)  # -200-0 -> 0.01-1.0

    def factor_to_slider(factor: float) -> int:
        """Convert scale factor to slider value."""
        if abs(factor - 1.0) < 0.001:
            return 0
        elif factor > 1.0:
            return int(((factor - 1.0) / 99.0) * 200.0)
        else:
            inv = 1.0 / factor
            return -int(((inv - 1.0) / 99.0) * 200.0)

    def on_slider_changed(value: int) -> None:
        factor = slider_to_factor(value)
        state["scale_factor"] = factor
        scale_spin.blockSignals(True)
        scale_spin.setValue(factor)
        scale_spin.blockSignals(False)

    def on_spin_changed(value: float) -> None:
        state["scale_factor"] = value
        scale_slider.blockSignals(True)
        scale_slider.setValue(factor_to_slider(value))
        scale_slider.blockSignals(False)

    scale_slider.valueChanged.connect(on_slider_changed)
    scale_spin.valueChanged.connect(on_spin_changed)

    slider_container = QWidget()
    slider_container.setLayout(slider_row)
    slider_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(slider_container)

    # Apply buttons row: Label + [Sel][Tree][All]
    apply_row = QHBoxLayout()
    apply_row.setContentsMargins(0, 0, 0, 0)
    apply_label = QLabel("Apply:")
    apply_label.setMinimumWidth(50)
    apply_row.addWidget(apply_label)

    apply_grid = ButtonGrid(columns=3)
    apply_grid.add_button("☝️", lambda: do_scale(
        "CURRENT"), "Apply scale to selected")
    apply_grid.add_button("🌳", lambda: do_scale(
        "TREE"), "Apply scale to subtree")
    apply_grid.add_button("🌎", lambda: do_scale("ALL"), "Apply scale to all")
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
    def create_scale_section(*args, **kwargs):  # type: ignore
        return None
