"""
LKS UI - Extension Tab.

Provides extension management controls:
- Reload all LKS modules
- Register/unregister actions from menu
- Clean up stale menu entries

Usage:
    from ui.ui_tab_extension import create_extension_tab
    tab = create_extension_tab(log_success, log_error)
    tabs.add_tab("Extension", tab)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def create_extension_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
) -> "QWidget":
    """
    Create the extension management tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages

    Returns:
        QWidget containing extension controls
    """
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from ui.ui_widget_sub_header import create_sub_header

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(4)

    # =========================================================================
    # MODULE RELOAD SECTION
    # =========================================================================
    reload_section = CollapsibleSection(
        title="🔄 Module Reload", color="#64b5f6", collapsed=False)

    def on_reload_all() -> None:
        try:
            from utils.hot_reload import reload_all
            reloaded, failed = reload_all()
            log_success(f"Reloaded {reloaded} modules, {failed} failed")
        except Exception as e:
            log_error(f"Reload failed: {e}")

    def on_reload_ui() -> None:
        try:
            from utils.hot_reload import reload_by_prefix
            reloaded, failed = reload_by_prefix("ui")
            log_success(f"Reloaded {reloaded} UI modules, {failed} failed")
        except Exception as e:
            log_error(f"UI reload failed: {e}")

    def on_reload_ops() -> None:
        try:
            from utils.hot_reload import reload_by_prefix
            reloaded, failed = reload_by_prefix("ops")
            log_success(f"Reloaded {reloaded} ops modules, {failed} failed")
        except Exception as e:
            log_error(f"Ops reload failed: {e}")

    reload_grid = ButtonGrid(columns=3)
    reload_grid.add_button("Reload All", on_reload_all,
                           "Reload all LKS modules")
    reload_grid.add_button("Reload UI", on_reload_ui, "Reload UI modules only")
    reload_grid.add_button("Reload Ops", on_reload_ops,
                           "Reload operator modules")
    reload_section.content_layout.addWidget(reload_grid)

    layout.addWidget(reload_section)

    # =========================================================================
    # MENU REGISTRATION SECTION
    # =========================================================================
    menu_section = CollapsibleSection(
        title="📋 Menu Registration", color="#81c784", collapsed=False)

    menu_section.content_layout.addWidget(create_sub_header("Actions"))

    def on_register_all() -> None:
        try:
            from utils.registration_utils import register_actions
            count = register_actions()
            log_success(f"Registered {count} actions to Scripts menu")
        except Exception as e:
            log_error(f"Registration failed: {e}")

    def on_show_registered() -> None:
        try:
            from utils.registration_utils import get_registered_actions
            actions = get_registered_actions()
            if actions:
                log_info(f"Registered: {len(actions)} actions")
                for action in actions[:5]:  # Show first 5
                    log_info(f"  • {action}")
                if len(actions) > 5:
                    log_info(f"  ... and {len(actions) - 5} more")
            else:
                log_info("No actions registered yet")
        except Exception as e:
            log_error(f"Failed to get registered actions: {e}")

    action_grid = ButtonGrid(columns=2)
    action_grid.add_button("Register All", on_register_all,
                           "Register all action scripts")
    action_grid.add_button(
        "Show Registered", on_show_registered, "Show registered actions")
    menu_section.content_layout.addWidget(action_grid)

    menu_section.content_layout.addWidget(create_sub_header("Cleanup"))

    def on_cleanup_menu() -> None:
        try:
            from utils.menu_cleanup import cleanup_lks_menu
            deleted, names = cleanup_lks_menu()
            if deleted > 0:
                log_warn(
                    f"Deleted {deleted} stale menu files. Restart 3DCoat.")
                for name in names[:3]:
                    log_info(f"  • {name}")
            else:
                log_info("No stale menu files found.")
        except Exception as e:
            log_error(f"Menu cleanup failed: {e}")

    def on_show_menu_status() -> None:
        try:
            from utils.menu_cleanup import get_menu_cleanup_status
            status = get_menu_cleanup_status()
            count = status.get("count", 0)
            if count > 0:
                log_info(f"Found {count} LKS menu files:")
                for name in status.get("files", [])[:5]:
                    log_info(f"  • {name}")
            else:
                log_info("No LKS menu files in ExtraMenuItems")
        except Exception as e:
            log_error(f"Failed to get menu status: {e}")

    cleanup_grid = ButtonGrid(columns=2)
    cleanup_grid.add_button(
        "Cleanup Menu", on_cleanup_menu, "Remove stale menu entries")
    cleanup_grid.add_button(
        "Show Status", on_show_menu_status, "Show menu file status")
    menu_section.content_layout.addWidget(cleanup_grid)

    layout.addWidget(menu_section)

    # =========================================================================
    # EXTENSION INFO SECTION
    # =========================================================================
    info_section = CollapsibleSection(
        title="ℹ️ Extension Info", color="#90a4ae", collapsed=True)

    def on_show_paths() -> None:
        try:
            from utils.coat_menu_utils import get_lks_root, get_actions_dir
            log_info(f"LKS Root: {get_lks_root()}")
            log_info(f"Actions: {get_actions_dir()}")
        except Exception as e:
            log_error(f"Failed to get paths: {e}")

    def on_show_modules() -> None:
        try:
            from utils.hot_reload import discover_lks_modules
            modules = discover_lks_modules()
            log_info(f"Loaded {len(modules)} LKS modules")
            for name, priority in modules[:5]:
                log_info(f"  [{priority}] {name}")
            if len(modules) > 5:
                log_info(f"  ... and {len(modules) - 5} more")
        except Exception as e:
            log_error(f"Failed to discover modules: {e}")

    def on_show_actions() -> None:
        try:
            from utils.action_discovery import discover_actions
            from utils.coat_menu_utils import get_actions_dir
            actions = discover_actions(get_actions_dir())
            log_info(f"Discovered {len(actions)} action scripts")
            for action in actions[:5]:
                log_info(f"  • {action.filename}")
            if len(actions) > 5:
                log_info(f"  ... and {len(actions) - 5} more")
        except Exception as e:
            log_error(f"Failed to discover actions: {e}")

    info_grid = ButtonGrid(columns=3)
    info_grid.add_button("Paths", on_show_paths, "Show LKS paths")
    info_grid.add_button("Modules", on_show_modules, "Show loaded modules")
    info_grid.add_button("Actions", on_show_actions, "Show discovered actions")
    info_section.content_layout.addWidget(info_grid)

    layout.addWidget(info_section)

    layout.addStretch()

    return container
