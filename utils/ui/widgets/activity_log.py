"""
ActivityLog widget - A scrollable activity log with timestamped, colored messages.

Messages are appended with timestamps and color-coded by level.
Supports info, warn, error, debug, and success levels.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTextEdit,
    )
    from PySide6.QtGui import QTextCursor

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as QWidgetType


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

# Default text edit styling
DEFAULT_LOG_STYLE: str = """
    QTextEdit {
        background: #1e1e1e;
        color: #d4d4d4;
        border: 1px solid #333;
        border-radius: 3px;
        font-family: Consolas, monospace;
        font-size: 9pt;
        padding: 4px;
    }
"""


if HAS_QT:

    class ActivityLog(QWidget):
        """
        A scrollable activity log with timestamped, colored messages.

        Messages are appended with timestamps and color-coded by level.
        Supports info, warn, error, debug, and success levels.

        Args:
            parent: Parent widget
            max_lines: Maximum number of lines to keep (0 = unlimited)
            show_timestamps: Whether to show timestamps
            min_height: Minimum height of the log widget
            max_height: Maximum height of the log widget

        Example:
            log = ActivityLog(parent)
            log.log_info("Operation started")
            log.log_success("Operation complete")
            log.log_error("Something failed")
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            max_lines: int = 200,
            show_timestamps: bool = True,
            min_height: int = 100,
            max_height: int = 150,
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
            self._text.setStyleSheet(DEFAULT_LOG_STYLE)
            self._text.setMinimumHeight(min_height)
            self._text.setMaximumHeight(max_height)
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

        def get_text(self) -> str:
            """Get all log text as plain text."""
            return self._text.toPlainText()

        def get_html(self) -> str:
            """Get all log text as HTML."""
            return self._text.toHtml()

        def set_max_lines(self, max_lines: int) -> None:
            """Set maximum number of lines to keep."""
            self._max_lines = max_lines

        def set_show_timestamps(self, show: bool) -> None:
            """Set whether to show timestamps."""
            self._show_timestamps = show

        def get_log_callback(self) -> Callable[[str], None]:
            """Get a callback function for use with other modules."""
            return self.log_info

else:
    # Stub class when PySide6 is not available
    class ActivityLog:  # type: ignore[no-redef]
        """Stub ActivityLog for when Qt is not available."""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def log_info(self, message: str) -> None:
            print(f"[INFO] {message}")

        def log_warn(self, message: str) -> None:
            print(f"[WARN] {message}")

        def log_error(self, message: str) -> None:
            print(f"[ERROR] {message}")

        def log_debug(self, message: str) -> None:
            print(f"[DEBUG] {message}")

        def log_success(self, message: str) -> None:
            print(f"[SUCCESS] {message}")

        def log(self, message: str, level: str = "info") -> None:
            print(f"[{level.upper()}] {message}")

        def clear(self) -> None:
            pass

        def get_text(self) -> str:
            return ""

        def get_html(self) -> str:
            return ""

        def set_max_lines(self, max_lines: int) -> None:
            pass

        def set_show_timestamps(self, show: bool) -> None:
            pass

        def get_log_callback(self) -> Callable[[str], None]:
            return print
