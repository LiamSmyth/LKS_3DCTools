"""
LKS UI - Resample Tools Collapsible Section.

A collapsible section containing resample operations with:
- Half (0.5x) scope buttons
- Double (2x) scope buttons
- Smart resample (match density)
- Target Polycount — resample to exact polycount with scope buttons
- Target Density — resample to uniform world-space detail density with scope buttons

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
    from PySide6.QtWidgets import (
        QLabel, QHBoxLayout, QWidget,
    )
    from lks_utils.gui_qt.widgets.enhanced_slider import QEnhancedSlider
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ScopeButtonRow, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.menu_action_tooltip import action_menu_tooltip
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 70
_TT_MATCH_DENSITY = MarkdownFileResource("data/tooltips/resample_match_density.md", base_dir=__file__)
_TT_TARGET_POLYCOUNT = MarkdownFileResource("data/tooltips/resample_target_polycount.md", base_dir=__file__)
_TT_TARGET_DENSITY = MarkdownFileResource("data/tooltips/resample_target_density.md", base_dir=__file__)
_TT_DENSITY_SLIDER = MarkdownFileResource("data/tooltips/resample_density_slider.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_resample.md", base_dir=__file__)


# =============================================================================
# POLYCOUNT COLOR GRADIENT & ESTIMATE HELPERS
# =============================================================================

# Breakpoints: (polycount, hex_color) — interpolated between for smooth gradient
_POLY_COLOR_BREAKPOINTS: list[tuple[int, str]] = [
    (0,          "#90caf9"),   # blue — very safe
    (50_000,     "#90caf9"),   # blue
    (200_000,    "#81c784"),   # green
    (1_000_000,  "#ffd54f"),   # yellow
    (5_000_000,  "#ffb74d"),   # orange
    (10_000_000, "#ef5350"),   # red — extreme
]

BYTES_PER_POLY: int = 64  # rough: vertices + indices + attribute data per polygon


def _lerp_hex_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    r1: int = int(hex1[1:3], 16)
    g1: int = int(hex1[3:5], 16)
    b1: int = int(hex1[5:7], 16)
    r2: int = int(hex2[1:3], 16)
    g2: int = int(hex2[3:5], 16)
    b2: int = int(hex2[5:7], 16)
    r: int = int(r1 + (r2 - r1) * t)
    g: int = int(g1 + (g2 - g1) * t)
    b: int = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _polycount_color(polycount: int) -> str:
    """Return a hex color for the given polycount, interpolating between breakpoints."""
    if polycount <= 0:
        return _POLY_COLOR_BREAKPOINTS[0][1]
    for i in range(len(_POLY_COLOR_BREAKPOINTS) - 1):
        lo_poly, lo_color = _POLY_COLOR_BREAKPOINTS[i]
        hi_poly, hi_color = _POLY_COLOR_BREAKPOINTS[i + 1]
        if lo_poly <= polycount <= hi_poly:
            if lo_poly == hi_poly:
                return lo_color
            t: float = (polycount - lo_poly) / (hi_poly - lo_poly)
            return _lerp_hex_color(lo_color, hi_color, t)
    return _POLY_COLOR_BREAKPOINTS[-1][1]  # fallback: red


def _format_memory(total_polys: int) -> str:
    """Format memory estimate from total polygon count (64 bytes/poly)."""
    bytes_est: float = float(total_polys) * BYTES_PER_POLY
    mb: float = bytes_est / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.0f} MB"
    gb: float = mb / 1024
    return f"{gb:.1f} GB"


def _warning_badge(total_polys: int) -> str:
    """Return an HTML badge string, or empty string if no warning needed."""
    if total_polys >= 50_000_000:
        return (
            ' <span style="background-color:#ef5350;color:#fff;'
            'padding:1px 5px;border-radius:3px;font-size:10px;'
            'font-weight:bold;">⚠ Extreme polycount</span>'
        )
    if total_polys >= 10_000_000:
        return (
            ' <span style="background-color:#ffb74d;color:#1a1a1a;'
            'padding:1px 5px;border-radius:3px;font-size:10px;'
            'font-weight:bold;">⚠ High polycount</span>'
        )
    return ""


# =============================================================================
# HELPERS
# =============================================================================

def _iter_visible_sculpt(root: "coat.SceneElement") -> list:
    """
    Collect all visible sculpt objects via direct child traversal.

    Avoids 3DCoat's iterateSubtree which traverses instance links.
    Only returns elements that are visible and are sculpt objects.
    """
    import coat
    result: list = []

    def _walk(el: coat.SceneElement) -> None:
        if el.visible() and el.isSculptObject():
            result.append(el)
        for i in range(el.childCount()):
            child: coat.SceneElement | None = el.child(i)
            if child is not None:
                _walk(child)

    _walk(root)
    return result


# =============================================================================
# RESAMPLE SECTION FACTORY
# =============================================================================

def create_resample_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create a collapsible resample tools section with label + scope button pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget with resample tools
    """
    section = CollapsibleSection(
        title="Resample", icon_name="resample", collapsed=True, state_key="section_resample",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    def resample_scope(scope_name: str, scale: float) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_Resample import main as resample
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            ctx = make_iteration_context("Resampling", _log_info, log_success)
            resample(scope=scope, scale=scale,
                     progress_callback=ctx.on_progress)
            log_success(f"Resampled {scope_name.lower()} to {scale}x")
            refresh_tree()
        except Exception as e:
            log_error(f"Resample failed: {e}")

    # =========================================================================
    # REGION 1 — Half, Double, Match Selection
    # =========================================================================
    region_label = QLabel("Resample density to:")
    region_label.setStyleSheet("color: #aaa; font-size: 10px; padding: 2px 0px;")
    layout.addWidget(region_label)

    # --- Inline row: Half (0.5x) | Double (2x) ---
    half_double_row = QWidget()
    half_double_layout = QHBoxLayout(half_double_row)
    half_double_layout.setContentsMargins(0, 0, 0, 0)
    half_double_layout.setSpacing(12)

    # Half (0.5x)
    half_scope_row = ScopeButtonRow()
    half_scope_row.set_callback("sel", lambda: resample_scope("CURRENT", 0.5))
    half_scope_row.set_callback("tree", lambda: resample_scope("TREE", 0.5))
    half_scope_row.set_callback("all", lambda: resample_scope("ALL", 0.5))
    half_scope_row.set_tooltips(
        sel="Resample selection to half",
        tree=action_menu_tooltip(
            "Resample subtree to half",
            "SculptObject_Resample_Half_Subtree.py",
        ),
        all="Resample all to half",
    )
    half_label = QLabel("Half (0.5x):")
    half_label.setFixedWidth(_LABEL_WIDTH)
    half_label.setStyleSheet("color: #ddd;")
    half_double_layout.addWidget(half_label)
    half_double_layout.addWidget(half_scope_row)

    # Double (2x)
    double_scope_row = ScopeButtonRow()
    double_scope_row.set_callback("sel", lambda: resample_scope("CURRENT", 2.0))
    double_scope_row.set_callback("tree", lambda: resample_scope("TREE", 2.0))
    double_scope_row.set_callback("all", lambda: resample_scope("ALL", 2.0))
    double_scope_row.set_tooltips(
        sel="Resample selection to 2x",
        tree="Resample subtree to 2x",
        all="Resample all to 2x",
    )
    double_label = QLabel("Double (2x):")
    double_label.setFixedWidth(_LABEL_WIDTH)
    double_label.setStyleSheet("color: #ddd;")
    half_double_layout.addWidget(double_label)
    half_double_layout.addWidget(double_scope_row)

    half_double_layout.addStretch()
    layout.addWidget(half_double_row)

    # --- Row: Match Density to Selection ---
    def _match_density_tree() -> None:
        """Resample-smart match density for subtree against selected reference."""
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_UniformDensity import resample_smart_match_tree
            count: int = resample_smart_match_tree()
            log_success(f"Matched density on {count} subtree objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (subtree) failed: {e}")

    def _match_density_all() -> None:
        """Resample-smart match density for all sculpt objects against selected reference."""
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_UniformDensity import resample_smart_match_all
            count: int = resample_smart_match_all()
            log_success(f"Matched density on {count} objects (all)")
            refresh_tree()
        except Exception as e:
            log_error(f"Match density (all) failed: {e}")

    match_row = QWidget()
    match_row_layout = QHBoxLayout(match_row)
    match_row_layout.setContentsMargins(0, 0, 0, 0)
    match_row_layout.setSpacing(4)

    match_label = QLabel("Match Density to Selection:")
    add_tooltip(match_label, _TT_MATCH_DENSITY)
    match_label.setStyleSheet("color: #ddd;")
    match_scope_row = ScopeButtonRow()
    match_scope_row.set_callback("sel", None)
    match_scope_row.set_callback("tree", lambda: _match_density_tree())
    match_scope_row.set_callback("all", lambda: _match_density_all())
    match_scope_row.set_tooltips(
        tree=action_menu_tooltip(
            "Smart-resample match density on subtree",
            "SculptObject_MatchDensity_Resample_Subtree.py",
        ),
        all=action_menu_tooltip(
            "Smart-resample match density on all objects",
            "SculptObject_MatchDensity_Resample_All.py",
        ),
    )
    match_row_layout.addWidget(match_label)
    match_row_layout.addWidget(match_scope_row)
    match_row_layout.addStretch()
    layout.addWidget(match_row)

    # --- Target Resample ---
    target_header = QLabel("Target Resample")
    target_header.setStyleSheet("color: #b0c4de; font-size: 10px; font-weight: bold; padding: 4px 0px 0px 0px;")
    layout.addWidget(target_header)

    def _resample_target_poly(scope_name: str, poly: int) -> None:
        """Resample to the exact target polycount."""
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_ResampleTarget import (
                main as resample_target,
                ResampleTargetMode,
            )
            from utils.scope_utils import Scope
            scope: Scope = getattr(Scope, scope_name)
            count: int = resample_target(
                scope=scope,
                target_polycount=poly,
                mode=ResampleTargetMode.TARGET_POLYCOUNT,
            )
            log_success(
                f"Resampled {scope_name.lower()} to {poly:,} polys "
                f"({count} objects)"
            )
            refresh_tree()
        except Exception as e:
            log_error(f"Target poly resample failed: {e}")

    def _resample_target_density(scope_name: str, density: float) -> None:
        """Resample to the target world-space density."""
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_ResampleTarget import (
                main as resample_target,
                ResampleTargetMode,
            )
            from utils.scope_utils import Scope
            scope: Scope = getattr(Scope, scope_name)
            count: int = resample_target(
                scope=scope,
                target_density=density,
                mode=ResampleTargetMode.TARGET_DENSITY,
            )
            log_success(
                f"Resampled {scope_name.lower()} to "
                f"{density:,.0f} tris/unit² ({count} objects)"
            )
            refresh_tree()
        except Exception as e:
            log_error(f"Target density resample failed: {e}")

    # --- Row 0: Polycount ---
    poly_label = QLabel("Polycount:")
    add_tooltip(poly_label, _TT_TARGET_POLYCOUNT)
    poly_label.setFixedWidth(_LABEL_WIDTH)
    poly_label.setStyleSheet("color: #ddd;")
    poly_slider = QEnhancedSlider(
        min_value=100,
        max_value=50_000_000,
        default_value=10000,
        step=1000,
        logarithmic=True,
        hard_min=100,
        hard_max=50_000_000,
    )
    add_tooltip(poly_slider, _TT_TARGET_POLYCOUNT)
    poly_scope_row = ScopeButtonRow()
    poly_scope_row.set_callback("sel", lambda: _resample_target_poly("CURRENT", int(poly_slider.value())))
    poly_scope_row.set_callback("tree", lambda: _resample_target_poly("TREE", int(poly_slider.value())))
    poly_scope_row.set_callback("all", lambda: _resample_target_poly("ALL", int(poly_slider.value())))
    poly_scope_row.set_tooltips(
        sel="Resample selection to target polycount",
        tree="Resample subtree to target polycount",
        all="Resample all to target polycount",
    )

    poly_row = QWidget()
    poly_row_layout = QHBoxLayout(poly_row)
    poly_row_layout.setContentsMargins(0, 0, 0, 0)
    poly_row_layout.setSpacing(4)
    poly_row_layout.addWidget(poly_label)
    poly_row_layout.addWidget(poly_slider, stretch=1)
    poly_row_layout.addWidget(poly_scope_row)
    layout.addWidget(poly_row)

    # --- Row 1: Density ---
    density_label = QLabel("Density:")
    add_tooltip(density_label, _TT_TARGET_DENSITY)
    density_label.setFixedWidth(_LABEL_WIDTH)
    density_label.setStyleSheet("color: #ddd;")
    density_slider = QEnhancedSlider(
        min_value=0.01,
        max_value=1_000_000.0,
        default_value=100.0,
        step=10.0,
        decimals=2,
        logarithmic=True,
        hard_min=0.01,
        hard_max=1_000_000.0,
    )
    add_tooltip(density_slider, _TT_DENSITY_SLIDER)
    density_suffix = QLabel("tris/unit²")
    density_suffix.setStyleSheet("color: #888; font-size: 10px;")
    density_scope_row = ScopeButtonRow()
    density_scope_row.set_callback("sel", lambda: _resample_target_density("CURRENT", density_slider.value()))
    density_scope_row.set_callback("tree", lambda: _resample_target_density("TREE", density_slider.value()))
    density_scope_row.set_callback("all", lambda: _resample_target_density("ALL", density_slider.value()))
    density_scope_row.set_tooltips(
        sel="Resample selection to target density",
        tree="Resample subtree to target density",
        all="Resample all to target density",
    )

    density_row = QWidget()
    density_row_layout = QHBoxLayout(density_row)
    density_row_layout.setContentsMargins(0, 0, 0, 0)
    density_row_layout.setSpacing(4)
    density_row_layout.addWidget(density_label)
    density_row_layout.addWidget(density_slider, stretch=1)
    density_row_layout.addWidget(density_suffix)
    density_row_layout.addWidget(density_scope_row)
    layout.addWidget(density_row)

    # =========================================================================
    # Estimated polycount readout (live, updates on slider / scope changes)
    # =========================================================================
    est_header = QLabel("Estimated polycount:")
    est_header.setStyleSheet("color: #aaa; font-size: 10px; padding: 4px 0px 2px 0px;")
    layout.addWidget(est_header)

    est_readout = QLabel("")
    est_readout.setStyleSheet("color: #888; font-size: 10px; padding-left: 4px;")
    est_readout.setWordWrap(False)
    est_readout.setMinimumHeight(32)  # prevent layout jiggle when badges appear

    def _update_polycount_estimate(*args: object) -> None:
        """Update target + density polycount estimates with color, memory, warnings."""
        try:
            import coat
            root: coat.SceneElement | None = coat.Scene.sculptRoot()
            if not root:
                est_readout.setText("(no scene)")
                return

            visible: list = _iter_visible_sculpt(root)
            obj_count: int = len(visible)
            if obj_count == 0:
                est_readout.setText("(no visible objects)")
                return

            # ── Target polycount estimate (poly_slider × object count) ──
            target_per_obj: int = int(poly_slider.value())
            target_total: int = target_per_obj * obj_count
            t_color: str = _polycount_color(target_total)
            t_mem: str = _format_memory(target_total)
            t_badge: str = _warning_badge(target_total)
            t_fmt: str = f"{target_total:,}"

            # ── Density estimate (world-space density prediction) ──
            density: float = density_slider.value()
            dens_total: int = 0
            for el in visible:
                vol: "coat.Volume" = el.Volume()
                if vol.getPolycount() <= 0:
                    continue
                aabb: "coat.boundbox" = vol.calcWorldSpaceAABB()
                size: "coat.vec3" = aabb.GetSize()
                avg_dim: float = (size.x + size.y + size.z) / 3.0
                if avg_dim <= 0.0:
                    continue
                dens_total += int(density * avg_dim * avg_dim)

            d_color: str = _polycount_color(dens_total)
            d_mem: str = _format_memory(dens_total)
            d_badge: str = _warning_badge(dens_total)
            d_fmt: str = f"{dens_total:,}"

            # ── Build HTML lines ──
            lines: list[str] = []

            # Line 1: Target polycount estimate
            lines.append(
                f'<span style="color:#aaa;">Target: </span>'
                f'~<span style="color:{t_color};font-weight:bold;">{t_fmt}</span>'
                f'<span style="color:#aaa;"> polys across {obj_count} objects'
                f'<span style="color:#888;"> · ~{t_mem} RAM</span>'
                f'{t_badge}'
            )

            # Line 2: Density estimate
            if dens_total > 0:
                lines.append(
                    f'<span style="color:#aaa;">Density: </span>'
                    f'~<span style="color:{d_color};font-weight:bold;">{d_fmt}</span>'
                    f'<span style="color:#aaa;"> polys across {obj_count} objects'
                    f'<span style="color:#888;"> · ~{d_mem} RAM</span>'
                    f'{d_badge}'
                )

            est_readout.setText("<br>".join(lines))
        except Exception:
            est_readout.setText("(no visible objects)")

    poly_slider.value_changed.connect(_update_polycount_estimate)
    density_slider.value_changed.connect(_update_polycount_estimate)
    layout.addWidget(est_readout)
    # Fire once to populate initial value
    _update_polycount_estimate()

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_resample_section(*args, **kwargs):  # type: ignore
        return None
