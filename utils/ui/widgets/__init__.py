"""
LKS UI Widgets Package - Reusable PySide6/Qt components for LKS panels.

This package provides reusable widget primitives for building LKS UI:
- CollapsibleSection: Expandable/collapsible group with header
- ButtonGrid: Grid of buttons with scope-based layout
- ActivityLog: Scrollable log display with timestamped messages
- LabeledSlider: Slider with label and value display
- SectionHeader: Styled section header label
- TabWidget: Tabbed container for organizing content
- ToolTip: Rich text tooltip with delayed display
- add_tooltip: Utility function for adding tooltips

Usage:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ActivityLog

    log = ActivityLog(parent)
    log.log_info("Operation complete")
    log.log_error("Something failed")

All widgets are re-exported here for backwards compatibility.
"""
from __future__ import annotations

from .collapsible_section import CollapsibleSection
from .button_grid import ButtonGrid
from .activity_log import ActivityLog, LOG_COLORS, LOG_PREFIXES
from .labeled_slider import LabeledSlider
from .section_header import SectionHeader
from .tab_widget import TabWidget
from .tooltip import ToolTip, add_tooltip

# Check if Qt is available (re-export for convenience)
try:
    from PySide6.QtWidgets import QWidget
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

__all__ = [
    "CollapsibleSection",
    "ButtonGrid",
    "ActivityLog",
    "LabeledSlider",
    "SectionHeader",
    "TabWidget",
    "ToolTip",
    "add_tooltip",
    "LOG_COLORS",
    "LOG_PREFIXES",
    "HAS_QT",
]
