"""
ToolTip - A rich text tooltip with delayed display and custom styling.

Provides more control than Qt's default tooltips, including:
- Rich text/HTML support
- Multi-line tooltips
- Delayed display with configurable delay
- Custom styling for dark theme
- Position control
"""
from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import (
        QWidget,
        QLabel,
        QVBoxLayout,
        QGraphicsDropShadowEffect,
        QApplication,
    )
    from PySide6.QtCore import Qt, QTimer, QPoint
    from PySide6.QtGui import QColor, QCursor

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as QWidgetType


# Default tooltip styling for dark theme
DEFAULT_TOOLTIP_STYLE: str = """
    QLabel {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 11px;
    }
"""

# Default delay before showing tooltip (milliseconds)
DEFAULT_SHOW_DELAY: int = 500

# Default delay before hiding tooltip (milliseconds)
DEFAULT_HIDE_DELAY: int = 100


if HAS_QT:
    # Offset from cursor position
    CURSOR_OFFSET: QPoint = QPoint(16, 16)

    class ToolTip(QWidget):
        """
        A rich text tooltip with delayed display and custom styling.

        This tooltip provides more control than Qt's default tooltips:
        - Rich text/HTML support for formatted content
        - Multi-line tooltips with proper wrapping
        - Delayed display with configurable delay
        - Custom styling for dark theme integration
        - Position control relative to cursor

        Args:
            parent: Parent widget (tooltip will be displayed relative to this)
            text: Tooltip text (can be HTML/rich text)
            show_delay: Delay before showing tooltip in milliseconds
            hide_delay: Delay before hiding tooltip in milliseconds
            max_width: Maximum width of tooltip before wrapping
            style: Custom CSS style for the tooltip

        Example:
            # Simple usage
            tooltip = ToolTip(my_button, "Click to save")
            tooltip.attach(my_button)

            # Rich text tooltip
            tooltip = ToolTip(
                my_button,
                "<b>Save</b><br>Save the current document to disk.<br>"
                "<i>Shortcut: Ctrl+S</i>",
                show_delay=300,
                max_width=250
            )
            tooltip.attach(my_button)

            # Or use the convenience function
            add_tooltip(my_button, "Simple tooltip text")
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            text: str = "",
            show_delay: int = DEFAULT_SHOW_DELAY,
            hide_delay: int = DEFAULT_HIDE_DELAY,
            max_width: int = 300,
            style: str | None = None,
        ) -> None:
            # Create as a top-level window with no frame
            super().__init__(None, Qt.ToolTip | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)

            self._parent_widget: QWidget | None = parent
            self._show_delay: int = show_delay
            self._hide_delay: int = hide_delay
            self._max_width: int = max_width
            self._attached_widgets: list[QWidget] = []

            # Layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            # Label for tooltip content
            self._label = QLabel(text)
            self._label.setWordWrap(True)
            self._label.setMaximumWidth(max_width)
            self._label.setTextFormat(Qt.RichText)
            self._label.setStyleSheet(style or DEFAULT_TOOLTIP_STYLE)
            layout.addWidget(self._label)

            # Add drop shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setXOffset(2)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 100))
            self._label.setGraphicsEffect(shadow)

            # Timers for show/hide delay
            self._show_timer = QTimer()
            self._show_timer.setSingleShot(True)
            self._show_timer.timeout.connect(self._do_show)

            self._hide_timer = QTimer()
            self._hide_timer.setSingleShot(True)
            self._hide_timer.timeout.connect(self._do_hide)

            # Track cursor position for show
            self._show_position: QPoint | None = None

        def set_text(self, text: str) -> None:
            """Set the tooltip text (can be HTML/rich text)."""
            self._label.setText(text)
            self.adjustSize()

        def text(self) -> str:
            """Get the current tooltip text."""
            return self._label.text()

        def set_show_delay(self, delay: int) -> None:
            """Set the delay before showing tooltip (milliseconds)."""
            self._show_delay = delay

        def set_hide_delay(self, delay: int) -> None:
            """Set the delay before hiding tooltip (milliseconds)."""
            self._hide_delay = delay

        def set_max_width(self, width: int) -> None:
            """Set the maximum width of the tooltip."""
            self._max_width = width
            self._label.setMaximumWidth(width)
            self.adjustSize()

        def set_style(self, style: str) -> None:
            """Set custom CSS style for the tooltip."""
            self._label.setStyleSheet(style)

        def attach(self, widget: QWidget) -> None:
            """
            Attach the tooltip to a widget.

            This installs event filters to show/hide the tooltip on
            mouse enter/leave events.

            Args:
                widget: Widget to attach tooltip to
            """
            if widget not in self._attached_widgets:
                widget.installEventFilter(self)
                self._attached_widgets.append(widget)

        def detach(self, widget: QWidget) -> None:
            """
            Detach the tooltip from a widget.

            Args:
                widget: Widget to detach tooltip from
            """
            if widget in self._attached_widgets:
                widget.removeEventFilter(self)
                self._attached_widgets.remove(widget)

        def show_at(self, position: QPoint) -> None:
            """
            Show the tooltip at the specified global position.

            Args:
                position: Global screen position
            """
            self._show_position = position
            self._hide_timer.stop()
            self._show_timer.start(self._show_delay)

        def show_now(self, position: QPoint | None = None) -> None:
            """
            Show the tooltip immediately without delay.

            Args:
                position: Global screen position (uses cursor if None)
            """
            self._show_timer.stop()
            self._show_position = position or QCursor.pos()
            self._do_show()

        def hide_delayed(self) -> None:
            """Hide the tooltip after the hide delay."""
            self._show_timer.stop()
            self._hide_timer.start(self._hide_delay)

        def hide_now(self) -> None:
            """Hide the tooltip immediately."""
            self._show_timer.stop()
            self._hide_timer.stop()
            self.hide()

        def eventFilter(self, watched: QWidget, event) -> bool:
            """Handle events for attached widgets."""
            from PySide6.QtCore import QEvent

            if watched in self._attached_widgets:
                if event.type() == QEvent.Enter:
                    # Show tooltip after delay
                    pos = QCursor.pos() + CURSOR_OFFSET
                    self.show_at(pos)
                    return False
                elif event.type() == QEvent.Leave:
                    # Hide tooltip after delay
                    self.hide_delayed()
                    return False
                elif event.type() == QEvent.MouseMove:
                    # Update position if visible
                    if self.isVisible():
                        self._update_position(QCursor.pos() + CURSOR_OFFSET)
                    return False

            return super().eventFilter(watched, event)

        def _do_show(self) -> None:
            """Actually show the tooltip."""
            if self._show_position:
                self._update_position(self._show_position)
                self.adjustSize()
                self.show()
                self.raise_()

        def _do_hide(self) -> None:
            """Actually hide the tooltip."""
            self.hide()

        def _update_position(self, position: QPoint) -> None:
            """Update tooltip position, keeping it on screen."""
            # Get screen geometry
            screen = QApplication.screenAt(position)
            if screen:
                screen_rect = screen.availableGeometry()
            else:
                screen_rect = QApplication.primaryScreen().availableGeometry()

            # Adjust position to stay on screen
            x = position.x()
            y = position.y()

            # Ensure tooltip fits horizontally
            if x + self.width() > screen_rect.right():
                x = screen_rect.right() - self.width()
            if x < screen_rect.left():
                x = screen_rect.left()

            # Ensure tooltip fits vertically
            if y + self.height() > screen_rect.bottom():
                # Show above cursor if doesn't fit below
                y = position.y() - self.height() - CURSOR_OFFSET.y() * 2
            if y < screen_rect.top():
                y = screen_rect.top()

            self.move(x, y)

    def add_tooltip(
        widget: QWidget,
        text: str,
        rich_text: bool = False,
        show_delay: int = DEFAULT_SHOW_DELAY,
        max_width: int = 300,
    ) -> ToolTip | None:
        """
        Add a tooltip to a widget.

        This is a convenience function that creates a ToolTip and attaches
        it to the widget. For simple tooltips, you can also use
        widget.setToolTip(text) directly.

        Args:
            widget: Widget to add tooltip to
            text: Tooltip text (can be HTML if rich_text=True)
            rich_text: If True, use custom ToolTip with rich text support
            show_delay: Delay before showing tooltip (milliseconds)
            max_width: Maximum width of tooltip

        Returns:
            The ToolTip instance if rich_text=True, otherwise None

        Example:
            # Simple tooltip (uses Qt's built-in tooltip)
            add_tooltip(my_button, "Click to save")

            # Rich text tooltip with custom styling
            add_tooltip(
                my_button,
                "<b>Save</b><br>Save the current document.",
                rich_text=True
            )
        """
        if rich_text:
            tooltip = ToolTip(
                parent=widget,
                text=text,
                show_delay=show_delay,
                max_width=max_width,
            )
            tooltip.attach(widget)
            return tooltip
        else:
            # Use Qt's built-in tooltip for simple cases
            widget.setToolTip(text)
            return None

else:
    # Stub classes when PySide6 is not available
    CURSOR_OFFSET = None

    class ToolTip:  # type: ignore[no-redef]
        """Stub ToolTip for when Qt is not available."""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def set_text(self, text: str) -> None:
            pass

        def text(self) -> str:
            return ""

        def set_show_delay(self, delay: int) -> None:
            pass

        def set_hide_delay(self, delay: int) -> None:
            pass

        def set_max_width(self, width: int) -> None:
            pass

        def set_style(self, style: str) -> None:
            pass

        def attach(self, widget) -> None:
            pass

        def detach(self, widget) -> None:
            pass

        def show_at(self, position) -> None:
            pass

        def show_now(self, position=None) -> None:
            pass

        def hide_delayed(self) -> None:
            pass

        def hide_now(self) -> None:
            pass

    def add_tooltip(widget, text: str, **kwargs) -> None:
        """Stub add_tooltip for when Qt is not available."""
        pass
