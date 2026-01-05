"""
SectionHeader widget - A styled section header label.

Provides consistent styling for section headers in LKS panels.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import QLabel, QWidget

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as QWidgetType


# Default colors for headers
DEFAULT_HEADER_COLOR: str = "#ffb74d"  # Orange
DEFAULT_SUBHEADER_COLOR: str = "#90caf9"  # Blue


if HAS_QT:

    class SectionHeader(QLabel):
        """
        A styled section header label.

        Args:
            parent: Parent widget
            text: Header text
            sub: If True, use smaller sub-header style
            color: Text color (hex or Qt color name)

        Example:
            header = SectionHeader(parent, text="Main Section")
            sub_header = SectionHeader(parent, text="Sub Section", sub=True)
        """

        def __init__(
            self,
            parent: QWidget | None = None,
            text: str = "",
            sub: bool = False,
            color: str | None = None,
        ) -> None:
            super().__init__(text, parent)

            # Determine styling based on header type
            font_size = "10px" if sub else "11px"

            if color is not None:
                header_color = color
            else:
                header_color = DEFAULT_SUBHEADER_COLOR if sub else DEFAULT_HEADER_COLOR

            self.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: {font_size};
                    color: {header_color};
                    padding: 2px 0;
                }}
            """)

        def set_color(self, color: str) -> None:
            """Update the header color."""
            # Preserve current font size by checking current style
            current_style = self.styleSheet()
            if "10px" in current_style:
                font_size = "10px"
            else:
                font_size = "11px"

            self.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: {font_size};
                    color: {color};
                    padding: 2px 0;
                }}
            """)

else:
    # Stub class when PySide6 is not available
    class SectionHeader:  # type: ignore[no-redef]
        """Stub SectionHeader for when Qt is not available."""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def setText(self, text: str) -> None:
            pass

        def text(self) -> str:
            return ""

        def set_color(self, color: str) -> None:
            pass
