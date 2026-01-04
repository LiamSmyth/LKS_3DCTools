"""
LKS UI module.

Contains PySide6/Qt-based UI components and styles for the LKS cModule.

Widgets:
    CollapsibleSection: Expandable/collapsible group with header
    ButtonGrid: Grid of buttons with scope-based layout
    ActivityLog: Scrollable log display with timestamped messages
    LabeledSlider: Slider with label and value display
    SectionHeader: Styled section header label
    add_tooltip: Utility to add tooltips to widgets
"""
from .styles import DARK_STYLESHEET
from .widgets import (
    CollapsibleSection,
    ButtonGrid,
    ActivityLog,
    LabeledSlider,
    SectionHeader,
    add_tooltip,
)

__all__ = [
    "DARK_STYLESHEET",
    "CollapsibleSection",
    "ButtonGrid",
    "ActivityLog",
    "LabeledSlider",
    "SectionHeader",
    "add_tooltip",
]
