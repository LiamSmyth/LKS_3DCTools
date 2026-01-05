"""
LKS UI - Dynamic Subdiv Tools Collapsible Section.

A collapsible section containing dynamic subdivision controls:
- Details level increment/decrement
- Apply to all brushes

Usage:
    from ui.ui_collapsible_subdiv_tools import create_subdiv_section
    section = create_subdiv_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from ui.ui_widget_sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# SUBDIV SECTION FACTORY
# =============================================================================

def create_subdiv_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible dynamic subdivision section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree (unused but kept for consistency)

    Returns:
        CollapsibleSection widget with subdiv tools
    """
    section = CollapsibleSection(
        title="🔺 Dynamic Subdiv", color="#a5d6a7", collapsed=True)
    layout = section.content_layout

    # --- Details Level ---
    layout.addWidget(create_sub_header("Details Level"))

    def increment_level() -> None:
        try:
            from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
            from utils.lks_settings import get_brush_settings, save_brush_settings
            settings = get_brush_settings()
            new_level: float = min(8.0, settings.details_level + 1.0)
            settings.details_level = int(new_level)
            settings.auto_subdivide = True
            save_brush_settings()
            apply_auto_subdivide_all(True)
            apply_details_level_all(new_level)
            log_success(f"Details level: {new_level}")
        except Exception as e:
            log_error(f"Increment failed: {e}")

    def decrement_level() -> None:
        try:
            from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
            from utils.lks_settings import get_brush_settings, save_brush_settings
            settings = get_brush_settings()
            new_level: float = max(0.0, settings.details_level - 1.0)
            settings.details_level = int(new_level)
            settings.auto_subdivide = True
            save_brush_settings()
            apply_auto_subdivide_all(True)
            apply_details_level_all(new_level)
            log_success(f"Details level: {new_level}")
        except Exception as e:
            log_error(f"Decrement failed: {e}")

    def apply_brush_settings() -> None:
        try:
            from utils.brush_settings_utils import (
                apply_auto_subdivide_all,
                apply_details_level_all,
                apply_remove_stretching_all,
            )
            from utils.lks_settings import get_brush_settings
            settings = get_brush_settings()
            apply_auto_subdivide_all(settings.auto_subdivide)
            apply_details_level_all(float(settings.details_level))
            apply_remove_stretching_all(settings.remove_stretching)
            log_success("Applied to all brushes")
        except Exception as e:
            log_error(f"Apply failed: {e}")

    level_grid = ButtonGrid(columns=3)
    level_grid.add_button("−", decrement_level, "Decrement level")
    level_grid.add_button("+", increment_level, "Increment level")
    level_grid.add_button(
        "Apply All", apply_brush_settings, "Apply to all brushes")
    layout.addWidget(level_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_subdiv_section(*args, **kwargs):  # type: ignore
        return None
