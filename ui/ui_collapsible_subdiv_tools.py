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
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QHBoxLayout

    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header
    from utils.ui.widgets.badge_button import _make_icon_from_svg
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.menu_action_tooltip import action_menu_tooltip

    _APPLY_ICON: QIcon = _make_icon_from_svg("apply")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_HELP = MarkdownFileResource("data/tooltips/help_subdiv.md", base_dir=__file__)


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
        title="Dynamic Subdiv", icon_name="subdivide", collapsed=True, state_key="section_subdiv",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    # --- Details Level ---
    sub_header_row = QHBoxLayout()
    sub_header_row.setContentsMargins(0, 0, 0, 0)
    sub_header_row.addWidget(create_sub_header("Details Level"))
    sub_header_row.addStretch()
    layout.addLayout(sub_header_row)

    def increment_level() -> None:
        try:
            from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
            from utils.lks_settings import get_brush_settings, save_brush_settings
            settings = get_brush_settings()
            new_level: float = settings.details_level + 0.5
            settings.details_level = new_level
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
            new_level: float = max(-1.0, settings.details_level - 0.5)
            settings.details_level = new_level
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
    level_grid.add_button(
        "−",
        decrement_level,
        action_menu_tooltip(
            "Decrement details level by 0.5 (enables auto-subdivide; applies to all brushes)",
            "Brush_DecrementDetailsLevel.py",
        ),
    )
    level_grid.add_button(
        "+",
        increment_level,
        action_menu_tooltip(
            "Increment details level by 0.5 (enables auto-subdivide; applies to all brushes)",
            "Brush_IncrementDetailsLevel.py",
        ),
    )
    level_grid.add_button(
        "Apply All",
        apply_brush_settings,
        action_menu_tooltip(
            "Apply cached dynamic subdiv settings to all brushes",
            "Brush_ApplyDynamicSubdivSettings.py",
        ),
        icon=_APPLY_ICON,
    )
    grid_row = QHBoxLayout()
    grid_row.setContentsMargins(0, 0, 0, 0)
    grid_row.addWidget(level_grid)
    grid_row.addStretch()
    layout.addLayout(grid_row)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_subdiv_section(*args, **kwargs):  # type: ignore
        return None
