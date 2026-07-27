"""
LKS UI - Hotkey Tab.

Provides hotkey editor controls:
- Launch hotkey editor (closes 3DCoat)

Usage:
    from ui.ui_tab_hotkey import create_hotkey_tab
    tab = create_hotkey_tab(log_success, log_error, log_info, log_warn)
    tabs.add_tab("Hotkey", tab)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


def create_hotkey_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    *,
    parent: "QWidget | None" = None,
) -> "QWidget":
    """
    Create the hotkey editor tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages
        parent: Parent panel window for embedding dialogs.

    Returns:
        QWidget containing hotkey editor controls
    """
    from utils.ui.widgets import (
        CollapsibleSection, ButtonGrid,
    )
    from utils.ui.widgets.tab_container import StandardTabBody

    body = StandardTabBody(
        title="Hotkey Editor",
        info_tooltip=_load_ui_tooltip("hotkey_tab.md"),
    )

    # =========================================================================
    # HOTKEY EDITOR SECTION
    # =========================================================================
    editor_section = CollapsibleSection(
        title="Hotkey Editor", color="#ce93d8", collapsed=False, icon_name="settings",
        help_text=_load_ui_tooltip("hotkey_editor_help.md"),
    )

    def on_launch_hotkey_editor() -> None:
        """Launch hotkey editor standalone and close 3DCoat."""
        try:
            from PySide6.QtCore import QTimer

            # Use embedded dialog so it stays on top of the pinned panel
            if parent is not None:
                from lks_utils.gui_qt.widgets.embedded_dialog import (
                    QEmbeddedDialog,
                    DialogButton,
                    BUTTONS_YES_NO,
                )

                dialog = QEmbeddedDialog(
                    parent=parent,
                    title="Launch Hotkey Editor",
                    message=(
                        "⚠️ Launching the Hotkey Editor will close 3DCoat.<br><br>"
                        "This is necessary because 3DCoat saves its in-memory "
                        "hotkey state on exit, which would overwrite any edits "
                        "made while it's running.<br><br>"
                        "The editor will open as a standalone application "
                        "after 3DCoat closes.<br><br>"
                        "Continue?"
                    ),
                    buttons=BUTTONS_YES_NO,
                )
                result: DialogButton | None = dialog.exec_()

                if result != DialogButton.YES:
                    log_info("Hotkey Editor launch cancelled")
                    return
            else:
                # Fallback for standalone usage without a parent
                from PySide6.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    None,
                    "Launch Hotkey Editor",
                    "⚠️ Launching the Hotkey Editor will close 3DCoat.\n\n"
                    "This is necessary because 3DCoat saves its in-memory hotkey state "
                    "on exit, which would overwrite any edits made while it's running.\n\n"
                    "The editor will open as a standalone application after 3DCoat closes.\n\n"
                    "Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply != QMessageBox.StandardButton.Yes:
                    log_info("Hotkey Editor launch cancelled")
                    return

            # Defer the launch so we exit the dialog's nested event loop
            # before starting the subprocess.
            QTimer.singleShot(0, lambda: _do_launch_hotkey_editor(log_success, log_error, log_info))

        except Exception as e:
            log_error(f"Failed to launch Hotkey Editor: {e}")
            import traceback
            log_error(traceback.format_exc())


    def _do_launch_hotkey_editor(
        log_success: Callable[[str], None],
        log_error: Callable[[str], None],
        log_info: Callable[[str], None],
    ) -> None:
        """Actual subprocess launch + coat quit, deferred via QTimer."""
        try:
            import coat
            from pathlib import Path
            import shutil
            import subprocess
            import sys

            # Find Python executable in system PATH
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

            DETACHED_PROCESS = 0x00000008

            # Use cmd /c start to launch a truly independent process.
            # DETACHED_PROCESS alone only disconnects the console — the
            # child can still be terminated when 3DCoat's process exits.
            # cmd /c start creates a new process tree that survives the
            # parent's termination.
            subprocess.Popen(
                [
                    "cmd", "/c", "start", "",
                    str(python_exe), str(editor_path),
                ],
                creationflags=DETACHED_PROCESS,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            log_success("Closing 3DCoat...")

            # Close 3DCoat
            coat.utils.quit()

        except Exception as e:
            log_error(f"Failed to launch Hotkey Editor: {e}")
            import traceback
            log_error(traceback.format_exc())

    editor_grid = ButtonGrid(columns=1)
    editor_grid.add_button(
        "Launch Hotkey Editor (Closes 3DCoat)",
        on_launch_hotkey_editor,
        "Launch standalone editor and close 3DCoat to prevent file overwrite"
    )
    editor_section.content_layout.addWidget(editor_grid)

    body.content_layout.addWidget(editor_section)

    return body
