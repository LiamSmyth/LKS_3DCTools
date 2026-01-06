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
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame

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
    # Use tab factory for consistent structure
    from utils.ui.widgets import create_tab_with_revert
    tab = create_tab_with_revert(log_success, log_error, title="Tools")
    layout = tab.content_layout

    # --- Scope Icon Legend ---
    legend_frame = QFrame()
    legend_frame.setStyleSheet("""
        QFrame {
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 4px;
        }
    """)
    legend_layout = QHBoxLayout(legend_frame)
    legend_layout.setContentsMargins(8, 4, 8, 4)
    legend_layout.setSpacing(12)
    
    legend_title = QLabel("Scope:")
    legend_title.setStyleSheet("font-weight: bold; color: #90caf9; background: transparent;")
    legend_layout.addWidget(legend_title)
    
    sel_label = QLabel("☝️ Selected")
    sel_label.setStyleSheet("color: #ddd; background: transparent;")
    legend_layout.addWidget(sel_label)
    
    tree_label = QLabel("🌳 Subtree")
    tree_label.setStyleSheet("color: #ddd; background: transparent;")
    legend_layout.addWidget(tree_label)
    
    all_label = QLabel("🌎 All")
    all_label.setStyleSheet("color: #ddd; background: transparent;")
    legend_layout.addWidget(all_label)

    invert_label = QLabel("🔄 Invert")
    invert_label.setStyleSheet("color: #ddd; background: transparent;")
    legend_layout.addWidget(invert_label)
    
    legend_layout.addStretch()
    layout.addWidget(legend_frame)

    # --- Reorderable Sections in GripBoxContainer ---
    from utils.ui.widgets import GripBoxContainer
    grip_container = GripBoxContainer()
    layout.addWidget(grip_container)

    # --- Load Collapsible Sections ---

    # Decimate Tools
    from ui.ui_collapsible_decimate_tools import create_decimate_section
    decimate_section = create_decimate_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(decimate_section, "decimate_section")

    # Proxy/Cache Tools
    from ui.ui_collapsible_proxy_tools import create_proxy_section
    proxy_section = create_proxy_section(log_success, log_error, refresh_tree)
    grip_container.add_widget(proxy_section, "proxy_section")

    # Resample Tools
    from ui.ui_collapsible_resample_tools import create_resample_section
    resample_section = create_resample_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(resample_section, "resample_section")

    # Mode Conversion Tools
    from ui.ui_collapsible_mode_tools import create_mode_section
    mode_section = create_mode_section(log_success, log_error, refresh_tree)
    grip_container.add_widget(mode_section, "mode_section")

    # Scale Tools
    from ui.ui_collapsible_scale_tools import create_scale_section
    scale_section = create_scale_section(log_success, log_error, refresh_tree)
    grip_container.add_widget(scale_section, "scale_section")

    # Visibility & Ghost Tools (merged)
    from ui.ui_collapsible_visibility_ghost_tools import create_visibility_ghost_section
    visibility_ghost_section = create_visibility_ghost_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(visibility_ghost_section, "visibility_ghost_section")

    # Smart Actions
    from ui.ui_collapsible_smart_tools import create_smart_section
    smart_section = create_smart_section(log_success, log_error, refresh_tree)
    grip_container.add_widget(smart_section, "smart_section")

    # Autopo Tools
    from ui.ui_collapsible_autopo_tools import create_autopo_section
    autopo_section = create_autopo_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(autopo_section, "autopo_section")

    # Dynamic Subdiv Tools
    from ui.ui_collapsible_subdiv_tools import create_subdiv_section
    subdiv_section = create_subdiv_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(subdiv_section, "subdiv_section")

    # Layers Tools
    from ui.ui_collapsible_layers_tools import create_layers_section
    layers_section = create_layers_section(
        log_success, log_error, refresh_tree)
    grip_container.add_widget(layers_section, "layers_section")

    # Add stretch at bottom
    layout.addStretch()

    return tab.widget


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_tools_tab(*args, **kwargs) -> None:  # type: ignore
        return None
