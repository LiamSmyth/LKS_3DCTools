"""
GripBox - Individual widget wrapper with drag column for reordering.

A widget wrapper that adds a thin grip column on the left side for drag-drop reordering.
The grip column spans the full height of the contained widget.

Usage:
    from utils.ui.widgets.grip_box_item import GripBox
    
    # Note: Typically used inside GripBoxContainer, not directly
    grip_box = GripBox(my_widget, state_key="widget1")
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtCore import QPoint

try:
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel
    from PySide6.QtCore import Qt, QMimeData, QPoint
    from PySide6.QtGui import QDrag
    
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


if HAS_QT:
    
    class GripBox(QFrame):
        """
        A single item with a grip column for drag-drop reordering.
        
        Layout: [grip column (fixed width)] [content widget (expands)]
        
        The grip column is a thin vertical bar on the left that spans the full
        height of the content. The entire column is draggable.
        """
        def __init__(
            self,
            content_widget: QWidget,
            state_key: str | None = None,
            parent: QWidget | None = None
        ):
            super().__init__(parent)
            self.content_widget = content_widget
            self.state_key = state_key
            self.drag_start_pos: QPoint | None = None
            
            # Frame styling - minimal, just slight background on hover
            self.setFrameShape(QFrame.NoFrame)
            self.setStyleSheet("""
                GripBox {
                    background-color: transparent;
                    margin: 0px;
                    padding: 0px;
                }
                GripBox:hover {
                    background-color: #313131;
                }
            """)
            
            # Layout: [grip column] [content]
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Grip column - fixed width, full height, slightly darker
            self.grip_column = QFrame()
            self.grip_column.setFixedWidth(14)
            self.grip_column.setStyleSheet("""
                QFrame {
                    background-color: #252525;
                    border-right: 1px solid #1a1a1a;
                }
                QFrame:hover {
                    background-color: #2f2f2f;
                }
            """)
            self.grip_column.setCursor(Qt.SizeVerCursor)
            
            # Grip icon (centered vertically via layout)
            grip_layout = QVBoxLayout(self.grip_column)
            grip_layout.setContentsMargins(0, 0, 0, 0)
            grip_layout.addStretch()
            
            grip_icon = QLabel("⋮⋮")
            grip_icon.setStyleSheet("""
                QLabel {
                    color: #555555;
                    font-size: 11px;
                    padding: 0px;
                    background-color: transparent;
                }
            """)
            grip_icon.setAlignment(Qt.AlignCenter)
            grip_icon.setToolTip("Drag to reorder")
            grip_layout.addWidget(grip_icon)
            
            grip_layout.addStretch()
            
            layout.addWidget(self.grip_column)
            
            # Content widget - expands to fill space
            layout.addWidget(content_widget, 1)
        
        def mousePressEvent(self, event):
            """Start drag on grip column click."""
            if event.button() == Qt.LeftButton:
                # Check if click is on grip column
                grip_rect = self.grip_column.geometry()
                if grip_rect.contains(event.pos()):
                    self.drag_start_pos = event.pos()
            super().mousePressEvent(event)
        
        def mouseMoveEvent(self, event):
            """Initiate drag if moved far enough."""
            if not (event.buttons() & Qt.LeftButton):
                return
            if not self.drag_start_pos:
                return
            
            # Check if moved far enough to start drag
            if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
                return
            
            # Create drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(f"grip_box_{id(self)}")
            drag.setMimeData(mime_data)
            
            # Simple drag without pixmap (safer)
            drag.exec(Qt.MoveAction)
            self.drag_start_pos = None
        
        def mouseReleaseEvent(self, event):
            """Clear drag state."""
            self.drag_start_pos = None
            super().mouseReleaseEvent(event)

else:
    # Stub class when PySide6 not available
    class GripBox:  # type: ignore[no-redef]
        """Stub GripBox for when Qt is not available."""
        def __init__(self, *args, **kwargs):
            self.content_widget = None
            self.state_key = None
