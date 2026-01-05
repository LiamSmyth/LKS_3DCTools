"""
CollapsibleSection widget - An expandable/collapsible section with header.

Provides a section with a clickable header that toggles visibility of content.
Optionally includes a checkbox for enable/disable functionality.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QCheckBox,
    )
    from PySide6.QtCore import Qt, Signal

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as QWidgetType


if HAS_QT:

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

        Example:
            section = CollapsibleSection(parent, title="Settings", collapsed=False)
            section.content_layout.addWidget(QLabel("Some content"))
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
            self._checkbox: QCheckBox | None = None

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
            if self._checkable and self._checkbox is not None:
                self._checked = enabled
                self._checkbox.setChecked(enabled)

        def set_title(self, title: str) -> None:
            """Update the section title."""
            self._title_label.setText(title)

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

else:
    # Stub class when PySide6 is not available
    class CollapsibleSection:  # type: ignore[no-redef]
        """Stub CollapsibleSection for when Qt is not available."""

        toggled = None
        enabled_changed = None

        def __init__(self, *args, **kwargs) -> None:
            pass

        @property
        def content(self):
            return None

        @property
        def content_layout(self):
            return None

        def is_collapsed(self) -> bool:
            return False

        def is_expanded(self) -> bool:
            return True

        def is_enabled(self) -> bool:
            return True

        def expand(self) -> None:
            pass

        def collapse(self) -> None:
            pass

        def set_enabled(self, enabled: bool) -> None:
            pass

        def set_title(self, title: str) -> None:
            pass
