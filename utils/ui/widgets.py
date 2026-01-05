"""
LKS UI Widgets - DEPRECATED: Import from utils.ui.widgets package instead.

This file is kept for backwards compatibility. All widgets have been moved to
individual files in utils/ui/widgets/ for better maintainability.

New location:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid, ActivityLog
    from utils.ui.widgets import ToolTip, add_tooltip  # New!

Individual widget files:
    - utils/ui/widgets/collapsible_section.py
    - utils/ui/widgets/button_grid.py
    - utils/ui/widgets/activity_log.py
    - utils/ui/widgets/labeled_slider.py
    - utils/ui/widgets/section_header.py
    - utils/ui/widgets/tab_widget.py
    - utils/ui/widgets/tooltip.py
"""
from __future__ import annotations

# Re-export everything from the new widgets package for backwards compatibility
from utils.ui.widgets import (
    CollapsibleSection,
    ButtonGrid,
    ActivityLog,
    LabeledSlider,
    SectionHeader,
    TabWidget,
    ToolTip,
    add_tooltip,
    LOG_COLORS,
    LOG_PREFIXES,
    HAS_QT,
)

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
