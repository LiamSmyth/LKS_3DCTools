"""
LKS UI - Dev Tab.

Provides development tools:
- Module hot-reload
- Extension info

Usage:
    from ui.ui_tab_dev import create_dev_tab
    tab = create_dev_tab(log_success, log_error, log_info, log_warn)
    tabs.add_tab("Dev", tab)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def create_dev_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
) -> "QWidget":
    """
    Create the development tools tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages

    Returns:
        QWidget containing dev tools
    """
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    from utils.ui.widgets import CollapsibleSection, ButtonGrid

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(4)

    # =========================================================================
    # DEV MODE TOGGLE
    # =========================================================================
    from PySide6.QtWidgets import QCheckBox

    dev_mode_cb = QCheckBox("🔧 Dev Mode (reload modules before every action)")
    dev_mode_cb.setToolTip(
        "When enabled, action scripts reload all LKS modules before executing.\n"
        "Useful for development but adds ~1s delay to radial menu invocation.\n"
        "Disable for production use / fast radial menus."
    )
    dev_mode_cb.setStyleSheet("""
        QCheckBox {
            color: #ddd;
            font-size: 11px;
            padding: 4px 2px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
        }
    """)

    # Load current state
    try:
        from utils.lks_settings import get_settings
        dev_mode_cb.setChecked(get_settings().dev_mode)
    except Exception:
        dev_mode_cb.setChecked(True)

    def on_dev_mode_toggled(checked: bool) -> None:
        try:
            from utils.lks_settings import get_settings, save_settings
            get_settings().dev_mode = checked
            save_settings()
            state_str: str = "ON" if checked else "OFF"
            log_info(f"Dev mode {state_str}")
        except Exception as e:
            log_error(f"Failed to save dev_mode: {e}")

    dev_mode_cb.toggled.connect(on_dev_mode_toggled)
    layout.addWidget(dev_mode_cb)

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

    # --- Revert to Defaults Button ---
    from PySide6.QtWidgets import QPushButton
    revert_btn = QPushButton("⟲ Revert UI State to Defaults")
    revert_btn.setStyleSheet("""
        QPushButton {
            background-color: #3a3a3a;
            color: #ddd;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
            border-color: #90caf9;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
    """)
    revert_btn.setToolTip(
        "Reset all collapsible section states to their defaults")

    def on_revert() -> None:
        try:
            from utils.lks_settings import reset_ui_state
            reset_ui_state()
            log_success(
                "UI state reverted to defaults. Restart panel to apply.")
        except Exception as e:
            log_error(f"Failed to revert UI state: {e}")

    revert_btn.clicked.connect(on_revert)
    layout.addWidget(revert_btn)

    layout.addStretch()

    return container
