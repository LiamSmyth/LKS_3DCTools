"""
LKS UI - Layers Tools Collapsible Section.

A collapsible section containing layer management:
- Setup standard layers (Sculpt/Color)
- Clean empty layers
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
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, add_tooltip
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# TOOLTIPS FOR LAYER OPERATIONS
# =============================================================================

TOOLTIP_SETUP_LAYERS: str = """
<b>Setup Standard Layers</b><br><br>
Creates the standard 2-layer setup for sculpting:<br>
• <b>Layer 0</b> - "Sculpt" (Depth layer, 100% opacity)<br>
• <b>Layer 1</b> - "Color" (Vertex colors, 100% opacity)<br><br>
<i>Non-destructive: existing layers are preserved.</i>
"""

TOOLTIP_CLEAN_LAYERS: str = """
<b>Clean Empty Layers</b><br><br>
Removes layers created by mesh operations that<br>
are empty or no longer needed.<br><br>
Use after decimate, resample, or boolean operations<br>
to clean up unwanted layer clutter.<br><br>
<i>Non-destructive: only removes empty layers.</i>
"""

TOOLTIP_CONSOLIDATE_LAYERS: str = """
<b>Consolidate All Layers</b><br><br>
Merges ALL layers down into the standard 2-layer setup:<br>
• Flattens all sculpt depth into Layer 0<br>
• Flattens all vertex colors into Layer 1<br><br>
<span style="color:#ffb74d"><b>⚠ DESTRUCTIVE:</b></span> This cannot be undone!<br>
All layer separations will be permanently lost.<br><br>
<i>Use when you want to simplify a complex layer stack.</i>
"""


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

    def consolidate_layers() -> None:
        try:
            from utils.Scene_layer_utils import consolidate_layers as do_consolidate
            do_consolidate()
            log_success("Layers consolidated")
        except Exception as e:
            log_error(f"Layer consolidation failed: {e}")

    # Create button grid - 3 columns for the 3 layer operations
    grid = ButtonGrid(columns=3)

    # Add buttons and capture references for tooltips
    btn_setup = grid.add_button(
        "Setup", setup_layers, "Create standard layers")
    btn_clean = grid.add_button("Clean", clean_layers, "Remove empty layers")
    btn_consolidate = grid.add_button(
        "Consolidate", consolidate_layers, "Merge all layers")

    # Add rich tooltips explaining each operation
    if btn_setup:
        add_tooltip(btn_setup, TOOLTIP_SETUP_LAYERS)
    if btn_clean:
        add_tooltip(btn_clean, TOOLTIP_CLEAN_LAYERS)
    if btn_consolidate:
        add_tooltip(btn_consolidate, TOOLTIP_CONSOLIDATE_LAYERS)

    layout.addWidget(grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_layers_section(*args, **kwargs):  # type: ignore
        return None
