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
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget, QRadioButton, QButtonGroup
    from lks_utils.gui_qt.widgets.enhanced_slider import QEnhancedSlider
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ScopeButtonRow, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.sub_header import create_sub_header
    from utils.ui.widgets.badge_button import _make_icon_from_svg

    _SCALE_ICON: QIcon = _make_icon_from_svg("scale")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 80
_TT_SCALE_FACTOR = MarkdownFileResource("data/tooltips/scale_factor.md", base_dir=__file__)
_TT_SCALE_APPLY = MarkdownFileResource("data/tooltips/scale_apply.md", base_dir=__file__)
_TT_SCALE_SLIDER = MarkdownFileResource("data/tooltips/scale_slider.md", base_dir=__file__)
_TT_SCALE_PIVOT = MarkdownFileResource("data/tooltips/scale_pivot.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_scale.md", base_dir=__file__)


def create_scale_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create scale tools section with slider and quick scale buttons.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="Scale", icon_name="scale", collapsed=True, state_key="section_scale",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    state: dict = {"scale_factor": 1.0, "pivot": "world_origin"}

    def do_scale(scope_name: str, factor: float | None = None) -> None:
        """Execute scale with given or current factor."""
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Scale import main as op_scale, ScalePivot
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            use_factor = factor if factor is not None else state["scale_factor"]
            pivot = ScalePivot(state["pivot"])
            ctx = make_iteration_context("Scaling", _log_info, log_success)
            op_scale(
                scope=scope,
                scale_factor=use_factor,
                pivot=pivot,
                progress_callback=ctx.on_progress,
                verbose_log=_log_info,
            )
            if use_factor < 1.0:
                label = f"×{use_factor:.1f}" if use_factor >= 0.1 else f"×{use_factor:.2f}"
            else:
                label = f"×{int(use_factor)}" if use_factor == int(
                    use_factor) else f"×{use_factor:.1f}"
            pivot_tag = "world" if pivot.value == "world_origin" else "sel"
            log_success(f"Scaled {scope_name.lower()} {label} ({pivot_tag})")
            refresh_tree()
        except Exception as e:
            log_error(f"Scale failed: {e}")

    # --- Pivot mode ---
    layout.addWidget(create_sub_header("Pivot"))
    pivot_row = QWidget()
    pivot_layout = QHBoxLayout(pivot_row)
    pivot_layout.setContentsMargins(0, 0, 0, 0)
    pivot_layout.setSpacing(8)
    pivot_group = QButtonGroup(pivot_row)
    radio_world = QRadioButton("World origin")
    radio_sel = QRadioButton("Selection")
    radio_world.setChecked(True)
    pivot_group.addButton(radio_world)
    pivot_group.addButton(radio_sel)
    add_tooltip(radio_world, _TT_SCALE_PIVOT)
    add_tooltip(radio_sel, _TT_SCALE_PIVOT)
    radio_world.toggled.connect(
        lambda on: state.update(pivot="world_origin") if on else None
    )
    radio_sel.toggled.connect(
        lambda on: state.update(pivot="selection") if on else None
    )
    pivot_layout.addWidget(radio_world)
    pivot_layout.addWidget(radio_sel)
    pivot_layout.addStretch(1)
    layout.addWidget(pivot_row)

    # --- Quick Scale buttons (applied to TREE by default) ---
    layout.addWidget(create_sub_header("Quick Scale"))

    quick_grid = ButtonGrid(columns=4)
    quick_grid.add_button("×0.1", lambda: do_scale(
        "TREE", 0.1), "Scale tree down 10x", icon=_SCALE_ICON)
    quick_grid.add_button("×0.5", lambda: do_scale(
        "TREE", 0.5), "Scale tree down 2x", icon=_SCALE_ICON)
    quick_grid.add_button("×2", lambda: do_scale(
        "TREE", 2.0), "Scale tree up 2x", icon=_SCALE_ICON)
    quick_grid.add_button("×10", lambda: do_scale(
        "TREE", 10.0), "Scale tree up 10x", icon=_SCALE_ICON)
    layout.addWidget(quick_grid)

    # --- Custom Scale slider and apply buttons ---
    layout.addWidget(create_sub_header("Custom Scale"))

    scale_slider = QEnhancedSlider(
        min_value=0.01,
        max_value=100.0,
        default_value=1.0,
        step=0.1,
        decimals=3,
        logarithmic=True,
        hard_min=0.001,
        hard_max=1000.0,
    )
    add_tooltip(scale_slider, _TT_SCALE_SLIDER)
    scale_slider.value_changed.connect(lambda v: state.update(scale_factor=v))

    apply_scope_row = ScopeButtonRow()
    apply_scope_row.set_callback("sel", lambda: do_scale("CURRENT"))
    apply_scope_row.set_callback("tree", lambda: do_scale("TREE"))
    apply_scope_row.set_callback("all", lambda: do_scale("ALL"))
    apply_scope_row.set_tooltips(
        sel="Apply scale to selected",
        tree="Apply scale to subtree",
        all="Apply scale to all",
    )
    add_tooltip(apply_scope_row, _TT_SCALE_APPLY)

    scale_row = QWidget()
    scale_row_layout = QHBoxLayout(scale_row)
    scale_row_layout.setContentsMargins(0, 0, 0, 0)
    scale_row_layout.setSpacing(4)
    scale_label = QLabel("Factor:")
    scale_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(scale_label, _TT_SCALE_FACTOR)
    scale_row_layout.addWidget(scale_label)
    scale_row_layout.addWidget(scale_slider, stretch=1)
    scale_row_layout.addWidget(apply_scope_row)
    layout.addWidget(scale_row)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_scale_section(*args, **kwargs):  # type: ignore
        return None
