"""
LKS UI - Autopo Tools Collapsible Section.

A collapsible section containing autopo workflow configuration:
- Preprocess: Voxelize and decimate inline checkboxes with spinboxes
- Target polycount slider
- Capture details slider
- Auto density slider
- Option checkboxes (hardsurface, tangent smooth, skip dialog)
- Run buttons
- Delete retopo buttons

Usage:
    from ui.ui_collapsible_autopo_tools import create_autopo_section
    section = create_autopo_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QSizePolicy, QWidget, QHBoxLayout, QLabel, QSpinBox, QCheckBox,
    )
    from lks_utils.gui_qt.widgets.enhanced_slider import QEnhancedSlider
    from lks_utils.gui_qt.widgets.q_dial_enum_picker import QDialEnumPicker
    from lks_utils.gui_qt.widgets.dial_enum_option import DialEnumOption
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, GridRowTable, Align, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.sub_header import create_sub_header
    from utils.ui.widgets.badge_button import _make_icon_from_svg
    from utils.menu_action_tooltip import action_menu_tooltip

    _PLAY_ICON: QIcon = _make_icon_from_svg("play")
    _AUTOPO_ICON: QIcon = _make_icon_from_svg("autopo")
    _DELETE_ICON: QIcon = _make_icon_from_svg("delete")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 90
_AUTOPO_DENSITY_UI_TO_API: float = 50.0  # UI 0–100% ↔ API 0.0–2.0
_TT_CAPTURE_DETAILS = MarkdownFileResource("data/tooltips/autopo_capture_details.md", base_dir=__file__)
_TT_DENSITY = MarkdownFileResource("data/tooltips/autopo_density.md", base_dir=__file__)
_TT_SKIP_DIALOG = MarkdownFileResource("data/tooltips/autopo_skip_dialog.md", base_dir=__file__)
_TT_QUALITY = MarkdownFileResource("data/tooltips/autopo_quality.md", base_dir=__file__)
_TT_HARDSURFACE = MarkdownFileResource("data/tooltips/autopo_hardsurface.md", base_dir=__file__)
_TT_TANGENT = MarkdownFileResource("data/tooltips/autopo_tangent.md", base_dir=__file__)
_TT_VOXELIZE = MarkdownFileResource("data/tooltips/autopo_voxelize.md", base_dir=__file__)
_TT_VOXELIZE_POLY = MarkdownFileResource("data/tooltips/autopo_voxelize_polycount.md", base_dir=__file__)
_TT_DECIMATE_PRE = MarkdownFileResource("data/tooltips/autopo_decimate_preprocess.md", base_dir=__file__)
_TT_DECIMATE_LIMIT = MarkdownFileResource("data/tooltips/autopo_decimate_limit.md", base_dir=__file__)
_TT_POLYCOUNT = MarkdownFileResource("data/tooltips/autopo_polycount.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_autopo.md", base_dir=__file__)

# =============================================================================
# AUTOPO SECTION FACTORY
# =============================================================================

def create_autopo_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible autopo tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with autopo tools
    """
    from utils.lks_settings import get_autopo_settings

    section = CollapsibleSection(
        title="Autopo", icon_name="autopo", collapsed=True, state_key="section_autopo",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    settings = get_autopo_settings()

    # --- State storage for widgets ---
    widgets: dict = {}

    # --- Save function (defined early so it can be used in connect() calls) ---
    def save_autopo_settings() -> None:
        try:
            from utils.lks_settings import get_autopo_settings, save_autopo_settings as save_fn
            s = get_autopo_settings()
            s.autopo_polycount = int(widgets["polycount"].value())
            s.autopo_capture_details = widgets["capture_details"].value(
            ) / 100.0
            s.autopo_auto_density = (
                widgets["auto_density"].value() / _AUTOPO_DENSITY_UI_TO_API
            )
            s.autopo_hardsurface = widgets["hardsurface"].isChecked()
            s.autopo_tangent_smooth = widgets["tangent_smooth"].isChecked()
            s.autopo_voxelize = widgets["voxelize"].isChecked()
            s.autopo_bypass_density_modal = widgets["bypass_modal"].isChecked()
            s.autopo_voxelize_polycount = widgets["vox_polycount"].value()
            s.autopo_decimate_if_above = widgets["decimate_if_above"].isChecked(
            )
            s.autopo_decimation_limit = widgets["decimation_limit"].value()
            save_fn()
        except Exception as e:
            log_error(f"Failed to save autopo settings: {e}")

    def save_autopo_quality() -> None:
        """Save quality dropdown separately."""
        try:
            from utils.lks_settings import get_autopo_settings, save_autopo_settings as save_fn
            s = get_autopo_settings()
            quality_picker = widgets["quality"]
            s.autopo_quality = quality_picker.current_value()
            save_fn()
        except Exception as e:
            log_error(f"Failed to save autopo quality: {e}")

    # --- Preprocess Header ---
    layout.addWidget(create_sub_header("Preprocess"))

    # --- Voxelize & Decimate GridRowTable ---
    table2 = GridRowTable()

    # Row 0: Voxelize
    voxelize_cb = QCheckBox()
    voxelize_cb.setChecked(settings.autopo_voxelize)
    add_tooltip(voxelize_cb, _TT_VOXELIZE)
    widgets["voxelize"] = voxelize_cb
    voxelize_cb.stateChanged.connect(save_autopo_settings)

    vox_spin = QSpinBox()
    vox_spin.setRange(100, 10000)
    vox_spin.setSingleStep(100)
    vox_spin.setValue(settings.autopo_voxelize_polycount)
    add_tooltip(vox_spin, _TT_VOXELIZE_POLY)
    widgets["vox_polycount"] = vox_spin
    vox_spin.valueChanged.connect(save_autopo_settings)

    vox_label_widget = QWidget()
    vox_label_layout = QHBoxLayout(vox_label_widget)
    vox_label_layout.setContentsMargins(0, 0, 0, 0)
    vox_label_layout.setSpacing(4)
    vox_row_label = QLabel("Voxelize to K polys:")
    add_tooltip(vox_row_label, _TT_VOXELIZE)
    vox_label_layout.addWidget(vox_row_label)
    vox_label_layout.addWidget(voxelize_cb)
    vox_label_layout.addStretch()

    vox_control = QWidget()
    vox_control_layout = QHBoxLayout(vox_control)
    vox_control_layout.setContentsMargins(0, 0, 0, 0)
    vox_control_layout.addWidget(vox_spin)
    vox_control_layout.addStretch()

    table2.add_cell(0, 0, vox_label_widget, Align.LEFT)
    table2.add_cell(0, 1, vox_control)

    # Row 1: Decimate
    dec_cb = QCheckBox()
    dec_cb.setChecked(settings.autopo_decimate_if_above)
    add_tooltip(dec_cb, _TT_DECIMATE_PRE)
    widgets["decimate_if_above"] = dec_cb
    dec_cb.stateChanged.connect(save_autopo_settings)

    dec_limit_spin = QSpinBox()
    dec_limit_spin.setRange(1, 1000)
    dec_limit_spin.setSingleStep(5)
    dec_limit_spin.setValue(settings.autopo_decimation_limit)
    add_tooltip(dec_limit_spin, _TT_DECIMATE_LIMIT)
    widgets["decimation_limit"] = dec_limit_spin
    dec_limit_spin.valueChanged.connect(save_autopo_settings)

    dec_label_widget = QWidget()
    dec_label_layout = QHBoxLayout(dec_label_widget)
    dec_label_layout.setContentsMargins(0, 0, 0, 0)
    dec_label_layout.setSpacing(4)
    dec_row_label = QLabel("Decimate if above (K polys):")
    add_tooltip(dec_row_label, _TT_DECIMATE_PRE)
    dec_label_layout.addWidget(dec_row_label)
    dec_label_layout.addWidget(dec_cb)
    dec_label_layout.addStretch()

    dec_control = QWidget()
    dec_control_layout = QHBoxLayout(dec_control)
    dec_control_layout.setContentsMargins(0, 0, 0, 0)
    dec_control_layout.addWidget(dec_limit_spin)
    dec_control_layout.addStretch()

    table2.add_cell(1, 0, dec_label_widget, Align.LEFT)
    table2.add_cell(1, 1, dec_control)

    table2.finalize()
    table2.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    layout.addWidget(table2)

    # --- Target Polycount Header ---
    layout.addWidget(create_sub_header("Target Polycount"))

    # --- Row 0: Polycount (direct QHBoxLayout for proper slider expansion) ---
    poly_label = QLabel("Polycount:")
    poly_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(poly_label, _TT_POLYCOUNT)
    poly_slider = QEnhancedSlider(
        min_value=100.0,
        max_value=100_000.0,
        default_value=float(settings.autopo_polycount),
        step=100.0,
        decimals=0,
        logarithmic=True,
        hard_min=100.0,
        hard_max=100_000.0,
    )
    add_tooltip(poly_slider, _TT_POLYCOUNT)
    widgets["polycount"] = poly_slider

    def on_poly_changed(value: float) -> None:
        save_autopo_settings()

    poly_slider.value_changed.connect(on_poly_changed)

    poly_row = QWidget()
    poly_row_layout = QHBoxLayout(poly_row)
    poly_row_layout.setContentsMargins(0, 0, 0, 0)
    poly_row_layout.setSpacing(4)
    poly_row_layout.addWidget(poly_label)
    poly_row_layout.addWidget(poly_slider, stretch=1)
    layout.addWidget(poly_row)

    # --- Row 1: Capture Details ---
    details_label = QLabel("Capture Details:")
    details_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(details_label, _TT_CAPTURE_DETAILS)
    details_slider = QEnhancedSlider(
        min_value=0.0,
        max_value=100.0,
        default_value=float(int(settings.autopo_capture_details * 100)),
        step=5.0,
        decimals=0,
    )
    add_tooltip(details_slider, _TT_CAPTURE_DETAILS)
    details_value = QLabel(f"{int(settings.autopo_capture_details * 100)}%")
    details_value.setMinimumWidth(35)
    widgets["capture_details"] = details_slider
    widgets["capture_details_label"] = details_value

    def on_capture_changed(value: float) -> None:
        details_value.setText(f"{int(value)}%")
        save_autopo_settings()

    details_slider.value_changed.connect(on_capture_changed)

    details_row = QWidget()
    details_row_layout = QHBoxLayout(details_row)
    details_row_layout.setContentsMargins(0, 0, 0, 0)
    details_row_layout.setSpacing(4)
    details_row_layout.addWidget(details_label)
    details_row_layout.addWidget(details_slider, stretch=1)
    details_row_layout.addWidget(details_value)
    layout.addWidget(details_row)

    # --- Row 2: Auto Density ---
    _density_ui_pct: int = int(
        max(0.0, min(100.0, settings.autopo_auto_density * _AUTOPO_DENSITY_UI_TO_API))
    )
    density_label = QLabel("Auto Density:")
    density_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(density_label, _TT_DENSITY)
    density_slider = QEnhancedSlider(
        min_value=0.0,
        max_value=100.0,
        default_value=float(_density_ui_pct),
        step=5.0,
        decimals=0,
    )
    add_tooltip(density_slider, _TT_DENSITY)
    density_value = QLabel(f"{_density_ui_pct}%")
    density_value.setMinimumWidth(35)
    widgets["auto_density"] = density_slider
    widgets["auto_density_label"] = density_value

    def on_density_changed(value: float) -> None:
        density_value.setText(f"{int(value)}%")
        save_autopo_settings()

    density_slider.value_changed.connect(on_density_changed)

    density_row = QWidget()
    density_row_layout = QHBoxLayout(density_row)
    density_row_layout.setContentsMargins(0, 0, 0, 0)
    density_row_layout.setSpacing(4)
    density_row_layout.addWidget(density_label)
    density_row_layout.addWidget(density_slider, stretch=1)
    density_row_layout.addWidget(density_value)
    layout.addWidget(density_row)

    # --- Row 3: Quality ---
    quality_label = QLabel("Quality:")
    quality_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(quality_label, _TT_QUALITY)
    current_quality = getattr(
        settings, 'autopo_quality', 'intermediate') or 'intermediate'
    quality_options = [
        DialEnumOption(value="draft", label="Draft"),
        DialEnumOption(value="intermediate", label="Intermediate"),
        DialEnumOption(value="best", label="Best"),
    ]
    quality_index = max(0, [o.value for o in quality_options].index(current_quality))
    quality_combo = QDialEnumPicker(
        options=quality_options,
        current_index=quality_index,
        width=150,
        height=22,
    )
    add_tooltip(quality_combo, _TT_QUALITY)
    widgets["quality"] = quality_combo
    quality_combo.current_index_changed.connect(lambda idx: save_autopo_quality())

    quality_row = QWidget()
    quality_row_layout = QHBoxLayout(quality_row)
    quality_row_layout.setContentsMargins(0, 0, 0, 0)
    quality_row_layout.setSpacing(4)
    quality_row_layout.addWidget(quality_label)
    quality_row_layout.addWidget(quality_combo)
    quality_row_layout.addStretch()
    layout.addWidget(quality_row)

    # --- Estimated polycount readout (color-coded with memory and warning level) ---
    _AUTOPO_COLOR_BREAKPOINTS: list[tuple[int, str]] = [
        (0,       "#90caf9"),   # blue — very safe
        (1_000,   "#90caf9"),   # blue
        (5_000,   "#81c784"),   # green
        (20_000,  "#ffd54f"),   # yellow
        (50_000,  "#ef5350"),   # red — high
        (100_000, "#ef5350"),   # red — extreme
    ]

    def _autopo_polycolor(polys: int) -> str:
        """Interpolated hex color for autopo-scale polycounts."""
        if polys <= 0:
            return _AUTOPO_COLOR_BREAKPOINTS[0][1]
        for i in range(len(_AUTOPO_COLOR_BREAKPOINTS) - 1):
            lo_p, lo_c = _AUTOPO_COLOR_BREAKPOINTS[i]
            hi_p, hi_c = _AUTOPO_COLOR_BREAKPOINTS[i + 1]
            if lo_p <= polys <= hi_p:
                if lo_p == hi_p:
                    return lo_c
                t: float = (polys - lo_p) / (hi_p - lo_p)
                r1: int = int(lo_c[1:3], 16); g1: int = int(lo_c[3:5], 16); b1: int = int(lo_c[5:7], 16)
                r2: int = int(hi_c[1:3], 16); g2: int = int(hi_c[3:5], 16); b2: int = int(hi_c[5:7], 16)
                return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"
        return _AUTOPO_COLOR_BREAKPOINTS[-1][1]

    def _autopo_memory(polys: int) -> str:
        """Memory estimate at 64 bytes/poly."""
        mb: float = (polys * 64) / (1024 * 1024)
        if mb < 1024:
            return f"{mb:.0f} MB"
        return f"{mb / 1024:.1f} GB"

    def _autopo_badge(polys: int) -> str:
        """HTML warning badge for high/extreme polycounts."""
        if polys >= 50_000:
            return (
                ' <span style="background-color:#ef5350;color:#fff;'
                'padding:1px 5px;border-radius:3px;font-size:10px;'
                'font-weight:bold;">⚠ Extreme</span>'
            )
        if polys >= 20_000:
            return (
                ' <span style="background-color:#ffb74d;color:#1a1a1a;'
                'padding:1px 5px;border-radius:3px;font-size:10px;'
                'font-weight:bold;">⚠ High</span>'
            )
        return ""

    est_header = QLabel("Estimated polycount:")
    est_header.setStyleSheet("color: #aaa; font-size: 10px; padding: 4px 0px 2px 0px;")
    layout.addWidget(est_header)

    est_readout = QLabel("")
    est_readout.setStyleSheet("color: #888; font-size: 10px; padding-left: 4px;")
    est_readout.setWordWrap(False)
    est_readout.setMinimumHeight(32)

    def _update_autopo_estimate(*args: object) -> None:
        """Display polycount estimate with colour, memory, warnings."""
        try:
            target_polys: int = int(poly_slider.value())
            t_color: str = _autopo_polycolor(target_polys)
            t_mem: str = _autopo_memory(target_polys)
            t_badge: str = _autopo_badge(target_polys)

            est_readout.setText(
                f'<span style="color:{t_color};font-weight:bold;">{target_polys:,}</span>'
                f'<span style="color:#aaa;"> polys</span>'
                f'<span style="color:#888;"> · ~{t_mem} RAM</span>'
                f'{t_badge}'
            )
        except Exception:
            est_readout.setText("—")

    poly_slider.value_changed.connect(_update_autopo_estimate)
    layout.addWidget(est_readout)
    _update_autopo_estimate()  # initial value

    # --- Options: Hardsurface | Tangent Smooth | Skip Dialog (label-first, grid-aligned) ---
    layout.addWidget(create_sub_header("Options"))

    options_table = GridRowTable()

    hardsurface_cb = QCheckBox()
    hardsurface_cb.setChecked(settings.autopo_hardsurface)
    widgets["hardsurface"] = hardsurface_cb
    hardsurface_cb.stateChanged.connect(save_autopo_settings)

    hardsurface_label = QLabel("Hardsurface")
    add_tooltip(hardsurface_label, _TT_HARDSURFACE)
    add_tooltip(hardsurface_cb, _TT_HARDSURFACE)

    options_table.add_cell(0, 0, hardsurface_label, Align.LEFT)
    options_table.add_cell(0, 1, hardsurface_cb, Align.LEFT)

    tangent_cb = QCheckBox()
    tangent_cb.setChecked(settings.autopo_tangent_smooth)
    widgets["tangent_smooth"] = tangent_cb
    tangent_cb.stateChanged.connect(save_autopo_settings)

    tangent_label = QLabel("Tangent Smooth")
    add_tooltip(tangent_label, _TT_TANGENT)
    add_tooltip(tangent_cb, _TT_TANGENT)

    options_table.add_cell(1, 0, tangent_label, Align.LEFT)
    options_table.add_cell(1, 1, tangent_cb, Align.LEFT)

    bypass_cb = QCheckBox()
    bypass_cb.setChecked(settings.autopo_bypass_density_modal)
    widgets["bypass_modal"] = bypass_cb
    bypass_cb.stateChanged.connect(save_autopo_settings)

    bypass_label = QLabel("Skip Dialog")
    add_tooltip(bypass_label, _TT_SKIP_DIALOG)
    add_tooltip(bypass_cb, _TT_SKIP_DIALOG)

    options_table.add_cell(2, 0, bypass_label, Align.LEFT)
    options_table.add_cell(2, 1, bypass_cb, Align.LEFT)

    options_table.finalize()
    options_table.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    layout.addWidget(options_table)

    # --- Run buttons ---
    layout.addWidget(create_sub_header("Run Autopo"))

    def autopo_run() -> None:
        try:
            from utils.autopo_utils import run_autopo_with_settings
            # Use convenience function that loads ALL settings from cache
            run_autopo_with_settings()
            log_success("Autopo complete")
        except Exception as e:
            log_error(f"Autopo failed: {e}")

    def autopo_to_sculpt() -> None:
        try:
            from utils.autopo_utils import autopo_to_sculpt as ats
            ats()
            log_success("Autopo → Sculpt complete")
            refresh_tree()
        except Exception as e:
            log_error(f"Autopo to sculpt failed: {e}")

    def autopo_to_multires() -> None:
        try:
            from utils.autopo_utils import autopo_to_multiresolution
            autopo_to_multiresolution()
            log_success("Autopo → Multires complete")
            refresh_tree()
        except Exception as e:
            log_error(f"Autopo to multires failed: {e}")

    run_grid = ButtonGrid(columns=3)
    run_grid.add_button(
        "Run",
        autopo_run,
        action_menu_tooltip(
            "Run autopo with configured settings",
            "Autopo_Run.py",
        ),
        icon=_PLAY_ICON,
    )
    run_grid.add_button(
        "Autopo → Sculpt",
        autopo_to_sculpt,
        action_menu_tooltip(
            "Run autopo then import to sculpt room",
            "Autopo_ToSculpt.py",
        ),
        icon=_AUTOPO_ICON,
    )
    run_grid.add_button(
        "Autopo → Multires",
        autopo_to_multires,
        action_menu_tooltip(
            "Run autopo then import as multires object",
            "Autopo_ToMultires.py",
        ),
        icon=_AUTOPO_ICON,
    )
    layout.addWidget(run_grid)

    # --- Show Retopo in Sculpt checkbox ---
    show_retopo_row = QHBoxLayout()
    show_retopo_row.setContentsMargins(0, 0, 0, 0)
    show_retopo_cb = QCheckBox("Show Retopo in Sculpt")
    show_retopo_cb.setToolTip("Show retopo objects while in sculpt room")
    widgets["show_retopo"] = show_retopo_cb

    # Query initial state from 3DCoat
    try:
        import coat
        initial_state: bool = coat.ui.getBoolValue(
            "$ShowRetopoObjectsInVoxelRoom")
        show_retopo_cb.setChecked(initial_state)
    except Exception:
        pass  # If we can't query, leave unchecked

    def on_show_retopo_changed(state: int) -> None:
        try:
            import coat
            coat.ui.setBoolValue("$ShowRetopoObjectsInVoxelRoom", state != 0)
        except Exception as e:
            log_error(f"Failed to toggle show retopo: {e}")

    show_retopo_cb.stateChanged.connect(on_show_retopo_changed)
    show_retopo_row.addWidget(show_retopo_cb)
    show_retopo_row.addStretch()

    layout.addLayout(show_retopo_row)

    # --- Delete retopo objects ---
    def delete_current_retopo() -> None:
        """Delete the retopo object matching the currently selected sculpt element."""
        try:
            import coat
            from utils.scene_api import SceneAPI

            selected = SceneAPI.get_selected_elements()
            if not selected:
                log_error("No sculpt object selected")
                return

            name: str = selected[0].name()
            retopo_model: coat.Model = coat.Model.fromRetopo()
            for i in range(retopo_model.getObjectsCount() - 1, -1, -1):
                if retopo_model.getObjectName(i) == name:
                    retopo_model.removeObject(i)
                    log_success(f"Deleted retopo: {name}")
                    return
            log_error(f"No retopo object named '{name}' found")
        except Exception as e:
            log_error(f"Failed to delete retopo: {e}")

    def delete_all_retopos() -> None:
        """Delete all retopo objects in the scene."""
        try:
            import coat
            retopo_model: coat.Model = coat.Model.fromRetopo()
            count: int = retopo_model.getObjectsCount()
            if count == 0:
                log_error("No retopo objects found")
                return
            for i in range(count - 1, -1, -1):
                retopo_model.removeObject(i)
            log_success(f"Deleted {count} retopo object(s)")
        except Exception as e:
            log_error(f"Failed to delete all retopos: {e}")

    delete_grid = ButtonGrid(columns=2)
    delete_grid.add_button(
        "Delete Retopo",
        delete_current_retopo,
        "Delete the retopo object matching the selected sculpt element",
        icon=_DELETE_ICON,
    )
    delete_grid.add_button(
        "Delete All Retopos",
        delete_all_retopos,
        "Delete all retopo objects in the scene",
        icon=_DELETE_ICON,
    )
    layout.addWidget(delete_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_autopo_section(*args, **kwargs):  # type: ignore
        return None
