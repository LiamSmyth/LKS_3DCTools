"""
LKS UI - Layers Tools Collapsible Section.

A collapsible section containing layer management:
- Setup standard layers (Sculpt/Color)
- Cleanup empty layers (then select Layer 0)
- Consolidate all layers

Usage:
    from ui.ui_collapsible_layers_tools import create_layers_section
    section = create_layers_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QSizePolicy
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.ui.widgets.badge_button import _make_icon_from_svg

    _LAYERS_ICON: QIcon = _make_icon_from_svg("layers")
    _CLEANUP_ICON: QIcon = _make_icon_from_svg("cleanup")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Tooltip resources (module-local directory)
_TT_SETUP = MarkdownFileResource("data/tooltips/layers_setup.md", base_dir=__file__)
_TT_CLEAN = MarkdownFileResource("data/tooltips/layers_clean.md", base_dir=__file__)
_TT_CONSOLIDATE = MarkdownFileResource("data/tooltips/layers_consolidate.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_layers.md", base_dir=__file__)


def create_layers_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible layers section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree (unused but kept for consistency)

    Returns:
        CollapsibleSection widget with layer tools
    """
    section = CollapsibleSection(
        title="Layers", icon_name="layers", collapsed=True, state_key="section_layers",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    def setup_layers() -> None:
        try:
            from utils.Scene_layer_utils import ensure_standard_layers
            ensure_standard_layers()
            log_success("Layers setup complete")
        except Exception as e:
            log_error(f"Layer setup failed: {e}")

    def clean_layers() -> None:
        try:
            from utils.Scene_cleanup_utils import cleanup_after_mesh_operation
            cleanup_after_mesh_operation()
            log_success("Cleaned empty layers; Layer 0 selected")
        except Exception as e:
            log_error(f"Layer cleanup failed: {e}")

    def consolidate_layers() -> None:
        try:
            from utils.Scene_layer_utils import consolidate_layers as do_consolidate
            do_consolidate()
            log_success("Layers consolidated")
        except Exception as e:
            log_error(f"Layer consolidation failed: {e}")

    grid = ButtonGrid(columns=3)
    grid.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

    btn_setup = grid.add_button("Setup", setup_layers, "Create standard layers", icon=_LAYERS_ICON)
    btn_clean = grid.add_button(
        "Cleanup Empty", clean_layers, "Remove empty layers; select Layer 0", icon=_CLEANUP_ICON)
    btn_consolidate = grid.add_button("Consolidate", consolidate_layers, "Merge all layers", icon=_LAYERS_ICON)

    if btn_setup:
        add_tooltip(btn_setup, _TT_SETUP)
    if btn_clean:
        add_tooltip(btn_clean, _TT_CLEAN)
    if btn_consolidate:
        add_tooltip(btn_consolidate, _TT_CONSOLIDATE)

    layout.addWidget(grid)
    layout.addStretch()

    return section


if not HAS_QT:
    def create_layers_section(*args, **kwargs):  # type: ignore
        return None
