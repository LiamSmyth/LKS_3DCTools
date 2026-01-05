"""
LKS UI - Autopo Tools Collapsible Section.

A collapsible section containing autopo workflow configuration:
- Target polycount
- Capture details slider
- Auto density slider
- Option checkboxes (hardsurface, tangent smooth, voxelize, bypass modal)
- Voxelize polycount
- Decimate options
- Run buttons

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
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QLabel, QSlider, QSpinBox, QCheckBox,
    )
    from PySide6.QtCore import Qt
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from ui.ui_widget_sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


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
        title="🎯 Autopo", color="#ffcc80", collapsed=True)
    layout = section.content_layout

    settings = get_autopo_settings()

    # --- State storage for widgets ---
    widgets: dict = {}

    # --- Save function (defined early so it can be used in connect() calls) ---
    def save_autopo_settings() -> None:
        try:
            from utils.lks_settings import get_autopo_settings, save_autopo_settings as save_fn
            s = get_autopo_settings()
            s.autopo_polycount = widgets["polycount"].value()
            s.autopo_capture_details = widgets["capture_details"].value(
            ) / 100.0
            s.autopo_auto_density = widgets["auto_density"].value() / 100.0
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

    # --- Target Polycount ---
    layout.addWidget(create_sub_header("Target Polycount"))

    poly_row = QHBoxLayout()
    poly_row.setContentsMargins(0, 0, 0, 0)
    poly_spin = QSpinBox()
    poly_spin.setRange(1, 1000000)
    poly_spin.setSingleStep(1000)
    poly_spin.setValue(settings.autopo_polycount)
    poly_spin.setToolTip("Target polycount for autopo")
    widgets["polycount"] = poly_spin
    poly_row.addWidget(poly_spin)

    poly_container = QWidget()
    poly_container.setLayout(poly_row)
    poly_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(poly_container)

    # --- Capture Details slider (0-100%) ---
    details_row = QHBoxLayout()
    details_row.setContentsMargins(0, 0, 0, 0)
    details_label = QLabel("Capture Details:")
    details_label.setMinimumWidth(100)
    details_slider = QSlider(Qt.Horizontal)
    details_slider.setRange(0, 100)
    details_slider.setSingleStep(5)
    details_slider.setValue(int(settings.autopo_capture_details * 100))
    details_slider.setToolTip("Detail capture amount (0-100%)")
    details_value = QLabel(f"{int(settings.autopo_capture_details * 100)}%")
    details_value.setMinimumWidth(35)
    widgets["capture_details"] = details_slider
    widgets["capture_details_label"] = details_value

    def on_capture_changed(value: int) -> None:
        details_value.setText(f"{value}%")
        save_autopo_settings()

    details_slider.valueChanged.connect(on_capture_changed)
    details_row.addWidget(details_label)
    details_row.addWidget(details_slider)
    details_row.addWidget(details_value)

    details_container = QWidget()
    details_container.setLayout(details_row)
    details_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(details_container)

    # --- Auto Density slider (0-200%) ---
    density_row = QHBoxLayout()
    density_row.setContentsMargins(0, 0, 0, 0)
    density_label = QLabel("Auto Density:")
    density_label.setMinimumWidth(100)
    density_slider = QSlider(Qt.Horizontal)
    density_slider.setRange(0, 200)
    density_slider.setSingleStep(10)
    density_slider.setValue(int(settings.autopo_auto_density * 100))
    density_slider.setToolTip("Painted density influence (0-200%)")
    density_value = QLabel(f"{int(settings.autopo_auto_density * 100)}%")
    density_value.setMinimumWidth(35)
    widgets["auto_density"] = density_slider
    widgets["auto_density_label"] = density_value

    def on_density_changed(value: int) -> None:
        density_value.setText(f"{value}%")
        save_autopo_settings()

    density_slider.valueChanged.connect(on_density_changed)
    density_row.addWidget(density_label)
    density_row.addWidget(density_slider)
    density_row.addWidget(density_value)

    density_container = QWidget()
    density_container.setLayout(density_row)
    density_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(density_container)

    # --- Checkboxes row 1: hardsurface, tangent smooth ---
    layout.addWidget(create_sub_header("Options"))

    check_row1 = QHBoxLayout()
    check_row1.setContentsMargins(0, 0, 0, 0)
    hardsurface_cb = QCheckBox("Hardsurface")
    hardsurface_cb.setChecked(settings.autopo_hardsurface)
    hardsurface_cb.setToolTip("Optimize for hard surface models")
    widgets["hardsurface"] = hardsurface_cb

    tangent_cb = QCheckBox("Tangent Smooth")
    tangent_cb.setChecked(settings.autopo_tangent_smooth)
    tangent_cb.setToolTip("Apply tangent smoothing")
    widgets["tangent_smooth"] = tangent_cb

    hardsurface_cb.stateChanged.connect(save_autopo_settings)
    tangent_cb.stateChanged.connect(save_autopo_settings)
    check_row1.addWidget(hardsurface_cb)
    check_row1.addWidget(tangent_cb)

    check_container1 = QWidget()
    check_container1.setLayout(check_row1)
    check_container1.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(check_container1)

    # --- Checkboxes row 2: voxelize, bypass modal ---
    check_row2 = QHBoxLayout()
    check_row2.setContentsMargins(0, 0, 0, 0)
    voxelize_cb = QCheckBox("Voxelize")
    voxelize_cb.setChecked(settings.autopo_voxelize)
    voxelize_cb.setToolTip("Voxelize after autopo")
    widgets["voxelize"] = voxelize_cb

    bypass_cb = QCheckBox("Bypass Modal")
    bypass_cb.setChecked(settings.autopo_bypass_density_modal)
    bypass_cb.setToolTip("Skip density modal dialog")
    widgets["bypass_modal"] = bypass_cb

    voxelize_cb.stateChanged.connect(save_autopo_settings)
    bypass_cb.stateChanged.connect(save_autopo_settings)
    check_row2.addWidget(voxelize_cb)
    check_row2.addWidget(bypass_cb)

    check_container2 = QWidget()
    check_container2.setLayout(check_row2)
    check_container2.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(check_container2)

    # --- Voxelize polycount (x1000) ---
    vox_row = QHBoxLayout()
    vox_row.setContentsMargins(0, 0, 0, 0)
    vox_label = QLabel("Vox Polys (K):")
    vox_label.setMinimumWidth(90)
    vox_spin = QSpinBox()
    vox_spin.setRange(100, 10000)
    vox_spin.setSingleStep(100)
    vox_spin.setValue(settings.autopo_voxelize_polycount)
    vox_spin.setToolTip("Voxelize target polycount (x1000)")
    widgets["vox_polycount"] = vox_spin

    vox_spin.valueChanged.connect(save_autopo_settings)
    vox_row.addWidget(vox_label)
    vox_row.addWidget(vox_spin)

    vox_container = QWidget()
    vox_container.setLayout(vox_row)
    vox_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(vox_container)

    # --- Decimate options ---
    dec_row = QHBoxLayout()
    dec_row.setContentsMargins(0, 0, 0, 0)
    dec_cb = QCheckBox("Decimate If Above")
    dec_cb.setChecked(settings.autopo_decimate_if_above)
    dec_cb.setToolTip("Decimate if above limit")
    widgets["decimate_if_above"] = dec_cb

    dec_cb.stateChanged.connect(save_autopo_settings)
    dec_row.addWidget(dec_cb)

    dec_container = QWidget()
    dec_container.setLayout(dec_row)
    dec_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(dec_container)

    dec_limit_row = QHBoxLayout()
    dec_limit_row.setContentsMargins(0, 0, 0, 0)
    dec_limit_label = QLabel("Dec Limit (K):")
    dec_limit_label.setMinimumWidth(90)
    dec_limit_spin = QSpinBox()
    dec_limit_spin.setRange(1, 1000)
    dec_limit_spin.setSingleStep(5)
    dec_limit_spin.setValue(settings.autopo_decimation_limit)
    dec_limit_spin.setToolTip("Decimation limit (x1000 polys)")
    widgets["decimation_limit"] = dec_limit_spin

    dec_limit_spin.valueChanged.connect(save_autopo_settings)
    dec_limit_row.addWidget(dec_limit_label)
    dec_limit_row.addWidget(dec_limit_spin)

    dec_limit_container = QWidget()
    dec_limit_container.setLayout(dec_limit_row)
    dec_limit_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(dec_limit_container)

    # Connect polycount spin to save
    poly_spin.valueChanged.connect(save_autopo_settings)

    # --- Run buttons ---
    layout.addWidget(create_sub_header("Run Autopo"))

    def autopo_run() -> None:
        try:
            from utils.autopo_utils import execute_autopo, AutopoParams
            from utils.lks_settings import get_autopo_settings
            s = get_autopo_settings()
            params = AutopoParams(
                target_polycount=s.autopo_polycount,
                capture_details=s.autopo_capture_details,
                auto_density=s.autopo_auto_density,
                hardsurface=s.autopo_hardsurface,
            )
            execute_autopo(params)
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
    run_grid.add_button("Run", autopo_run, "Run autopo with settings")
    run_grid.add_button("→ Sculpt", autopo_to_sculpt,
                        "Autopo then import to sculpt")
    run_grid.add_button("→ Multires", autopo_to_multires,
                        "Autopo then import as multires")
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

    show_retopo_container = QWidget()
    show_retopo_container.setLayout(show_retopo_row)
    show_retopo_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(show_retopo_container)

    # --- Delete matching retopo objects ---
    def delete_matching_retopos() -> None:
        """Delete retopo objects whose names match selected sculpt elements."""
        try:
            import coat
            from utils.scene_api import SceneAPI

            # Get selected sculpt element names
            selected_elements: list[coat.SceneElement] = SceneAPI.get_selected_elements(
            )
            if not selected_elements:
                log_error("No sculpt objects selected")
                return

            sculpt_names: set[str] = {el.name() for el in selected_elements}

            # Get retopo model
            retopo_model: coat.Model = coat.Model.fromRetopo()
            objects_count: int = retopo_model.getObjectsCount()

            if objects_count == 0:
                log_error("No retopo objects found")
                return

            # Find matching retopo objects (iterate in reverse to safely delete)
            deleted_count: int = 0
            for i in range(objects_count - 1, -1, -1):
                retopo_name: str = retopo_model.getObjectName(i)
                if retopo_name in sculpt_names:
                    retopo_model.removeObject(i)
                    deleted_count += 1

            if deleted_count > 0:
                log_success(f"Deleted {deleted_count} retopo object(s)")
            else:
                log_error("No matching retopo objects found")

        except Exception as e:
            log_error(f"Failed to delete retopos: {e}")

    delete_grid = ButtonGrid(columns=1)
    delete_grid.add_button(
        "🗑️ Delete Retopos",
        delete_matching_retopos,
        "Delete retopo objects matching selected sculpt elements"
    )
    layout.addWidget(delete_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_autopo_section(*args, **kwargs):  # type: ignore
        return None
