"""
HelpMenu - Collapsible help section with scrollable content.

Provides a consistent help/info section with:
- Question mark circle emoji (❓) for visual recognition
- Always collapsed by default
- Scrollable text area with max height
- Styled to match LKS dark theme

Usage:
    from utils.ui.widgets import HelpMenu
    
    help_menu = HelpMenu(
        title="About Hotkeys",
        content=(
            "<b>How to use:</b><br/>"
            "Step 1: Do this<br/>"
            "Step 2: Do that<br/>"
        ),
        max_height=200  # Optional, default 200
    )
    layout.addWidget(help_menu)
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt

from .collapsible_section import CollapsibleSection


class HelpMenu(QWidget):
    """
    Collapsible help section with scrollable text content.
    
    Always collapsed by default, uses question mark emoji for consistency.
    """
    
    def __init__(
        self,
        title: str = "Help",
        content: str = "",
        max_height: int = 200,
        parent: QWidget | None = None,
    ) -> None:
        """
        Create a help menu widget.
        
        Args:
            title: Title text (without emoji prefix)
            content: HTML or plain text content
            max_height: Maximum height of scroll area in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Add question mark emoji prefix
        full_title = f"❓ {title}"
        
        # Create collapsible section (always collapsed)
        self._section = CollapsibleSection(
            title=full_title,
            color="#90a4ae",  # Gray color for info sections
            collapsed=True
        )
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(max_height)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2b2b2b;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)
        
        # Create content label
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        content_label.setStyleSheet("color: #aaa; font-size: 10px; padding: 8px;")
        content_label.setOpenExternalLinks(True)
        
        scroll_area.setWidget(content_label)
        self._section.content_layout.addWidget(scroll_area)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._section)
