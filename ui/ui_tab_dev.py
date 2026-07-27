"""
LKS UI - Dev Tab.

Provides development tools:
- Dev mode toggle (hot-reload every action)
- Module hot-reload (all / UI / ops)
- Extension info (paths, modules, actions)

Usage:
    from ui.ui_tab_dev import create_dev_tab
    body = create_dev_tab(log_success, log_error, log_info, log_warn)
    tabs.add_tab("Dev", body)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


def create_dev_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    panel: "QWidget | None" = None,
) -> "QWidget":
    """
    Create the development tools tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages
        panel: The LKSMainPanel instance for panel-level operations (restart, etc.)

    Returns:
        QWidget (StandardTabBody) containing dev tools
    """
    from PySide6.QtWidgets import QCheckBox, QSizePolicy

    from utils.ui.widgets.tab_container import StandardTabBody

    from utils.ui.widgets import CollapsibleSection, ButtonGrid

    body = StandardTabBody(
        title="Dev",
        info_tooltip=_load_ui_tooltip("dev_tab.md"),
    )
    layout = body.content_layout

    # =========================================================================
    # DEV MODE TOGGLE
    # =========================================================================
    dev_mode_cb = QCheckBox("Dev Mode (reload modules before every action)")
    # Short native tip; tab info button + Module Reload help cover detail.
    dev_mode_cb.setToolTip(
        "Reload all LKS modules before each action (~1s). Disable for production."
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
        title="Module Reload",
        color="#64b5f6",
        collapsed=False,
        icon_name="refresh",
        help_text=_load_ui_tooltip("dev_module_reload_help.md"),
    )

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

    # --- Restart Panel (full reload + UI rebuild) ---
    def on_restart_panel() -> None:
        try:
            from utils.hot_reload import full_restart_panel
            log_info("Full hot-restart: clearing all caches, closing panel, "
                     "re-registering actions, and opening fresh panel...")
            ok: bool = full_restart_panel(log_callback=log_info)
            if ok:
                log_success("Panel restarted with updated code")
            else:
                log_warn("Panel restart completed with errors — check log for details")
        except Exception as e:
            log_error(f"Panel restart failed: {e}")

    restart_grid = ButtonGrid(columns=1)
    restart_grid.add_button(
        "Restart Panel",
        on_restart_panel,
        "Full hot-restart: clears __pycache__, closes the panel, "
        "removes ALL LKS modules from sys.modules (filesystem-based "
        "discovery), re-registers action scripts, and opens a fresh "
        "panel from the reloaded code.\n"
        "Use this after editing any Python files in the LKS addon.\n\n"
        "Note: the cExtension C++ registration and menu XML files "
        "cannot be fully reset without restarting 3DCoat, but "
        "everything else is reloaded from disk.",
    )
    reload_section.content_layout.addWidget(restart_grid)

    layout.addWidget(reload_section)

    # =========================================================================
    # EXTENSION INFO SECTION
    # =========================================================================
    info_section = CollapsibleSection(
        title="Extension Info", color="#90a4ae", collapsed=True, icon_name="info")

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
            for name in modules[:5]:
                log_info(f"  • {name}")
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

    return body
