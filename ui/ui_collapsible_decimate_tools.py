"""
LKS UI - Decimate Tools Collapsible Section.

Grid layout (label | control | scope_buttons):
  Row 0:  Quick:        [50%][80%][1k][10k][100k][1M]
  Row 1:  Reduction:    [══════════ slider ══════════]  [Sel][Tree][All]
  Row 2:  Polycount:    [══════════ log slider ══════]  [Sel][Tree][All]
  Row 3:  Match Density to Selection:                  [Tree][All]

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
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QLabel,
    )

    from lks_utils.gui_qt.widgets.enhanced_slider import QEnhancedSlider
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ScopeButtonRow, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.badge_button import _make_icon_from_svg
    from utils.menu_action_tooltip import action_menu_tooltip

    _DECIMATE_ICON: QIcon = _make_icon_from_svg("decimate")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 80
_TT_DECIMATE_QUICK = MarkdownFileResource("data/tooltips/decimate_quick.md", base_dir=__file__)
_TT_DECIMATE_SLIDER = MarkdownFileResource("data/tooltips/decimate_slider.md", base_dir=__file__)
_TT_DECIMATE_POLYCOUNT = MarkdownFileResource(
    "data/tooltips/decimate_polycount_slider.md", base_dir=__file__
)
_TT_MATCH_DENSITY = MarkdownFileResource(
    "data/tooltips/decimate_match_density.md", base_dir=__file__
)
_HELP = MarkdownFileResource("data/tooltips/help_decimate.md", base_dir=__file__)

# Quick polycount presets (label → target polycount)
_QUICK_POLY_PRESETS: list[tuple[str, int]] = [
    ("1k", 1_000),
    ("10k", 10_000),
    ("100k", 100_000),
    ("1M", 1_000_000),
]

DEFAULT_POLYCOUNT: int = 10_000
POLYCOUNT_MIN: int = 100
POLYCOUNT_MAX: int = 10_000_000


# =============================================================================
# DECIMATE SECTION FACTORY
# =============================================================================

def create_decimate_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """Create the decimate tools collapsible section."""
    section = CollapsibleSection(
        title="Decimate", icon_name="decimate", state_key="section_decimate",
        help_text=_HELP.text,
    )

    layout: QVBoxLayout = section.content_layout

    # --- State ---
    state: dict[str, int] = {
        "slider_value": 50,
        "polycount_value": DEFAULT_POLYCOUNT,
    }

    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    # =========================================================================
    # QUICK DECIMATE CALLBACKS
    # =========================================================================

    def quick_decimate(percent: float) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Decimating", _log_info, log_success)
            decimate(scope=Scope.CURRENT, reduction_percent=percent,
                     progress_callback=ctx.on_progress)
            log_success(f"Decimated selected to {int(percent)}%")
            refresh_tree()
        except Exception as e:
            log_error(f"Quick decimate failed: {e}")

    def quick_decimate_poly(polycount: int) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Decimating", _log_info, log_success)
            decimate(
                scope=Scope.CURRENT,
                reduction_percent=None,
                target_polycount=polycount,
                progress_callback=ctx.on_progress,
            )
            log_success(f"Decimated selected to {polycount:,} polys")
            refresh_tree()
        except Exception as e:
            log_error(f"Quick polycount decimate failed: {e}")

    # =========================================================================
    # SCOPE CALLBACKS (slider-based decimate)
    # =========================================================================

    def decimate_scope(scope_name: str) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            scope: Scope = getattr(Scope, scope_name)
            percent: int = state["slider_value"]
            ctx = make_iteration_context("Decimating", _log_info, log_success)
            decimate(scope=scope, reduction_percent=float(percent),
                     progress_callback=ctx.on_progress)
            log_success(f"Decimated {scope_name.lower()} to {percent}%")
            refresh_tree()
        except Exception as e:
            log_error(f"Decimate failed: {e}")

    def decimate_poly_scope(scope_name: str) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Decimate import main as decimate
            from utils.scope_utils import Scope
            scope: Scope = getattr(Scope, scope_name)
            polycount: int = state["polycount_value"]
            ctx = make_iteration_context("Decimating", _log_info, log_success)
            decimate(
                scope=scope,
                reduction_percent=None,
                target_polycount=polycount,
                progress_callback=ctx.on_progress,
            )
            log_success(f"Decimated {scope_name.lower()} to {polycount:,} polys")
            refresh_tree()
        except Exception as e:
            log_error(f"Polycount decimate failed: {e}")

    # =========================================================================
    # MATCH DENSITY CALLBACKS
    # =========================================================================

    def match_density_tree() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_UniformDensity import smart_match_tree
            count: int = smart_match_tree()
            log_success(f"Matched density on {count} subtree objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (subtree) failed: {e}")

    def match_density_all() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_UniformDensity import smart_match_all
            count: int = smart_match_all()
            log_success(f"Matched density on {count} objects (all)")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (all) failed: {e}")

    # =========================================================================
    # Row 0: Quick presets (percent + polycount)
    # =========================================================================
    quick_row = QWidget()
    quick_row_layout = QHBoxLayout(quick_row)
    quick_row_layout.setContentsMargins(0, 0, 0, 0)
    quick_row_layout.setSpacing(4)
    quick_label = QLabel("Quick:")
    quick_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(quick_label, _TT_DECIMATE_QUICK)
    quick_row_layout.addWidget(quick_label)
    quick_grid: ButtonGrid = ButtonGrid(columns=6)
    quick_grid.add_button(
        "50%",
        lambda: quick_decimate(50.0),
        action_menu_tooltip(
            "Decimate selected to 50%",
            "SculptObject_Decimate_Half_Selected.py",
        ),
        icon=_DECIMATE_ICON,
    )
    quick_grid.add_button(
        "80%",
        lambda: quick_decimate(80.0),
        action_menu_tooltip(
            "Decimate selected to 80%",
            "SculptObject_Decimate_80Percent_Selected.py",
        ),
        icon=_DECIMATE_ICON,
    )
    for label, poly in _QUICK_POLY_PRESETS:
        # clicked(bool) must not bind over the captured poly default
        quick_grid.add_button(
            label,
            lambda *_, p=poly: quick_decimate_poly(p),
            f"Decimate selected to {poly:,} polys",
            icon=_DECIMATE_ICON,
        )
    quick_row_layout.addWidget(quick_grid)
    quick_row_layout.addStretch()
    layout.addWidget(quick_row)

    # =========================================================================
    # Row 1: Reduction slider + Apply scope
    # =========================================================================
    decimate_slider = QEnhancedSlider(
        min_value=5.0,
        max_value=95.0,
        default_value=50.0,
        step=5.0,
        decimals=0,
    )
    add_tooltip(decimate_slider, _TT_DECIMATE_SLIDER)
    decimate_slider.value_changed.connect(
        lambda v: state.update(slider_value=int(v))
    )

    apply_scope_row: ScopeButtonRow = ScopeButtonRow()
    apply_scope_row.set_callback("sel", lambda: decimate_scope("CURRENT"))
    apply_scope_row.set_callback("tree", lambda: decimate_scope("TREE"))
    apply_scope_row.set_callback("all", lambda: decimate_scope("ALL"))
    apply_scope_row.set_tooltips(
        sel="Decimate selected",
        tree="Decimate subtree",
        all="Decimate all",
    )

    slider_row = QWidget()
    slider_row_layout = QHBoxLayout(slider_row)
    slider_row_layout.setContentsMargins(0, 0, 0, 0)
    slider_row_layout.setSpacing(4)
    reduction_label = QLabel("Reduction:")
    reduction_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(reduction_label, _TT_DECIMATE_SLIDER)
    slider_row_layout.addWidget(reduction_label)
    slider_row_layout.addWidget(decimate_slider, stretch=1)
    slider_row_layout.addWidget(apply_scope_row)
    layout.addWidget(slider_row)

    # =========================================================================
    # Row 2: Polycount slider + Apply scope
    # =========================================================================
    polycount_slider = QEnhancedSlider(
        min_value=float(POLYCOUNT_MIN),
        max_value=float(POLYCOUNT_MAX),
        default_value=float(DEFAULT_POLYCOUNT),
        step=100.0,
        decimals=0,
        logarithmic=True,
        hard_min=float(POLYCOUNT_MIN),
        hard_max=float(POLYCOUNT_MAX),
    )
    add_tooltip(polycount_slider, _TT_DECIMATE_POLYCOUNT)
    polycount_slider.value_changed.connect(
        lambda v: state.update(polycount_value=int(v))
    )

    poly_scope_row: ScopeButtonRow = ScopeButtonRow()
    poly_scope_row.set_callback("sel", lambda: decimate_poly_scope("CURRENT"))
    poly_scope_row.set_callback("tree", lambda: decimate_poly_scope("TREE"))
    poly_scope_row.set_callback("all", lambda: decimate_poly_scope("ALL"))
    poly_scope_row.set_tooltips(
        sel="Decimate selected to target polycount",
        tree="Decimate subtree to target polycount",
        all="Decimate all to target polycount",
    )

    poly_row = QWidget()
    poly_row_layout = QHBoxLayout(poly_row)
    poly_row_layout.setContentsMargins(0, 0, 0, 0)
    poly_row_layout.setSpacing(4)
    poly_label = QLabel("Polycount:")
    poly_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(poly_label, _TT_DECIMATE_POLYCOUNT)
    poly_row_layout.addWidget(poly_label)
    poly_row_layout.addWidget(polycount_slider, stretch=1)
    poly_row_layout.addWidget(poly_scope_row)
    layout.addWidget(poly_row)

    # =========================================================================
    # Row 3: Match Density
    # =========================================================================
    density_row = QWidget()
    density_row_layout = QHBoxLayout(density_row)
    density_row_layout.setContentsMargins(0, 0, 0, 0)
    density_row_layout.setSpacing(4)
    density_label = QLabel("Match Density to Selection:")
    add_tooltip(density_label, _TT_MATCH_DENSITY)
    density_row_layout.addWidget(density_label)

    density_scope_row: ScopeButtonRow = ScopeButtonRow()
    density_scope_row.set_callback("sel", None)
    density_scope_row.set_callback("tree", lambda: match_density_tree())
    density_scope_row.set_callback("all", lambda: match_density_all())
    density_scope_row.set_tooltips(
        tree=action_menu_tooltip(
            "Smart match density on subtree (decimate/subdivide path)",
            "SculptObject_MatchDensity_Smart_Subtree.py",
        ),
        all=action_menu_tooltip(
            "Smart match density on all objects (decimate/subdivide path)",
            "SculptObject_MatchDensity_Smart_All.py",
        ),
    )
    density_row_layout.addWidget(density_scope_row)
    density_row_layout.addStretch()
    layout.addWidget(density_row)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_decimate_section(*args, **kwargs):  # type: ignore
        return None
