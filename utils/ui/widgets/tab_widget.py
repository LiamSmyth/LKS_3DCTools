"""
TabWidget - A styled tab widget for organizing content into tabs.

Provides dark theme styling matching LKS panel aesthetics.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTabWidget,
        QScrollArea,
    )
    from PySide6.QtCore import Signal

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as QWidgetType


# Default tab widget styling for dark theme
DEFAULT_TAB_STYLE: str = """
    QTabWidget::pane {
        border: 1px solid #444;
        background: #2d2d2d;
    }
    QTabBar::tab {
        background: #353535;
        border: 1px solid #444;
        border-bottom: none;
        padding: 6px 12px;
        margin-right: 2px;
        color: #bbb;
        font-size: 11px;
    }
    QTabBar::tab:selected {
        background: #2d2d2d;
        color: #90caf9;
        border-bottom: 2px solid #90caf9;
    }
    QTabBar::tab:hover {
        background: #404040;
        color: #fff;
    }
"""


if HAS_QT:

    class TabWidget(QWidget):
        """
        A styled tab widget for organizing content into tabs.

        Features:
        - Dark theme styling matching LKS panel
        - Tab bar with horizontal tabs
        - Emoji support in tab labels
        - Scroll area in each tab content

        Args:
            parent: Parent widget

        Signals:
            tab_changed(int): Emitted when current tab changes

        Example:
            tabs = TabWidget(parent)
            layout1 = tabs.add_scrollable_tab("📋 General")
            layout1.addWidget(QLabel("General settings here"))

            layout2 = tabs.add_scrollable_tab("⚙️ Advanced")
            layout2.addWidget(QLabel("Advanced settings here"))
        """

        tab_changed = Signal(int)

        def __init__(
            self,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create tab widget with dark styling
            self._tab_widget = QTabWidget()
            self._tab_widget.setStyleSheet(DEFAULT_TAB_STYLE)
            self._tab_widget.currentChanged.connect(self._on_tab_changed)
            layout.addWidget(self._tab_widget)

        def add_tab(self, label: str, widget: QWidget) -> int:
            """
            Add a tab with the given label and content widget.

            Args:
                label: Tab label text (emojis supported)
                widget: Content widget for the tab

            Returns:
                Index of the new tab
            """
            return self._tab_widget.addTab(widget, label)

        def add_scrollable_tab(self, label: str) -> QVBoxLayout:
            """
            Add a tab with scrollable content area.

            Args:
                label: Tab label text (emojis supported)

            Returns:
                Layout to add content widgets to
            """
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(
                "QScrollArea { border: none; background: transparent; }"
            )

            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(4, 4, 4, 4)
            content_layout.setSpacing(4)

            scroll.setWidget(content)
            self._tab_widget.addTab(scroll, label)

            return content_layout

        def insert_tab(self, index: int, label: str, widget: QWidget) -> int:
            """
            Insert a tab at the specified index.

            Args:
                index: Position to insert the tab
                label: Tab label text
                widget: Content widget for the tab

            Returns:
                Index of the new tab
            """
            return self._tab_widget.insertTab(index, widget, label)

        def remove_tab(self, index: int) -> None:
            """Remove a tab by index."""
            self._tab_widget.removeTab(index)

        def current_index(self) -> int:
            """Get current tab index."""
            return self._tab_widget.currentIndex()

        def set_current_index(self, index: int) -> None:
            """Set current tab by index."""
            self._tab_widget.setCurrentIndex(index)

        def tab_count(self) -> int:
            """Get number of tabs."""
            return self._tab_widget.count()

        def set_tab_text(self, index: int, text: str) -> None:
            """Set the text for a tab."""
            self._tab_widget.setTabText(index, text)

        def tab_text(self, index: int) -> str:
            """Get the text of a tab."""
            return self._tab_widget.tabText(index)

        def set_tab_enabled(self, index: int, enabled: bool) -> None:
            """Enable or disable a tab."""
            self._tab_widget.setTabEnabled(index, enabled)

        def is_tab_enabled(self, index: int) -> bool:
            """Check if a tab is enabled."""
            return self._tab_widget.isTabEnabled(index)

        def widget(self, index: int) -> QWidget | None:
            """Get the widget at the specified tab index."""
            return self._tab_widget.widget(index)

        def _on_tab_changed(self, index: int) -> None:
            """Handle tab change."""
            self.tab_changed.emit(index)

else:
    # Stub class when PySide6 is not available
    class TabWidget:  # type: ignore[no-redef]
        """Stub TabWidget for when Qt is not available."""

        tab_changed = None

        def __init__(self, *args, **kwargs) -> None:
            pass

        def add_tab(self, label: str, widget) -> int:
            return 0

        def add_scrollable_tab(self, label: str):
            return None

        def insert_tab(self, index: int, label: str, widget) -> int:
            return 0

        def remove_tab(self, index: int) -> None:
            pass

        def current_index(self) -> int:
            return 0

        def set_current_index(self, index: int) -> None:
            pass

        def tab_count(self) -> int:
            return 0

        def set_tab_text(self, index: int, text: str) -> None:
            pass

        def tab_text(self, index: int) -> str:
            return ""

        def set_tab_enabled(self, index: int, enabled: bool) -> None:
            pass

        def is_tab_enabled(self, index: int) -> bool:
            return True

        def widget(self, index: int):
            return None
