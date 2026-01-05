"""
LKS UI - Outliner Tab.

Scene tree display with visibility/ghost state and selection controls.
Also includes a layer tree for paint layers.

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
        QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel,
        QSplitter,
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

    # Create splitter for scene tree and layer tree
    splitter = QSplitter(Qt.Vertical)

    # --- Scene Tree Section ---
    scene_section = QWidget()
    scene_layout = QVBoxLayout(scene_section)
    scene_layout.setContentsMargins(0, 0, 0, 0)
    scene_layout.setSpacing(2)

    scene_label = QLabel("📦 Scene Objects")
    scene_label.setStyleSheet("font-weight: bold; color: #90caf9;")
    scene_layout.addWidget(scene_label)

    tree = QTreeWidget()
    tree.setHeaderLabels(["Name", "V", "G", "Polys"])
    tree.setAlternatingRowColors(True)
    tree.setRootIsDecorated(True)
    tree.setColumnWidth(0, 140)
    tree.setColumnWidth(1, 25)
    tree.setColumnWidth(2, 25)
    tree.setColumnWidth(3, 55)
    tree.setMinimumHeight(120)
    scene_layout.addWidget(tree, 1)

    # --- Scene Object Button (directly under scene tree) ---
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
    scene_layout.addWidget(scene_btn_grid)

    splitter.addWidget(scene_section)

    # --- Layer Tree Section ---
    # NOTE: Layer tree is a STUB. 3DCoat's layer API implicitly creates layers
    # when querying non-existent IDs, making per-frame enumeration impossible.
    # Layer operations must use UI commands as workarounds.
    layer_section = QWidget()
    layer_layout = QVBoxLayout(layer_section)
    layer_layout.setContentsMargins(0, 0, 0, 0)
    layer_layout.setSpacing(2)

    layer_label = QLabel("🎨 Layers (stub - no per-frame query)")
    layer_label.setStyleSheet("font-weight: bold; color: #ce93d8;")
    layer_layout.addWidget(layer_label)

    layer_tree = QTreeWidget()
    layer_tree.setHeaderLabels(["Name", "Vis", "", ""])
    layer_tree.setAlternatingRowColors(True)
    layer_tree.setRootIsDecorated(False)
    layer_tree.setColumnWidth(0, 140)
    layer_tree.setColumnWidth(1, 35)
    layer_tree.setColumnWidth(2, 35)
    layer_tree.setColumnWidth(3, 35)
    layer_tree.setMinimumHeight(60)
    layer_layout.addWidget(layer_tree, 1)

    # --- Layer Button (stub - does nothing for now) ---
    def on_select_layer() -> None:
        # STUB: Cannot activate layers safely without knowing their IDs
        log_error("Layer activation not implemented (API limitation)")

    layer_btn_grid = ButtonGrid(columns=1)
    layer_btn_grid.add_button("Activate Layer (stub)", on_select_layer,
                              "Not implemented - 3DCoat API limitation")
    layer_layout.addWidget(layer_btn_grid)

    splitter.addWidget(layer_section)

    # Set initial splitter proportions (scene takes more space)
    splitter.setSizes([250, 80])
    layout.addWidget(splitter, 1)

    # --- Refresh Function ---
    def refresh_tree() -> None:
        # Refresh scene tree only - layer tree is a stub (no per-frame query)
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

        # Layer tree is NOT refreshed per-frame - just show static stub message

    # Initial population
    _populate_layer_stub(layer_tree)  # Static stub - only called once
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


def _populate_layer_stub(tree) -> None:
    """Populate the layer tree with a static stub message.

    3DCoat's layer API is fundamentally broken for enumeration:
    - getLayerName(id), layerVisible(id), layerIsEmpty(id) all CREATE layers
      when called with non-existent IDs
    - There is no getLayersCount() or safe enumeration method
    - getLayer(name) requires knowing the name ahead of time

    Layer operations must use UI commands as workarounds, not per-frame queries.
    See Scene_layer_utils.py for the consolidate_layers algorithm.
    """
    try:
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtGui import QColor, QBrush

        # Static stub - explain the limitation
        stub_msg = QTreeWidgetItem(["Layer API is limited", "", "", ""])
        stub_msg.setForeground(0, QBrush(QColor("#888888")))
        tree.addTopLevelItem(stub_msg)

        note1 = QTreeWidgetItem(["Use Layers panel in 3DCoat", "", "", ""])
        note1.setForeground(0, QBrush(QColor("#666666")))
        tree.addTopLevelItem(note1)

        note2 = QTreeWidgetItem(["'Consolidate Layers' in tools", "", "", ""])
        note2.setForeground(0, QBrush(QColor("#666666")))
        tree.addTopLevelItem(note2)

    except Exception as e:
        print(f"[LKS] Error populating layer stub: {e}")


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_outliner_tab(*args, **kwargs):  # type: ignore
        return None, lambda: None
