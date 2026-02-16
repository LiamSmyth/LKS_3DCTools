"""
LKS UI - Hotkey Tab.

Provides hotkey editor controls with launch functionality.

Usage:
    from ui.ui_tab_hotkey import create_hotkey_tab
    tab = create_hotkey_tab(log_success, log_error, log_info, log_warn)
    tabs.add_tab("Hotkey", tab)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def create_hotkey_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
) -> "QWidget":
    """
    Create the hotkey editor tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages

    Returns:
        QWidget containing hotkey editor controls
    """
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    from utils.ui.widgets import CollapsibleSection, ButtonGrid

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(4)

    # =========================================================================
    # HOTKEY EDITOR SECTION
    # =========================================================================
    editor_section = CollapsibleSection(
        title="🔑 Hotkey Editor", color="#ce93d8", collapsed=False)

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

    editor_grid = ButtonGrid(columns=1)
    editor_grid.add_button(
        "Launch Hotkey Editor (Closes 3DCoat)",
        on_launch_hotkey_editor,
        "Launch standalone editor and close 3DCoat to prevent file overwrite"
    )
    editor_section.content_layout.addWidget(editor_grid)

    layout.addWidget(editor_section)

    # =========================================================================
    # INFO/HELP SECTION
    # =========================================================================
    info_section = CollapsibleSection(
        title="ℹ️ About Hotkeys", color="#90a4ae", collapsed=True)

    from PySide6.QtWidgets import QLabel
    info_text = QLabel(
        "<b>Why does 3DCoat close?</b><br/>"
        "3DCoat saves its in-memory hotkey configuration when it exits. "
        "If the editor modifies the hotkey file while 3DCoat is running, "
        "the changes would be overwritten on exit.<br/><br/>"
        "<b>Workflow:</b><br/>"
        "1. Launch the Hotkey Editor (3DCoat closes)<br/>"
        "2. Make your hotkey changes in the editor<br/>"
        "3. Save changes in the editor<br/>"
        "4. Close the editor<br/>"
        "5. Restart 3DCoat (changes will be loaded)"
    )
    info_text.setWordWrap(True)
    info_text.setStyleSheet("color: #aaa; font-size: 10px; padding: 8px;")
    info_section.content_layout.addWidget(info_text)

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
