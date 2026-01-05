"""
LKS UI - Layers Tools Collapsible Section.

A collapsible section containing layer management:
- Setup standard layers (Sculpt/Color)
- Clean empty layers

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
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# LAYERS SECTION FACTORY
# =============================================================================

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
        title="📚 Layers", color="#90caf9", collapsed=True)
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
            log_success("Cleaned empty layers")
        except Exception as e:
            log_error(f"Layer cleanup failed: {e}")

    grid = ButtonGrid(columns=2)
    grid.add_button("Setup Layers", setup_layers, "Create Sculpt/Color layers")
    grid.add_button("Clean Layers", clean_layers, "Remove empty layers")
    layout.addWidget(grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_layers_section(*args, **kwargs):  # type: ignore
        return None
