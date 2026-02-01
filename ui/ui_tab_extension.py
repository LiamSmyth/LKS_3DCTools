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
    from utils.ui.widgets.sub_header import create_sub_header

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

    # =========================================================================
    # TOOLS SECTION
    # =========================================================================
    tools_section = CollapsibleSection(
        title="🔧 Tools", color="#ce93d8", collapsed=False)

    # Keep reference to editor window to prevent garbage collection
    def on_launch_hotkey_editor() -> None:
        """Launch hotkey editor standalone and close 3DCoat."""
        try:
            import coat
            from pathlib import Path
            import sys
            from PySide6.QtWidgets import QMessageBox

            # Confirmation dialog
            reply = QMessageBox.question(
                None,
                "Launch Hotkey Editor",
                "⚠️ Launching the Hotkey Editor will close 3DCoat.\n\n"
                "This is necessary because 3DCoat saves its in-memory hotkey state "
                "on exit, which would overwrite any edits made while it's running.\n\n"
                "The editor will open as a standalone application after 3DCoat closes.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                log_info("Hotkey Editor launch cancelled")
                return

            # Find Python executable in system PATH
            # 3DCoat uses system-installed Python, not an embedded interpreter
            import sys
            import shutil

            python_exe: Path | None = None
            pythonw_in_path: str | None = shutil.which("pythonw")
            python_in_path: str | None = shutil.which("python")

            # Prefer pythonw.exe (no console window)
            if pythonw_in_path:
                python_exe = Path(pythonw_in_path)
                log_info(f"Found Python: {python_exe}")
            elif python_in_path:
                python_exe = Path(python_in_path)
                log_info(f"Found Python: {python_exe}")
            else:
                log_error("Python executable not found in system PATH!")
                log_error("Please ensure Python is installed and added to PATH")
                return

            # Use run_standalone.py which handles imports correctly for detached mode
            editor_path: Path = Path(
                __file__).parent.parent / "utils" / "hotkey_editor" / "run_standalone.py"

            log_info("Launching Hotkey Editor as standalone process...")
            log_info(f"Python: {python_exe}")
            log_info(f"Editor: {editor_path}")

            # Launch editor as DETACHED process using subprocess
            # This ensures it survives when 3DCoat exits
            import subprocess

            # Windows-specific flags for detached process
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200

            subprocess.Popen(
                [str(python_exe), str(editor_path)],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for process to spawn
            log_info("Waiting for editor process to spawn...")
            coat.io.step(5)

            log_success("Closing 3DCoat...")

            # Close 3DCoat (quit is in utils namespace)
            coat.utils.quit()

        except Exception as e:
            log_error(f"Failed to launch Hotkey Editor: {e}")
            import traceback
            log_error(traceback.format_exc())

    tools_grid = ButtonGrid(columns=1)
    tools_grid.add_button(
        "🔑 Hotkey Editor (Closes 3DCoat)",
        on_launch_hotkey_editor,
        "Launch standalone editor and close 3DCoat to prevent file overwrite"
    )
    tools_section.content_layout.addWidget(tools_grid)

    layout.addWidget(tools_section)

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
