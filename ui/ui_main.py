"""
LKS UI - Main Panel.

Main panel window with header, tabs, footer, and activity log.
This is the top-level UI container that loads tab modules.

Usage:
    from ui.ui_main import LKSMainPanel
    panel = LKSMainPanel()
    panel.show()
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Qt

from utils.ui.styles import DARK_STYLESHEET
from utils.ui.widgets import TabWidget, ActivityLog


# =============================================================================
# MAIN PANEL CLASS
# =============================================================================

class LKSMainPanel(QWidget):
    """Main LKS Tools panel with tabbed interface."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LKS Tools")
        self.setMinimumSize(320, 500)
        self.resize(350, 600)
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet(DARK_STYLESHEET)

        # Position window in top-left area of screen
        self.move(100, 100)

        self._refresh_tree: Callable[[], None] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Header ---
        header = self._create_header()
        layout.addWidget(header)

        # --- Activity Log (create early - tabs need log callbacks) ---
        self._log = ActivityLog(max_lines=50)
        self._log.setMinimumHeight(80)
        self._log.setMaximumHeight(120)

        # --- Tabs (needs self._log for callbacks) ---
        self._tabs = TabWidget()
        self._load_tabs()
        layout.addWidget(self._tabs, 1)  # Stretch

        # --- Add Activity Log to layout ---
        layout.addWidget(self._log)

        # --- Footer Buttons ---
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create header with title and status."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("LKS Tools")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #90caf9;")
        layout.addWidget(title)

        layout.addStretch()

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._status_label)

        return container

    def _create_footer(self) -> QWidget:
        """Create footer with action buttons."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        btn_clear = QPushButton("Clear Log")
        btn_clear.setToolTip("Clear activity log")
        btn_clear.clicked.connect(self._log.clear)
        layout.addWidget(btn_clear)

        layout.addStretch()

        btn_close = QPushButton("X")
        btn_close.setFixedWidth(30)
        btn_close.setToolTip("Close panel")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        return container

    def _load_tabs(self) -> None:
        """Load tab modules."""
        # Outliner Tab
        from ui.ui_tab_outliner import create_outliner_tab
        outliner_tab, refresh_fn = create_outliner_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
        )
        self._tabs.add_tab("Outliner", outliner_tab)
        self._refresh_tree = refresh_fn

        # Tools Tab
        from ui.ui_tab_tools import create_tools_tab
        tools_tab = create_tools_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
            refresh_tree=self._do_refresh_tree,
        )
        self._tabs.add_tab("Tools", tools_tab)

        # Radial Menu Tab (removed emoji)
        from ui.ui_tab_radial_menu import create_radial_menu_tab
        radial_tab = create_radial_menu_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
        )
        self._tabs.add_tab("Radial", radial_tab)

        # Hotkey Tab (new)
        from ui.ui_tab_hotkey import create_hotkey_tab
        hotkey_tab = create_hotkey_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
            log_info=self._log.log_info,
            log_warn=self._log.log_warn,
        )
        self._tabs.add_tab("Hotkey", hotkey_tab)

        # Dev Tab (new - combines module reload and menu registration)
        from ui.ui_tab_dev import create_dev_tab
        dev_tab = create_dev_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
            log_info=self._log.log_info,
            log_warn=self._log.log_warn,
        )
        self._tabs.add_tab("Dev", dev_tab)

        # Extension Tab (legacy - kept for backwards compatibility)
        from ui.ui_tab_extension import create_extension_tab
        ext_tab = create_extension_tab(
            log_success=self._log.log_success,
            log_error=self._log.log_error,
            log_info=self._log.log_info,
            log_warn=self._log.log_warn,
        )
        # Commenting out for now - content moved to Dev and Hotkey tabs
        # self._tabs.add_tab("Extension", ext_tab)

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def _do_refresh_tree(self) -> None:
        """Refresh the outliner tree."""
        if self._refresh_tree:
            self._refresh_tree()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def log_info(self, text: str) -> None:
        """Log info message."""
        self._log.log_info(text)

    def log_success(self, text: str) -> None:
        """Log success message."""
        self._log.log_success(text)

    def log_error(self, text: str) -> None:
        """Log error message."""
        self._log.log_error(text)

    def log_warn(self, text: str) -> None:
        """Log warning message."""
        self._log.log_warn(text)

    def refresh_tree(self) -> None:
        """Public method to refresh the outliner tree."""
        self._do_refresh_tree()
