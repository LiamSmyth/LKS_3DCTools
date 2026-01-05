"""
LKS UI Widget - Sub Header.

Small section header label for subdividing collapsible sections.

Usage:
    from ui.ui_widget_sub_header import create_sub_header
    layout.addWidget(create_sub_header("Section Name"))
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel

try:
    from PySide6.QtWidgets import QLabel
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


def create_sub_header(text: str) -> "QLabel":
    """
    Create a styled sub-section header label.

    Args:
        text: Header text

    Returns:
        QLabel styled as a sub-header
    """
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #888; font-size: 9px; font-weight: bold;")
    return lbl


# Stub for no Qt
if not HAS_QT:
    def create_sub_header(text: str):  # type: ignore
        return None
