"""
LKS UI - Tools Tab.

Container for collapsible tool sections. Loads individual section factories.

Usage:
    from ui.ui_tab_tools import create_tools_tab
    tab_content = create_tools_tab(log_success, log_error, refresh_tree)
    tabs.add_tab("🔧 Tools", tab_content)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# TOOLS TAB FACTORY
# =============================================================================

def create_tools_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create the tools tab containing collapsible tool sections.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree

    Returns:
        QWidget containing all tool sections
    """
    # Scroll area for many sections
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)

    # --- Load Collapsible Sections ---

    # Decimate Tools
    from ui.ui_collapsible_decimate_tools import create_decimate_section
    decimate_section = create_decimate_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(decimate_section)

    # Proxy/Cache Tools
    from ui.ui_collapsible_proxy_tools import create_proxy_section
    proxy_section = create_proxy_section(log_success, log_error, refresh_tree)
    layout.addWidget(proxy_section)

    # Resample Tools
    from ui.ui_collapsible_resample_tools import create_resample_section
    resample_section = create_resample_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(resample_section)

    # Mode Conversion Tools
    from ui.ui_collapsible_mode_tools import create_mode_section
    mode_section = create_mode_section(log_success, log_error, refresh_tree)
    layout.addWidget(mode_section)

    # Scale Tools
    from ui.ui_collapsible_scale_tools import create_scale_section
    scale_section = create_scale_section(log_success, log_error, refresh_tree)
    layout.addWidget(scale_section)

    # Visibility Tools
    from ui.ui_collapsible_visibility_tools import create_visibility_section
    visibility_section = create_visibility_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(visibility_section)

    # Ghost Tools
    from ui.ui_collapsible_ghost_tools import create_ghost_section
    ghost_section = create_ghost_section(log_success, log_error, refresh_tree)
    layout.addWidget(ghost_section)

    # Smart Actions
    from ui.ui_collapsible_smart_tools import create_smart_section
    smart_section = create_smart_section(log_success, log_error, refresh_tree)
    layout.addWidget(smart_section)

    # Autopo Tools
    from ui.ui_collapsible_autopo_tools import create_autopo_section
    autopo_section = create_autopo_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(autopo_section)

    # Dynamic Subdiv Tools
    from ui.ui_collapsible_subdiv_tools import create_subdiv_section
    subdiv_section = create_subdiv_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(subdiv_section)

    # Layers Tools
    from ui.ui_collapsible_layers_tools import create_layers_section
    layers_section = create_layers_section(
        log_success, log_error, refresh_tree)
    layout.addWidget(layers_section)

    # Add stretch at bottom
    layout.addStretch()

    scroll.setWidget(container)
    return scroll


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_tools_tab(*args, **kwargs) -> None:  # type: ignore
        return None
