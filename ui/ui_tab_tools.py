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
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# HELP TEXT
# =============================================================================

def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


# =============================================================================
# TOOLS TAB FACTORY
# =============================================================================

def create_tools_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create the tools tab containing collapsible tool sections.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree
        log_info: Callback for info/progress messages

    Returns:
        QWidget containing all tool sections
    """
    from utils.ui.widgets.tab_container import StandardTabBody

    body = StandardTabBody(
        title="Tools",
        info_tooltip=_load_ui_tooltip("tools_tab.md"),
    )
    layout = body.content_layout

    # --- Reorderable Sections in GripBoxContainer ---
    from utils.ui.widgets import GripBoxContainer
    grip_container = GripBoxContainer()
    layout.addWidget(grip_container)

    # --- Load Collapsible Sections ---

    # Decimate Tools
    from ui.ui_collapsible_decimate_tools import create_decimate_section
    decimate_section = create_decimate_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(decimate_section, "decimate_section")

    # Proxy/Cache Tools
    from ui.ui_collapsible_proxy_tools import create_proxy_section
    proxy_section = create_proxy_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(proxy_section, "proxy_section")

    # Resample Tools
    from ui.ui_collapsible_resample_tools import create_resample_section
    resample_section = create_resample_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(resample_section, "resample_section")

    # Mode Conversion Tools
    from ui.ui_collapsible_mode_tools import create_mode_section
    mode_section = create_mode_section(log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(mode_section, "mode_section")

    # Boolean Tools (Create / Set Mode / Apply)
    from ui.ui_collapsible_boolean_tools import create_boolean_section
    boolean_section = create_boolean_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(boolean_section, "boolean_section")

    # Scale Tools
    from ui.ui_collapsible_scale_tools import create_scale_section
    scale_section = create_scale_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(scale_section, "scale_section")

    # Visibility & Ghost Tools (merged)
    from ui.ui_collapsible_visibility_ghost_tools import create_visibility_ghost_section
    visibility_ghost_section = create_visibility_ghost_section(
        log_success, log_error, refresh_tree, log_info=log_info)
    grip_container.add_widget(visibility_ghost_section,
                              "visibility_ghost_section")

    # Smart Actions
    from ui.ui_collapsible_smart_tools import create_smart_section
    smart_section = create_smart_section(
        log_success, log_error, refresh_tree, log_info=log_info)
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

    return body


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_tools_tab(*args, **kwargs) -> None:  # type: ignore
        return None
