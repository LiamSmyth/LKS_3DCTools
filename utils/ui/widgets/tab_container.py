"""
Tab Container - Helper for creating tabs with consistent structure.

Provides a factory function that creates tabs with:
- Revert UI State button at the top
- Scroll area for content
- Consistent styling

Usage:
    from utils.ui.widgets.tab_container import create_tab_with_revert
    
    container = create_tab_with_revert(
        log_success, log_error,
        title="My Tab"
    )
    # Add your content to container.content_layout
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget, QVBoxLayout

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QScrollArea, QPushButton, QLabel
    )
    from PySide6.QtCore import Qt
    
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


class TabContainer:
    """
    Container for tab content with built-in revert button.
    
    Attributes:
        widget: The main QWidget for the tab
        content_layout: QVBoxLayout where tab content should be added
    """
    def __init__(self, widget: "QWidget", content_layout: "QVBoxLayout"):
        self.widget = widget
        self.content_layout = content_layout


def create_tab_with_revert(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    title: str | None = None,
    scrollable: bool = True,
) -> TabContainer:
    """
    Create a tab container with a revert button at the top.
    
    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        title: Optional title label for the tab
        scrollable: Whether to wrap content in a scroll area
    
    Returns:
        TabContainer with widget and content_layout
    
    Example:
        tab = create_tab_with_revert(log_success, log_error, "Tools")
        tab.content_layout.addWidget(my_section)
        return tab.widget
    """
    if not HAS_QT:
        raise ImportError("PySide6 is required for tab containers")
    
    # Main container
    container = QWidget()
    main_layout = QVBoxLayout(container)
    main_layout.setContentsMargins(4, 4, 4, 4)
    main_layout.setSpacing(4)
    
    # Optional title
    if title:
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 12px;
            color: #90caf9;
            padding: 4px 0px;
        """)
        main_layout.addWidget(title_label)
    
    # Revert button
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
    revert_btn.setToolTip("Reset all collapsible section states to their defaults")
    
    def on_revert() -> None:
        try:
            from utils.lks_settings import reset_ui_state
            reset_ui_state()
            log_success("UI state reverted to defaults. Restart panel to apply.")
        except Exception as e:
            log_error(f"Failed to revert UI state: {e}")
    
    revert_btn.clicked.connect(on_revert)
    main_layout.addWidget(revert_btn)
    
    # Content area
    if scrollable:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)  # Stretch factor 1
    else:
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        main_layout.addLayout(content_layout, 1)
    
    return TabContainer(container, content_layout)
