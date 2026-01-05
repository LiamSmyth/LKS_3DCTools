"""
LKS UI - Outliner Tab.

Scene tree display with visibility/ghost state and selection controls.

Usage:
    from ui.ui_tab_outliner import create_outliner_tab
    tab_content, refresh_fn = create_outliner_tab(log_success, log_error)
    tabs.add_tab("🌳 Outliner", tab_content)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QBrush

    from utils.ui.widgets import ButtonGrid

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


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
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(4)

    # --- Scene Tree ---
    tree = QTreeWidget()
    tree.setHeaderLabels(["Name", "V", "G", "Polys"])
    tree.setAlternatingRowColors(True)
    tree.setRootIsDecorated(True)
    tree.setColumnWidth(0, 140)
    tree.setColumnWidth(1, 25)
    tree.setColumnWidth(2, 25)
    tree.setColumnWidth(3, 55)
    tree.setMinimumHeight(200)
    layout.addWidget(tree, 1)  # Stretch

    # --- Buttons ---
    def on_select() -> None:
        current = tree.currentItem()
        if current:
            element = current.data(0, Qt.UserRole)
            if element and hasattr(element, 'selectOne'):
                element.selectOne()
                log_success(f"Selected: {current.text(0)}")

    grid = ButtonGrid(columns=1)
    grid.add_button("Select in 3DC", on_select, "Select item in 3DCoat")
    layout.addWidget(grid)

    # --- Refresh Function ---
    def refresh_tree() -> None:
        tree.clear()
        try:
            from utils.scene_api import SceneAPI
            root = SceneAPI.get_sculpt_root()
            if not root:
                QTreeWidgetItem(tree, ["(No scene)", "", "", ""])
                return

            _add_element_to_tree(root, tree)
            tree.expandAll()
        except Exception as e:
            QTreeWidgetItem(tree, [f"Error: {e}", "", "", ""])

    # Initial population
    refresh_tree()

    return container, refresh_tree


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
        is_ghosted: bool = element.ghosted() if hasattr(element, 'ghosted') else False

        # Get polycount if sculpt object
        polys: str = ""
        if element.isSculptObject():
            vol = element.Volume()
            if vol:
                try:
                    polys = f"{vol.getPolycount():,}"
                except:
                    polys = "?"

        vis_text = "✓" if is_visible else "✗"
        ghost_text = "👻" if is_ghosted else ""

        item = QTreeWidgetItem([name, vis_text, ghost_text, polys])

        # Color coding
        if is_ghosted:
            item.setForeground(0, QBrush(QColor("#888888")))
        elif not is_visible:
            item.setForeground(0, QBrush(QColor("#666666")))
        elif element.isSculptObject():
            item.setForeground(0, QBrush(QColor("#90caf9")))

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
