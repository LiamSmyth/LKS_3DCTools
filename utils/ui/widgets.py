"""
LKS UI Widgets - Reusable PySide6/Qt components for LKS panels.

This module provides reusable widget primitives for building LKS UI:
- CollapsibleSection: Expandable/collapsible group with header
- ButtonGrid: Grid of buttons with scope-based layout
- ActivityLog: Scrollable log display with timestamped messages
- LabeledSlider: Slider with label and value display
- SectionHeader: Styled section header label

Usage:
    from ui.widgets import CollapsibleSection, ButtonGrid, ActivityLog

    log = ActivityLog(parent)
    log.log_info("Operation complete")
    log.log_error("Something failed")
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QPushButton, QFrame, QTextEdit, QSlider,
        QSizePolicy, QToolTip,
    )
    from PySide6.QtCore import Qt, Signal, QTimer, QPoint
    from PySide6.QtGui import QColor, QTextCursor, QFont

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Log level colors (Qt color names or hex)
LOG_COLORS: dict[str, str] = {
    "info": "#81c784",      # Green
    "warn": "#ffb74d",      # Orange
    "error": "#ef5350",     # Red
    "debug": "#90caf9",     # Blue
    "success": "#4caf50",   # Bright green
}

# Log level prefixes
LOG_PREFIXES: dict[str, str] = {
    "info": "",
    "warn": "⚠ ",
    "error": "✗ ",
    "debug": "[debug] ",
    "success": "✓ ",
}


if HAS_QT:

    # =========================================================================
    # COLLAPSIBLE SECTION
    # =========================================================================

    class CollapsibleSection(QWidget):
        """
        A collapsible section with a clickable header.

        The content area can be expanded/collapsed by clicking the header.
        An optional enable checkbox can control whether the section's actions
        are active.

        Signals:
            toggled(bool): Emitted when collapsed state changes (True = collapsed)
            enabled_changed(bool): Emitted when checkbox state changes

        Args:
            parent: Parent widget
            title: Section header text
            collapsed: Initial collapsed state
            checkable: Whether to show enable checkbox
            checked: Initial checkbox state (if checkable)
            color: Header text color (hex or Qt color name)
        """

        toggled = Signal(bool)
        enabled_changed = Signal(bool)

        def __init__(
            self,
            parent: QWidget | None = None,
            title: str = "Section",
            collapsed: bool = False,
            checkable: bool = False,
            checked: bool = True,
            color: str = "#ffb74d",
        ) -> None:
            super().__init__(parent)
            self._collapsed: bool = collapsed
            self._checkable: bool = checkable
            self._checked: bool = checked
            self._color: str = color

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)

            # Header frame
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(4)

            # Toggle button with arrow indicator
            self._toggle_btn = QPushButton("▼" if not collapsed else "▶")
            self._toggle_btn.setFixedSize(20, 20)
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #888;
                    font-size: 10px;
                }
                QPushButton:hover { color: #fff; }
            """)
            self._toggle_btn.clicked.connect(self._on_toggle)
            header_layout.addWidget(self._toggle_btn)

            # Optional checkbox
            if checkable:
                from PySide6.QtWidgets import QCheckBox
                self._checkbox = QCheckBox()
                self._checkbox.setChecked(checked)
                self._checkbox.stateChanged.connect(self._on_checkbox_changed)
                header_layout.addWidget(self._checkbox)

            # Title label (clickable)
            self._title_label = QLabel(title)
            self._title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 11px;
                    color: {color};
                }}
                QLabel:hover {{ color: #fff; }}
            """)
            self._title_label.setCursor(Qt.PointingHandCursor)
            self._title_label.mousePressEvent = lambda e: self._on_toggle()
            header_layout.addWidget(self._title_label)
            header_layout.addStretch()

            layout.addWidget(header_frame)

            # Content frame (holds user widgets) with left border for visual hierarchy
            self._content_frame = QFrame()
            self._content_frame.setStyleSheet(f"""
                QFrame {{
                    border-left: 2px solid {color};
                    margin-left: 8px;
                }}
            """)
            self._content_layout = QVBoxLayout(self._content_frame)
            self._content_layout.setContentsMargins(12, 4, 0, 4)
            self._content_layout.setSpacing(4)
            layout.addWidget(self._content_frame)

            # Apply initial state
            self._content_frame.setVisible(not collapsed)

        @property
        def content(self) -> QFrame:
            """Get the content frame to add widgets to."""
            return self._content_frame

        @property
        def content_layout(self) -> QVBoxLayout:
            """Get the content layout for adding widgets."""
            return self._content_layout

        def is_collapsed(self) -> bool:
            """Return True if section is collapsed."""
            return self._collapsed

        def is_expanded(self) -> bool:
            """Return True if section is expanded."""
            return not self._collapsed

        def is_enabled(self) -> bool:
            """Return checkbox state (True if not checkable)."""
            if self._checkable:
                return self._checked
            return True

        def expand(self) -> None:
            """Expand the section."""
            if self._collapsed:
                self._collapsed = False
                self._toggle_btn.setText("▼")
                self._content_frame.setVisible(True)
                self.toggled.emit(False)

        def collapse(self) -> None:
            """Collapse the section."""
            if not self._collapsed:
                self._collapsed = True
                self._toggle_btn.setText("▶")
                self._content_frame.setVisible(False)
                self.toggled.emit(True)

        def set_enabled(self, enabled: bool) -> None:
            """Set checkbox state (if checkable)."""
            if self._checkable:
                self._checked = enabled
                self._checkbox.setChecked(enabled)

        def _on_toggle(self) -> None:
            """Handle toggle button/label click."""
            if self._collapsed:
                self.expand()
            else:
                self.collapse()

        def _on_checkbox_changed(self, state: int) -> None:
            """Handle checkbox state change."""
            self._checked = state == Qt.Checked
            self.enabled_changed.emit(self._checked)

    # =========================================================================
    # BUTTON GRID
    # =========================================================================

    class ButtonGrid(QWidget):
        """
        A grid of buttons with consistent styling.

        Useful for scope-based operations (Current, Subtree, All).

        Args:
            parent: Parent widget
            columns: Number of columns in the grid
            button_style: CSS style for buttons

        Usage:
            grid = ButtonGrid(parent, columns=3)
            grid.add_button("Current", self._on_current)
            grid.add_button("Subtree", self._on_subtree)
            grid.add_button("All", self._on_all)
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            columns: int = 3,
            button_style: str | None = None,
        ) -> None:
            super().__init__(parent)
            self._columns: int = columns
            self._button_style: str = button_style or """
                QPushButton {
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 4px 8px;
                    color: #ddd;
                    min-height: 20px;
                }
                QPushButton:hover { background: #4a4a4a; border-color: #666; }
                QPushButton:pressed { background: #2a2a2a; }
            """
            self._row: int = 0
            self._col: int = 0
            self._buttons: list[QPushButton] = []

            self._layout = QGridLayout(self)
            self._layout.setContentsMargins(0, 0, 0, 0)
            self._layout.setSpacing(4)

        def add_button(
            self,
            text: str,
            callback: Callable[[], None],
            tooltip: str | None = None,
            style: str | None = None,
        ) -> QPushButton:
            """
            Add a button to the grid.

            Args:
                text: Button label
                callback: Click handler
                tooltip: Optional tooltip text
                style: Button style override

            Returns:
                The created button
            """
            btn = QPushButton(text)
            btn.setStyleSheet(style or self._button_style)
            btn.clicked.connect(callback)
            if tooltip:
                btn.setToolTip(tooltip)

            self._layout.addWidget(btn, self._row, self._col)
            self._buttons.append(btn)

            # Advance position
            self._col += 1
            if self._col >= self._columns:
                self._col = 0
                self._row += 1

            return btn

        def new_row(self) -> None:
            """Move to a new row."""
            if self._col > 0:
                self._row += 1
                self._col = 0

    # =========================================================================
    # ACTIVITY LOG
    # =========================================================================

    class ActivityLog(QWidget):
        """
        A scrollable activity log with timestamped, colored messages.

        Messages are appended with timestamps and color-coded by level.
        Supports info, warn, error, debug, and success levels.

        Args:
            parent: Parent widget
            max_lines: Maximum number of lines to keep (0 = unlimited)
            show_timestamps: Whether to show timestamps
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            max_lines: int = 200,
            show_timestamps: bool = True,
        ) -> None:
            super().__init__(parent)
            self._max_lines: int = max_lines
            self._show_timestamps: bool = show_timestamps
            self._line_count: int = 0

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            # Text widget
            self._text = QTextEdit()
            self._text.setReadOnly(True)
            self._text.setStyleSheet("""
                QTextEdit {
                    background: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #333;
                    border-radius: 3px;
                    font-family: Consolas, monospace;
                    font-size: 9pt;
                    padding: 4px;
                }
            """)
            self._text.setMinimumHeight(100)
            self._text.setMaximumHeight(150)
            layout.addWidget(self._text)

        def _format_timestamp(self) -> str:
            """Get current timestamp string."""
            return datetime.now().strftime("%H:%M:%S")

        def _append_line(self, text: str, level: str) -> None:
            """Append a line to the log with the specified level styling."""
            color = LOG_COLORS.get(level, "#d4d4d4")
            prefix = LOG_PREFIXES.get(level, "")

            # Build HTML line
            if self._show_timestamps:
                timestamp = f'<span style="color:#666;">[{self._format_timestamp()}]</span> '
            else:
                timestamp = ""

            html = f'{timestamp}<span style="color:{color};">{prefix}{text}</span><br>'
            self._text.insertHtml(html)

            # Trim old lines if needed
            self._line_count += 1
            if self._max_lines > 0 and self._line_count > self._max_lines:
                cursor = self._text.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                self._line_count -= 1

            # Scroll to end
            self._text.moveCursor(QTextCursor.End)

        def log_info(self, message: str) -> None:
            """Log an info message (green)."""
            self._append_line(message, "info")

        def log_warn(self, message: str) -> None:
            """Log a warning message (orange)."""
            self._append_line(message, "warn")

        def log_error(self, message: str) -> None:
            """Log an error message (red)."""
            self._append_line(message, "error")

        def log_debug(self, message: str) -> None:
            """Log a debug message (blue)."""
            self._append_line(message, "debug")

        def log_success(self, message: str) -> None:
            """Log a success message (bright green)."""
            self._append_line(message, "success")

        def log(self, message: str, level: str = "info") -> None:
            """
            Log a message with specified level.

            Args:
                message: The message to log
                level: One of "info", "warn", "error", "debug", "success"
            """
            method = getattr(self, f"log_{level}", self.log_info)
            method(message)

        def clear(self) -> None:
            """Clear all log messages."""
            self._text.clear()
            self._line_count = 0

        def get_log_callback(self) -> Callable[[str], None]:
            """Get a callback function for use with other modules."""
            return self.log_info

    # =========================================================================
    # LABELED SLIDER
    # =========================================================================

    class LabeledSlider(QWidget):
        """
        A horizontal slider with label and current value display.

        Args:
            parent: Parent widget
            label: Label text
            min_value: Minimum value
            max_value: Maximum value
            initial: Initial value
            suffix: Suffix for value display (e.g., "%")
        """

        value_changed = Signal(int)

        def __init__(
            self,
            parent: QWidget | None = None,
            label: str = "Value:",
            min_value: int = 0,
            max_value: int = 100,
            initial: int = 50,
            suffix: str = "",
        ) -> None:
            super().__init__(parent)
            self._suffix: str = suffix

            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            # Label
            self._label = QLabel(label)
            self._label.setMinimumWidth(70)
            layout.addWidget(self._label)

            # Slider
            self._slider = QSlider(Qt.Horizontal)
            self._slider.setMinimum(min_value)
            self._slider.setMaximum(max_value)
            self._slider.setValue(initial)
            self._slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #3a3a3a;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #90caf9;
                    width: 14px;
                    margin: -4px 0;
                    border-radius: 7px;
                }
                QSlider::handle:horizontal:hover {
                    background: #64b5f6;
                }
            """)
            self._slider.valueChanged.connect(self._on_value_changed)
            layout.addWidget(self._slider, 1)

            # Value display
            self._value_label = QLabel()
            self._value_label.setMinimumWidth(40)
            self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._update_value_display()
            layout.addWidget(self._value_label)

        def value(self) -> int:
            """Get current value."""
            return self._slider.value()

        def set_value(self, value: int) -> None:
            """Set current value."""
            self._slider.setValue(value)

        def _on_value_changed(self, value: int) -> None:
            """Handle slider value change."""
            self._update_value_display()
            self.value_changed.emit(value)

        def _update_value_display(self) -> None:
            """Update the value label."""
            self._value_label.setText(f"{self._slider.value()}{self._suffix}")

    # =========================================================================
    # SECTION HEADER
    # =========================================================================

    class SectionHeader(QLabel):
        """
        A styled section header label.

        Args:
            parent: Parent widget
            text: Header text
            sub: If True, use smaller sub-header style
            color: Text color (hex or Qt color name)
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            text: str = "",
            sub: bool = False,
            color: str = "#ffb74d",
        ) -> None:
            super().__init__(text, parent)
            font_size = "10px" if sub else "11px"
            sub_color = "#90caf9" if sub else color
            self.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: {font_size};
                    color: {sub_color};
                    padding: 2px 0;
                }}
            """)

    # =========================================================================
    # TAB WIDGET
    # =========================================================================

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
            tabs: List of (tab_label, content_widget) tuples
        """

        tab_changed = Signal(int)

        def __init__(
            self,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            from PySide6.QtWidgets import QTabWidget, QScrollArea

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create tab widget with dark styling
            self._tab_widget = QTabWidget()
            self._tab_widget.setStyleSheet("""
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
            """)
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
            from PySide6.QtWidgets import QScrollArea

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(
                "QScrollArea { border: none; background: transparent; }")

            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(4, 4, 4, 4)
            content_layout.setSpacing(4)

            scroll.setWidget(content)
            self._tab_widget.addTab(scroll, label)

            return content_layout

        def current_index(self) -> int:
            """Get current tab index."""
            return self._tab_widget.currentIndex()

        def set_current_index(self, index: int) -> None:
            """Set current tab by index."""
            self._tab_widget.setCurrentIndex(index)

        def tab_count(self) -> int:
            """Get number of tabs."""
            return self._tab_widget.count()

        def _on_tab_changed(self, index: int) -> None:
            """Handle tab change."""
            self.tab_changed.emit(index)

    # =========================================================================
    # TOOLTIP (utility for custom tooltips)
    # =========================================================================

    def add_tooltip(widget: QWidget, text: str) -> None:
        """Add a tooltip to a widget."""
        widget.setToolTip(text)

else:
    # Stub classes when PySide6 is not available
    class CollapsibleSection:  # type: ignore
        toggled = None
        enabled_changed = None
        def __init__(self, *args, **kwargs): pass
        @property
        def content(self): return None
        @property
        def content_layout(self): return None

    class ButtonGrid:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def add_button(self, *args, **kwargs): pass

    class ActivityLog:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def log_info(self, message: str) -> None: print(f"[INFO] {message}")
        def log_warn(self, message: str) -> None: print(f"[WARN] {message}")
        def log_error(self, message: str) -> None: print(f"[ERROR] {message}")
        def log_debug(self, message: str) -> None: print(f"[DEBUG] {message}")
        def log_success(
            self, message: str) -> None: print(f"[SUCCESS] {message}")

        def clear(self) -> None: pass
        def get_log_callback(self): return print

    class LabeledSlider:  # type: ignore
        value_changed = None
        def __init__(self, *args, **kwargs): pass
        def value(self) -> int: return 0
        def set_value(self, v): pass

    class SectionHeader:  # type: ignore
        def __init__(self, *args, **kwargs): pass

    class TabWidget:  # type: ignore
        tab_changed = None
        def __init__(self, *args, **kwargs): pass
        def add_tab(self, *args, **kwargs): return 0
        def add_scrollable_tab(self, *args, **kwargs): return None
        def current_index(self): return 0
        def set_current_index(self, index): pass
        def tab_count(self): return 0

    def add_tooltip(widget, text: str) -> None:
        pass
