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
        QWidget, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
    )
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


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

    # --- Target Resample (sub-header) ---
    layout.addWidget(create_sub_header("Target Resample"))

    def _resample_target_poly(scope_name: str, poly: int) -> None:
        """Resample to the exact target polycount."""
        try:
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

    # --- Target Polycount row: Label + SpinBox + [Sel][Tree][All] ---
    poly_row = QHBoxLayout()
    poly_row.setContentsMargins(0, 0, 0, 0)

    poly_label = QLabel("Polycount:")
    poly_label.setMinimumWidth(70)
    poly_row.addWidget(poly_label)

    poly_spin = QSpinBox()
    poly_spin.setRange(100, 50_000_000)
    poly_spin.setSingleStep(1000)
    poly_spin.setValue(10000)
    poly_spin.setToolTip(
        "Resample each object to this exact polygon count "
        "(regardless of current size)"
    )
    poly_row.addWidget(poly_spin)

    poly_grid = ButtonGrid(columns=3)
    poly_grid.add_button(
        "☝️",
        lambda: _resample_target_poly("CURRENT", poly_spin.value()),
        "Resample selection to target polycount",
    )
    poly_grid.add_button(
        "🌳",
        lambda: _resample_target_poly("TREE", poly_spin.value()),
        "Resample subtree to target polycount",
    )
    poly_grid.add_button(
        "🌎",
        lambda: _resample_target_poly("ALL", poly_spin.value()),
        "Resample all to target polycount",
    )
    poly_row.addWidget(poly_grid)

    poly_container = QWidget()
    poly_container.setLayout(poly_row)
    poly_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(poly_container)

    # --- Target Density row: Label + SpinBox + suffix + [Sel][Tree][All] ---
    density_row = QHBoxLayout()
    density_row.setContentsMargins(0, 0, 0, 0)

    density_label = QLabel("Density:")
    density_label.setMinimumWidth(70)
    density_row.addWidget(density_label)

    density_spin = QDoubleSpinBox()
    density_spin.setRange(0.01, 1_000_000.0)
    density_spin.setDecimals(2)
    density_spin.setSingleStep(10.0)
    density_spin.setValue(100.0)
    density_spin.setToolTip(
        "Tris per world-unit² — larger objects get proportionally more "
        "polygons to maintain consistent detail density.  Default 100 "
        "works well at most scene scales; increase for finer detail."
    )
    density_row.addWidget(density_spin)

    density_suffix = QLabel("tris/unit²")
    density_suffix.setStyleSheet("color: #888; font-size: 10px;")
    density_row.addWidget(density_suffix)

    density_grid = ButtonGrid(columns=3)
    density_grid.add_button(
        "☝️",
        lambda: _resample_target_density("CURRENT", density_spin.value()),
        "Resample selection to target density",
    )
    density_grid.add_button(
        "🌳",
        lambda: _resample_target_density("TREE", density_spin.value()),
        "Resample subtree to target density",
    )
    density_grid.add_button(
        "🌎",
        lambda: _resample_target_density("ALL", density_spin.value()),
        "Resample all to target density",
    )
    density_row.addWidget(density_grid)

    density_container = QWidget()
    density_container.setLayout(density_row)
    density_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(density_container)

    # --- Density preview readout (live, updates on spinbox change) ---
    density_readout = QLabel("")
    density_readout.setStyleSheet("color: #888; font-size: 9px; padding-left: 4px;")

    def _update_density_preview(density: float) -> None:
        """Compute predicted total polycount at this density across the scene."""
        try:
            import coat
            root: coat.SceneElement | None = coat.Scene.sculptRoot()
            if not root:
                density_readout.setText("(no scene)")
                return

            total: int = 0
            count: int = 0
            for el in _iter_visible_sculpt(root):
                vol: coat.Volume = el.Volume()
                if vol.getPolycount() <= 0:
                    continue
                aabb: coat.boundbox = vol.calcWorldSpaceAABB()
                size: coat.vec3 = aabb.GetSize()
                avg_dim: float = (size.x + size.y + size.z) / 3.0
                if avg_dim <= 0.0:
                    continue
                predicted: int = int(density * avg_dim * avg_dim)
                total += predicted
                count += 1

            if count == 0:
                density_readout.setText("(no visible objects)")
            else:
                density_readout.setText(
                    f"predicted: ~{total:,} polys across {count} objects"
                )
        except Exception:
            # Swallow — preview is best-effort
            density_readout.setText("")

    density_spin.valueChanged.connect(_update_density_preview)
    layout.addWidget(density_readout)
    # Fire once to populate initial value
    _update_density_preview(density_spin.value())

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_resample_section(*args, **kwargs):  # type: ignore
        return None
