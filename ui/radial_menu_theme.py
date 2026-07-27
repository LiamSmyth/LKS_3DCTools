"""Radial menu editor theme — easy-to-edit list / tree sizing.

Edit the constants below to change how large menu-structure rows and
action-picker rows appear in the radial menu editor (standalone window
and LKS panel tab).

Defaults are ~1.5× the previous compact sizes (16px icons / ~10px font /
~20px rows). Colors still come from ``utils.ui.styles``.

IMPORTANT: Do not apply QSS to the menu-structure tree. ``darken_treeview``
uses a QProxyStyle for branch arrows; a stylesheet on that tree breaks them.
Tree sizing is applied via font / iconSize / sizeHint only.

Alignment (siblings at the same depth must share one left column):
1. Every row uses a decoration of exactly ``TREE_ICON_SIZE`` (real SVG/emoji
   or transparent placeholder). Empty ``QIcon()`` does not reserve width.
2. Zebra striping must NOT set ``::item:alternate { background-color }`` in
   cascaded QSS — that path paints a different box model than base rows and
   shifts icons+labels+action IDs by ~1-2px. Parent ``DARK_STYLESHEET``
   strips that rule; zebra uses ``setAlternatingRowColors`` + palette
   ``AlternateBase`` / widget ``alternate-background-color`` only.
3. Nesting indent is only ``TREE_INDENTATION`` per depth.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QListWidget, QTreeWidget, QTreeWidgetItem

# =============================================================================
# EDIT THESE — list / tree visual size (~1.5× former defaults)
# =============================================================================

# Menu-structure tree (left / top list of radial menu items)
TREE_ICON_SIZE: int = 24            # SVG / placeholder decoration size in px (was 16)
TREE_FONT_SIZE_PX: int = 15         # Item label font size in px (was ~10)
TREE_ROW_MIN_HEIGHT: int = 30       # Minimum row height via sizeHint (was ~20)
TREE_INDENTATION: int = 20          # Per-depth indent only (siblings share column)
# Box-model metrics mirrored in utils.ui.styles for cascaded QTreeWidget::item
# (must be identical for base and :alternate — never differ by zebra state)
TREE_ITEM_PADDING: str = "0px 2px"
TREE_ITEM_BORDER: str = "none"
TREE_ITEM_MARGIN: str = "0px"

# Action-picker dialog lists (LKS Actions / 3DCoat Commands)
LIST_FONT_SIZE_PX: int = 15         # List label font size in px (was ~10)
LIST_ITEM_PADDING: str = "3px 6px"  # CSS padding for QListWidget::item
LIST_ROW_MIN_HEIGHT: int = 30       # Minimum list-row height in px

# Directory containing SVG icon assets (utils/ui/data/*.svg)
ICONS_DIR: Path = Path(__file__).resolve().parent.parent / "utils" / "ui" / "data"


# =============================================================================
# APPLY HELPERS
# =============================================================================

def transparent_placeholder_icon(size: int | None = None) -> QIcon:
    """Return a transparent icon that reserves ``TREE_ICON_SIZE`` decoration width.

    Qt does not reserve decoration space for an empty ``QIcon()``, so siblings
    with/without real icons would start their text at different columns.
    """
    side: int = TREE_ICON_SIZE if size is None else size
    pixmap: QPixmap = QPixmap(side, side)
    pixmap.fill(Qt.GlobalColor.transparent)
    return QIcon(pixmap)


def emoji_to_icon(emoji: str, size: int | None = None) -> QIcon:
    """Rasterize an emoji glyph into a fixed-size icon for column alignment."""
    side: int = TREE_ICON_SIZE if size is None else size
    pixmap: QPixmap = QPixmap(side, side)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter: QPainter = QPainter(pixmap)
    font: QFont = QFont("Segoe UI Emoji")
    font.setPixelSize(max(8, side - 4))
    painter.setFont(font)
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), emoji)
    painter.end()
    return QIcon(pixmap)


def list_item_stylesheet() -> str:
    """QSS fragment for radial-editor action-picker list item size / padding."""
    return (
        f"QListWidget::item {{"
        f"  min-height: {LIST_ROW_MIN_HEIGHT}px;"
        f"  padding: {LIST_ITEM_PADDING};"
        f"  font-size: {LIST_FONT_SIZE_PX}px;"
        f"}}"
    )


def apply_tree_list_theme(tree: QTreeWidget) -> None:
    """Apply icon size, font, indent, and row sizing to a menu-structure tree.

    Uses Qt APIs only (no setStyleSheet) so ``darken_treeview`` branch
    arrows keep working. Enables palette-based zebra (not QSS :alternate
    backgrounds) so sibling rows stay horizontally aligned.
    """
    tree.setIconSize(QSize(TREE_ICON_SIZE, TREE_ICON_SIZE))
    tree.setIndentation(TREE_INDENTATION)
    tree.setUniformRowHeights(True)
    tree.setAlternatingRowColors(True)
    font: QFont = tree.font()
    font.setPixelSize(TREE_FONT_SIZE_PX)
    tree.setFont(font)


def apply_action_list_theme(list_widget: QListWidget) -> None:
    """Apply font and row sizing to an action-picker QListWidget."""
    font: QFont = list_widget.font()
    font.setPixelSize(LIST_FONT_SIZE_PX)
    list_widget.setFont(font)
    existing: str = list_widget.styleSheet() or ""
    fragment: str = list_item_stylesheet()
    if fragment not in existing:
        list_widget.setStyleSheet(
            f"{existing}\n{fragment}" if existing else fragment
        )


def apply_tree_item_row_hint(item: QTreeWidgetItem) -> None:
    """Ensure a tree row is tall enough for the themed icon + font."""
    item.setSizeHint(0, QSize(0, TREE_ROW_MIN_HEIGHT))
