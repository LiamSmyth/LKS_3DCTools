"""
LKS UI - Getting Started Tab.

First-launch onboarding guide covering setup, hotkey mapping,
radial menus, and an overview of each tab.

Usage:
    from ui.ui_tab_getting_started import create_getting_started_tab
    tab = create_getting_started_tab()
    tabs.add_tab("Getting Started", tab)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from utils.ui.widgets.tab_container import StandardTabBody
    from utils.ui.widgets import CollapsibleSection, MarkdownDisplay
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources — resolve relative to LKS root data/
_WELCOME = MarkdownFileResource("embedded_docs/getting_started/welcome.md")
_HOTKEYS = MarkdownFileResource("embedded_docs/getting_started/hotkeys.md")
_RADIAL = MarkdownFileResource("embedded_docs/getting_started/radial.md")
_TABS_OVERVIEW = MarkdownFileResource("embedded_docs/getting_started/tabs_overview.md")
_TIPS = MarkdownFileResource("embedded_docs/getting_started/tips.md")


def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


def _md_display(resource: MarkdownFileResource) -> MarkdownDisplay:
    """Create a compact markdown display from a MarkdownFileResource."""
    display = MarkdownDisplay(resource)
    display.set_compact(True)
    return display


def create_getting_started_tab() -> QWidget | None:
    """Create the Getting Started onboarding tab.

    Returns:
        StandardTabBody widget with onboarding content, or None if Qt unavailable.
    """
    if not HAS_QT:
        return None

    body = StandardTabBody(
        title="Getting Started",
        info_tooltip=_load_ui_tooltip("getting_started_tab.md"),
    )
    layout = body.content_layout

    # SECTION 1 — Welcome
    welcome = CollapsibleSection(
        title="Welcome to LKS Tools",
        color="#64b5f6",
        collapsed=False,
    )
    welcome.content_layout.addWidget(_md_display(_WELCOME))
    layout.addWidget(welcome)

    # SECTION 2 — Mapping Tools to Hotkeys
    hotkeys = CollapsibleSection(
        title="Mapping Tools to Hotkeys",
        color="#81c784",
        collapsed=False,
    )
    hotkeys.content_layout.addWidget(_md_display(_HOTKEYS))
    layout.addWidget(hotkeys)

    # SECTION 3 — Radial Menus
    radial = CollapsibleSection(
        title="Radial Menus (Quick-Access Pie Menus)",
        color="#ce93d8",
        collapsed=False,
    )
    radial.content_layout.addWidget(_md_display(_RADIAL))
    layout.addWidget(radial)

    # SECTION 4 — Tab Overview
    tabs_overview = CollapsibleSection(
        title="What Each Tab Does",
        color="#ffb74d",
        collapsed=True,
    )
    tabs_overview.content_layout.addWidget(_md_display(_TABS_OVERVIEW))
    layout.addWidget(tabs_overview)

    # SECTION 5 — Tips
    tips = CollapsibleSection(
        title="Tips & Best Practices",
        color="#4fc3f7",
        collapsed=True,
    )
    tips.content_layout.addWidget(_md_display(_TIPS))
    layout.addWidget(tips)

    layout.addStretch()
    return body


# Stub for no Qt
if not HAS_QT:
    def create_getting_started_tab(*args, **kwargs):  # type: ignore
        return None
