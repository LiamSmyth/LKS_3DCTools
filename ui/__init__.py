"""
LKS UI Package.

Modular UI components for the LKS Tools panel.

Structure:
    ui_main.py              - Main panel (header, tabs, footer, log)
    ui_tab_*.py             - Tab content factories
    ui_collapsible_*.py     - Collapsible section factories

Usage:
    from ui.ui_main import LKSMainPanel
    panel = LKSMainPanel()
    panel.show()
"""
from __future__ import annotations

# Re-export main panel for convenience
try:
    from ui.ui_main import LKSMainPanel
except ImportError:
    LKSMainPanel = None  # type: ignore

__all__: list[str] = [
    "LKSMainPanel",
]
