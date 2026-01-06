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
            color: str = "#90caf9",  # Unified icy blue
            state_key: str | None = None,  # Key for persisting state
        ) -> None:
            super().__init__(parent)
            self._state_key: str | None = state_key
            
            # Load initial collapsed state from settings if state_key provided
            if state_key:
                try:
                    from utils.lks_settings import get_ui_state
                    ui_state = get_ui_state()
                    # Use saved state, fallback to parameter
                    collapsed = not getattr(ui_state, f"{state_key}_expanded", not collapsed)
                except Exception as e:
                    print(f"[CollapsibleSection] Failed to load state for {state_key}: {e}")
            
            self._collapsed: bool = collapsed
            self._checkable: bool = checkable
            self._checked: bool = checked
            self._color: str = "#90caf9"  # Always use unified icy blue
            self._checkbox: QCheckBox | None = None

            # Main container with rounded border
            container_frame = QFrame()
            container_frame.setStyleSheet("""
                QFrame {
                    background-color: #2b2b2b;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    margin: 2px;
                }
            """)
            container_layout = QVBoxLayout(container_frame)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            # Header frame
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(6, 4, 6, 4)
            header_layout.setSpacing(6)

            # Toggle button with plain arrow (▸ collapsed, ▾ expanded)
            self._toggle_btn = QPushButton("▾" if not collapsed else "▸")
            self._toggle_btn.setFixedSize(16, 16)
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #90caf9;
                    font-size: 12px;
                    padding: 0px;
                }
                QPushButton:hover { color: #b3d9ff; }
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
            self._title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 11px;
                    color: #90caf9;
                    background: transparent;
                }
                QLabel:hover { color: #b3d9ff; }
            """)
            self._title_label.setCursor(Qt.PointingHandCursor)
            self._title_label.mousePressEvent = lambda e: self._on_toggle()
            header_layout.addWidget(self._title_label)
            header_layout.addStretch()

            container_layout.addWidget(header_frame)

            # Content frame with left accent line
            self._content_frame = QFrame()
            self._content_frame.setStyleSheet("""
                QFrame {
                    border-left: 2px solid #90caf9;
                    background: transparent;
                }
            """)
            self._content_layout = QVBoxLayout(self._content_frame)
            self._content_layout.setContentsMargins(12, 6, 6, 6)
            self._content_layout.setSpacing(4)
            container_layout.addWidget(self._content_frame)

            # Add container to main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(container_frame)
            
            # Store container reference for visibility toggle
            self._container_frame = container_frame

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
                self._toggle_btn.setText("▾")
                self._content_frame.setVisible(True)
                self.toggled.emit(False)
                self._save_state()

        def collapse(self) -> None:
            """Collapse the section."""
            if not self._collapsed:
                self._collapsed = True
                self._toggle_btn.setText("▸")
                self._content_frame.setVisible(False)
                self.toggled.emit(True)
                self._save_state()
        
        def _save_state(self) -> None:
            """Save collapsed state to settings if state_key is set."""
            if self._state_key:
                try:
                    from utils.lks_settings import get_ui_state, save_ui_state
                    ui_state = get_ui_state()
                    setattr(ui_state, f"{self._state_key}_expanded", not self._collapsed)
                    save_ui_state()
                except Exception as e:
                    print(f"[CollapsibleSection] Failed to save state for {self._state_key}: {e}")

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
