"""
LKS UI - Outliner Tab.

Scene tree display with visibility/ghost state and selection controls.

Usage:
    from ui.ui_tab_outliner import create_outliner_tab
    tab_content, refresh_fn = create_outliner_tab(log_success, log_error)
    tabs.add_tab("🌳 Outliner", tab_content)
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtGui import QIcon

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QBrush, QFont, QPixmap, QPainter, QIcon
    from PySide6.QtSvg import QSvgRenderer

    from utils.ui.widgets import ButtonGrid

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False

# =============================================================================
# SVG ICON HELPERS (for visibility/ghost columns)
# =============================================================================

_ICONS_DIR: Path = Path(__file__).resolve().parent.parent / "utils" / "ui" / "data"
_ICON_SIZE: int = 14  # small enough to not expand the 8pt font row height

_ICON_COLOR_VISIBLE: str = "#90caf9"  # accent blue for visible
_ICON_COLOR_HIDDEN: str = "#555555"  # muted gray for hidden
_ICON_COLOR_GHOSTED: str = "#ffb74d"  # orange accent for ghosted
_ICON_COLOR_UNGHOSTED: str = "#3a3a3a"  # dim border for not ghosted


def _make_outliner_icon(name: str, color: str) -> "QIcon":
    """Create a QIcon from an SVG, replacing currentColor and rendering at _ICON_SIZE."""
    svg_path: Path = _ICONS_DIR / f"{name}.svg"
    if not svg_path.is_file():
        return QIcon()
    content: str = svg_path.read_text(encoding="utf-8")
    content = content.replace("currentColor", color)
    renderer: QSvgRenderer = QSvgRenderer(content.encode("utf-8"))
    pixmap: QPixmap = QPixmap(_ICON_SIZE, _ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter: QPainter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# Pre-bake the four icon variants at module load time
_ICON_VISIBLE: "QIcon | None" = None
_ICON_HIDDEN: "QIcon | None" = None
_ICON_GHOSTED: "QIcon | None" = None
_ICON_UNGHOSTED: "QIcon | None" = None

if HAS_QT:
    _ICON_VISIBLE = _make_outliner_icon("visibility", _ICON_COLOR_VISIBLE)
    _ICON_HIDDEN = _make_outliner_icon("visibility_off", _ICON_COLOR_HIDDEN)
    _ICON_GHOSTED = _make_outliner_icon("ghost", _ICON_COLOR_GHOSTED)
    _ICON_UNGHOSTED = _make_outliner_icon("ghost_off", _ICON_COLOR_UNGHOSTED)


# =============================================================================
# TREE LAYOUT CONSTANTS
# =============================================================================

_BRANCH_ARROW_SCALE: float = 0.5
_TREE_INDENT: int = 5
_COL_NAME_W: int = 140
_COL_VIS_W: int = 22
_COL_GHOST_W: int = 22
_COL_POLYS_W: int = 50
_TREE_MIN_HEIGHT: int = 120
_TREE_FONT_SIZE: int = 8
_HEADER_FONT_SIZE: int = 7

# Foreground colors for tree items
_GHOSTED_COLOR: str = "#888888"
_HIDDEN_COLOR: str = "#666666"
_SCULPT_COLOR: str = "#90caf9"

# =============================================================================
# HELP TEXT
# =============================================================================

def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


# =============================================================================
# OUTLINER TAB FACTORY
# =============================================================================

def create_outliner_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
) -> tuple["QWidget", Callable[[], None]]:
    """
    Create the outliner tab content.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages

    Returns:
        Tuple of (tab_widget, refresh_function)
    """
    from utils.ui.widgets.tab_container import StandardTabBody

    body = StandardTabBody(
        title="Scene Objects",
        info_tooltip=_load_ui_tooltip("outliner_tab.md"),
    )
    layout: QVBoxLayout = body.content_layout

    tree = QTreeWidget()
    tree.setHeaderLabels(["Name", "", "", "Polys"])
    tree.setAlternatingRowColors(False)
    tree.setRootIsDecorated(True)
    tree.setIndentation(_TREE_INDENT)
    tree.setColumnWidth(0, _COL_NAME_W)
    tree.setColumnWidth(1, _COL_VIS_W)
    tree.setColumnWidth(2, _COL_GHOST_W)
    tree.setColumnWidth(3, _COL_POLYS_W)
    tree.setMinimumHeight(_TREE_MIN_HEIGHT)
    # Force light branch arrows on dark background (must be BEFORE setStyleSheet)
    from lks_utils.gui_qt.theme import darken_treeview
    darken_treeview(tree, branch_scale=_BRANCH_ARROW_SCALE)

    # Apply font sizing via QFont (not QSS, which would wrap the style and
    # block the QProxyStyle override in darken_treeview)
    font: QFont = tree.font()
    font.setPointSize(_TREE_FONT_SIZE)
    tree.setFont(font)
    header_font: QFont = tree.header().font()
    header_font.setPointSize(_HEADER_FONT_SIZE)
    tree.header().setFont(header_font)
    tree.setToolTip(
        "Scene objects tree — eye icon=Visible/Hidden, ghost icon=Ghosted/Unghosted, Polys=Polycount. Click to select.")
    layout.addWidget(tree, 1)

    # --- Scene Object Button ---
    def on_select() -> None:
        current = tree.currentItem()
        if current:
            element = current.data(0, Qt.UserRole)
            if element and hasattr(element, 'selectOne'):
                element.selectOne()
                log_success(f"Selected: {current.text(0)}")

    scene_btn_grid = ButtonGrid(columns=1)
    scene_btn_grid.add_button("Select Object", on_select,
                              "Select scene item in 3DCoat")
    layout.addWidget(scene_btn_grid)

    # --- Refresh Function ---
    def refresh_tree() -> None:
        tree.clear()
        try:
            from utils.scene_api import SceneAPI
            root = SceneAPI.get_sculpt_root()
            if not root:
                QTreeWidgetItem(tree, ["(No scene)", "", "", ""])
            else:
                _add_element_to_tree(root, tree)
                tree.expandAll()
        except Exception as e:
            QTreeWidgetItem(tree, [f"Error: {e}", "", "", ""])

    # Initial population
    refresh_tree()

    return body, refresh_tree


# =============================================================================
# POLYCOUNT COLOR GRADIENT
# =============================================================================

# Breakpoints: (polycount, hex_color) — interpolated between for smooth gradient
_POLY_COLOR_BREAKPOINTS: list[tuple[int, str]] = [
    (0,          "#90caf9"),   # blue — very safe
    (50_000,     "#90caf9"),   # blue
    (200_000,    "#81c784"),   # green
    (1_000_000,  "#ffd54f"),   # yellow
    (5_000_000,  "#ffb74d"),   # orange
    (10_000_000, "#ef5350"),   # red — extreme
]


def _lerp_hex_color(hex1: str, hex2: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    r1: int = int(hex1[1:3], 16)
    g1: int = int(hex1[3:5], 16)
    b1: int = int(hex1[5:7], 16)
    r2: int = int(hex2[1:3], 16)
    g2: int = int(hex2[3:5], 16)
    b2: int = int(hex2[5:7], 16)
    r: int = int(r1 + (r2 - r1) * t)
    g: int = int(g1 + (g2 - g1) * t)
    b: int = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _polycount_color(polycount: int) -> str:
    """Return a hex color for the given polycount, interpolating between breakpoints."""
    if polycount <= 0:
        return _POLY_COLOR_BREAKPOINTS[0][1]
    for i in range(len(_POLY_COLOR_BREAKPOINTS) - 1):
        lo_poly, lo_color = _POLY_COLOR_BREAKPOINTS[i]
        hi_poly, hi_color = _POLY_COLOR_BREAKPOINTS[i + 1]
        if lo_poly <= polycount <= hi_poly:
            if lo_poly == hi_poly:
                return lo_color
            t: float = (polycount - lo_poly) / (hi_poly - lo_poly)
            return _lerp_hex_color(lo_color, hi_color, t)
    return _POLY_COLOR_BREAKPOINTS[-1][1]  # fallback: red


# =============================================================================
# HELPERS
# =============================================================================

def _add_element_to_tree(
    element,  # coat.SceneElement
    parent,   # QTreeWidget | QTreeWidgetItem
) -> None:
    """Add a scene element and its children to the tree."""
    try:
        from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QBrush

        name: str = element.name() if hasattr(element, 'name') else "Unknown"
        is_visible: bool = element.visible() if hasattr(element, 'visible') else True
        is_ghosted: bool = element.ghost() if hasattr(element, 'ghost') else False

        # Get polycount if sculpt object
        polys: str = ""
        polys_raw: int = 0
        if element.isSculptObject():
            vol = element.Volume()
            if vol:
                try:
                    polys_raw = vol.getPolycount()
                    polys = f"{polys_raw:,}"
                except:
                    polys = "?"

        # Create tree item with empty text columns (icons fill columns 1-2)
        item = QTreeWidgetItem([name, "", "", polys])
        if _ICON_VISIBLE is not None and _ICON_HIDDEN is not None:
            item.setIcon(1, _ICON_VISIBLE if is_visible else _ICON_HIDDEN)
        if _ICON_GHOSTED is not None and _ICON_UNGHOSTED is not None:
            item.setIcon(2, _ICON_GHOSTED if is_ghosted else _ICON_UNGHOSTED)

        # Color coding — name column
        if is_ghosted:
            item.setForeground(0, QBrush(QColor(_GHOSTED_COLOR)))
        elif not is_visible:
            item.setForeground(0, QBrush(QColor(_HIDDEN_COLOR)))
        elif element.isSculptObject():
            item.setForeground(0, QBrush(QColor(_SCULPT_COLOR)))

        # Color coding — polys column (gradient by polycount)
        if polys_raw > 0:
            item.setForeground(3, QBrush(QColor(_polycount_color(polys_raw))))

        item.setData(0, Qt.UserRole, element)

        if isinstance(parent, QTreeWidget):
            parent.addTopLevelItem(item)
        else:
            parent.addChild(item)

        # Add children
        if hasattr(element, 'childCount') and hasattr(element, 'child'):
            for i in range(element.childCount()):
                child = element.child(i)
                if child:
                    _add_element_to_tree(child, item)

    except Exception as e:
        print(f"[LKS] Error adding element: {e}")


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_outliner_tab(*args, **kwargs):  # type: ignore
        return None, lambda: None
