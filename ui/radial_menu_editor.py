"""
Radial Menu Configuration Editor.

Qt-based UI for creating and editing radial menu configurations.
Supports:
- Tree-based menu structure editing
- Action picker with registered LKS commands and 3DCoat native commands
- Drag-drop reordering
- Save/load configurations
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
        QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
        QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QSplitter,
        QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QApplication,
        QMenu, QInputDialog, QTabWidget, QTextEdit
    )
    from PySide6.QtGui import QAction, QIcon, QDrag
    HAS_QT = True
except ImportError:
    HAS_QT = False

# Try to import styles
try:
    from utils.ui.styles import DARK_STYLESHEET
except ImportError:
    DARK_STYLESHEET = ""


# =============================================================================
# CONSTANTS
# =============================================================================

# Default config path
_DATA_DIR: Path = Path(__file__).parent.parent / "data"
DEFAULT_CONFIG_PATH: Path = _DATA_DIR / "radial_menu_config.json"

# Common 3DCoat commands that users might want to map
COMMON_3DCOAT_COMMANDS: list[tuple[str, str]] = [
    # Ghost/Visibility
    ("$ToggleGhost", "Toggle Ghost (Native)"),
    ("$HideObject", "Hide Object"),
    ("$ShowAllObjects", "Show All Objects"),
    ("$Isolate_ghosting", "Isolate Ghosting"),
    ("$Invert_vox_visibility", "Invert Visibility"),
    ("$Toggle_vox_visibility", "Toggle Visibility"),

    # Transform
    ("$StartObjTransform3D", "Move/Transform Object"),
    ("$TRANSFORM_SCALE_FREE", "Scale Free"),
    ("$TRANSFORM_ROTATE_FREE", "Rotate Free"),
    ("$TRANSFORM_TRANSLATE_FREE", "Translate Free"),

    # Mesh Operations
    ("$DecimateToRetopo", "Decimate to Retopo"),
    ("$RemeshInPlace", "Remesh In Place"),
    ("$VoxToSurface", "Convert to Surface"),
    ("$SurfaceToVox", "Convert to Voxels"),

    # Tools
    ("$Pen", "Pen Tool"),
    ("$Pick_color", "Pick Color"),
    ("$SMOOTH_STROKE", "Smooth Stroke"),

    # Misc
    ("$UNDO", "Undo"),
    ("$REDO", "Redo"),
    ("$SYMMETRY", "Toggle Symmetry"),
]

# Common icons for menu items
COMMON_ICONS: list[str] = [
    "🔻", "🔺", "🔄", "⚙️", "📐", "📏", "👁️", "👻",
    "🎨", "✨", "🔧", "📦", "🗂️", "🌳", "☝️", "🌎",
    "✂️", "🔗", "🎯", "💾", "📁", "🖌️", "🔍", "⬆️", "⬇️"
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MenuItemData:
    """Data for a single menu item."""
    label: str
    icon: str = ""
    action: str = ""  # 3DCoat command like "$CommandName"
    description: str = ""
    angle: float | None = None
    children: list[MenuItemData] | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        data = {"label": self.label}
        if self.icon:
            data["icon"] = self.icon
        if self.action:
            data["action"] = self.action
        if self.description:
            data["description"] = self.description
        if self.angle is not None:
            data["angle"] = self.angle
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MenuItemData:
        """Create from dict (parsed JSON)."""
        children = None
        if "children" in data:
            children = [cls.from_dict(c) for c in data["children"]]
        return cls(
            label=data["label"],
            icon=data.get("icon", ""),
            action=data.get("action", ""),
            description=data.get("description", ""),
            angle=data.get("angle"),
            children=children,
        )


# =============================================================================
# ACTION PICKER DIALOG
# =============================================================================

class ActionPickerDialog(QDialog):
    """Dialog for picking an action (3DCoat command or LKS action)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick Action")
        self.setMinimumSize(500, 400)
        self._selected_action: str = ""
        self._setup_ui()
        self._load_actions()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Type to filter...")
        self._search_edit.textChanged.connect(self._filter_actions)
        search_layout.addWidget(self._search_edit)
        layout.addLayout(search_layout)

        # Tabs for different action sources
        self._tabs = QTabWidget()

        # Tab 1: LKS Registered Actions
        self._lks_list = QListWidget()
        self._lks_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tabs.addTab(self._lks_list, "LKS Actions")

        # Tab 2: Common 3DCoat Commands
        self._coat_list = QListWidget()
        self._coat_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tabs.addTab(self._coat_list, "3DCoat Commands")

        # Tab 3: Custom Command
        custom_widget = QWidget()
        custom_layout = QVBoxLayout(custom_widget)
        custom_layout.addWidget(QLabel("Enter custom 3DCoat command:"))
        self._custom_edit = QLineEdit()
        self._custom_edit.setPlaceholderText("$MyCommand")
        custom_layout.addWidget(self._custom_edit)
        custom_layout.addWidget(QLabel("Note: Commands must start with '$'"))
        custom_layout.addStretch()
        self._tabs.addTab(custom_widget, "Custom")

        layout.addWidget(self._tabs)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_actions(self):
        """Load available actions into lists."""
        # Load LKS registered actions
        try:
            from utils.action_discovery import discover_actions
            actions_dir = Path(__file__).parent.parent / "actions"
            actions = discover_actions(actions_dir)
            for action in actions:
                item = QListWidgetItem(f"{action.display_name}")
                item.setData(Qt.UserRole, f"$LKS_{action.menu_id}")
                item.setToolTip(f"Command: $LKS_{action.menu_id}")
                self._lks_list.addItem(item)
        except Exception as e:
            print(f"[ActionPicker] Failed to load LKS actions: {e}")

        # Load common 3DCoat commands
        for cmd, display_name in COMMON_3DCOAT_COMMANDS:
            item = QListWidgetItem(f"{display_name}")
            item.setData(Qt.UserRole, cmd)
            item.setToolTip(f"Command: {cmd}")
            self._coat_list.addItem(item)

    def _filter_actions(self, text: str):
        """Filter action lists by search text."""
        text_lower = text.lower()
        for list_widget in [self._lks_list, self._coat_list]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text_lower not in item.text().lower())

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on action item."""
        self._selected_action = item.data(Qt.UserRole)
        self.accept()

    def _accept(self):
        """Handle OK button."""
        current_tab = self._tabs.currentIndex()
        if current_tab == 0:  # LKS Actions
            item = self._lks_list.currentItem()
            if item:
                self._selected_action = item.data(Qt.UserRole)
        elif current_tab == 1:  # 3DCoat Commands
            item = self._coat_list.currentItem()
            if item:
                self._selected_action = item.data(Qt.UserRole)
        elif current_tab == 2:  # Custom
            self._selected_action = self._custom_edit.text().strip()
            if self._selected_action and not self._selected_action.startswith("$"):
                self._selected_action = "$" + self._selected_action

        if self._selected_action:
            self.accept()
        else:
            QMessageBox.warning(self, "No Action Selected",
                                "Please select or enter an action.")

    def get_selected_action(self) -> str:
        """Get the selected action command."""
        return self._selected_action


# =============================================================================
# MENU ITEM EDITOR PANEL
# =============================================================================

class MenuItemEditorPanel(QGroupBox):
    """Panel for editing a single menu item's properties."""

    itemChanged = Signal()

    def __init__(self, parent=None):
        super().__init__("Item Properties", parent)
        self._current_item: QTreeWidgetItem | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        # Label
        self._label_edit = QLineEdit()
        self._label_edit.textChanged.connect(self._on_property_changed)
        layout.addRow("Label:", self._label_edit)

        # Icon picker
        icon_layout = QHBoxLayout()
        self._icon_combo = QComboBox()
        self._icon_combo.setEditable(True)
        self._icon_combo.addItems([""] + COMMON_ICONS)
        self._icon_combo.currentTextChanged.connect(self._on_property_changed)
        icon_layout.addWidget(self._icon_combo)
        layout.addRow("Icon:", icon_layout)

        # Action (3DCoat command)
        action_layout = QHBoxLayout()
        self._action_edit = QLineEdit()
        self._action_edit.setPlaceholderText("$CommandName")
        self._action_edit.textChanged.connect(self._on_property_changed)
        action_layout.addWidget(self._action_edit)
        self._pick_action_btn = QPushButton("...")
        self._pick_action_btn.setFixedWidth(30)
        self._pick_action_btn.clicked.connect(self._pick_action)
        action_layout.addWidget(self._pick_action_btn)
        layout.addRow("Action:", action_layout)

        # Angle (optional, for root items)
        self._angle_spin = QDoubleSpinBox()
        self._angle_spin.setRange(0, 360)
        self._angle_spin.setDecimals(0)
        self._angle_spin.setSpecialValueText("Auto")
        self._angle_spin.valueChanged.connect(self._on_property_changed)
        layout.addRow("Angle:", self._angle_spin)

        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description...")
        self._desc_edit.textChanged.connect(self._on_property_changed)
        layout.addRow("Description:", self._desc_edit)

        # Start disabled
        self.setEnabled(False)

    def _pick_action(self):
        """Open action picker dialog."""
        dialog = ActionPickerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            action = dialog.get_selected_action()
            self._action_edit.setText(action)

    def _on_property_changed(self):
        """Handle property change."""
        if self._current_item:
            self.itemChanged.emit()

    def set_item(self, item: QTreeWidgetItem | None):
        """Set the item to edit."""
        self._current_item = item
        self.setEnabled(item is not None)

        if item:
            data: MenuItemData = item.data(0, Qt.UserRole)
            self._label_edit.setText(data.label)
            self._icon_combo.setCurrentText(data.icon)
            self._action_edit.setText(data.action)
            self._angle_spin.setValue(
                data.angle if data.angle is not None else 0)
            self._desc_edit.setText(data.description)

    def get_data(self) -> MenuItemData | None:
        """Get current data from form."""
        if not self._current_item:
            return None

        angle = self._angle_spin.value()
        return MenuItemData(
            label=self._label_edit.text(),
            icon=self._icon_combo.currentText(),
            action=self._action_edit.text(),
            description=self._desc_edit.text(),
            angle=angle if angle > 0 else None,
        )


# =============================================================================
# MAIN EDITOR WINDOW
# =============================================================================

class RadialMenuEditorWindow(QWidget):
    """Main radial menu configuration editor window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radial Menu Editor")
        self.setMinimumSize(800, 600)

        self._config_path: Path = DEFAULT_CONFIG_PATH
        self._modified: bool = False

        self._setup_ui()
        self._load_config()

        if DARK_STYLESHEET:
            self.setStyleSheet(DARK_STYLESHEET)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        self._new_btn = QPushButton("📄 New")
        self._new_btn.clicked.connect(self._new_config)
        toolbar.addWidget(self._new_btn)

        self._load_btn = QPushButton("📂 Load")
        self._load_btn.clicked.connect(self._load_config_dialog)
        toolbar.addWidget(self._load_btn)

        self._save_btn = QPushButton("💾 Save")
        self._save_btn.clicked.connect(self._save_config)
        toolbar.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("💾 Save As...")
        self._save_as_btn.clicked.connect(self._save_config_as)
        toolbar.addWidget(self._save_as_btn)

        toolbar.addStretch()

        self._preview_btn = QPushButton("👁️ Preview")
        self._preview_btn.clicked.connect(self._preview_menu)
        toolbar.addWidget(self._preview_btn)

        main_layout.addLayout(toolbar)

        # Main content: splitter with tree and editor
        splitter = QSplitter(Qt.Horizontal)

        # Left: Menu tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        tree_label = QLabel("Menu Structure:")
        left_layout.addWidget(tree_label)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Item", "Action"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setDragDropMode(QTreeWidget.InternalMove)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        left_layout.addWidget(self._tree)

        # Tree buttons
        tree_buttons = QHBoxLayout()
        self._add_item_btn = QPushButton("➕ Add Item")
        self._add_item_btn.clicked.connect(self._add_item)
        tree_buttons.addWidget(self._add_item_btn)

        self._add_child_btn = QPushButton("➕ Add Child")
        self._add_child_btn.clicked.connect(self._add_child)
        tree_buttons.addWidget(self._add_child_btn)

        self._delete_btn = QPushButton("🗑️ Delete")
        self._delete_btn.clicked.connect(self._delete_item)
        tree_buttons.addWidget(self._delete_btn)

        left_layout.addLayout(tree_buttons)

        splitter.addWidget(left_widget)

        # Right: Item editor
        self._editor_panel = MenuItemEditorPanel()
        self._editor_panel.itemChanged.connect(self._on_item_edited)
        splitter.addWidget(self._editor_panel)

        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)

        # Status bar
        self._status_label = QLabel("Ready")
        main_layout.addWidget(self._status_label)

    def _load_config(self, path: Path | None = None):
        """Load configuration from JSON file."""
        if path is None:
            path = self._config_path

        self._tree.clear()

        if not path.exists():
            self._status_label.setText(f"Config not found: {path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            items = config.get("items", [])
            for item_data in items:
                self._add_tree_item(MenuItemData.from_dict(item_data))

            self._config_path = path
            self._modified = False
            self._status_label.setText(f"Loaded: {path.name}")
        except Exception as e:
            self._status_label.setText(f"Error loading: {e}")

    def _add_tree_item(self, data: MenuItemData, parent: QTreeWidgetItem | None = None) -> QTreeWidgetItem:
        """Add a tree item from MenuItemData."""
        display = f"{data.icon} {data.label}" if data.icon else data.label
        item = QTreeWidgetItem([display, data.action])
        item.setData(0, Qt.UserRole, data)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled |
                      Qt.ItemIsDropEnabled)

        if parent:
            parent.addChild(item)
        else:
            self._tree.addTopLevelItem(item)

        # Add children recursively
        if data.children:
            for child_data in data.children:
                self._add_tree_item(child_data, item)

        return item

    def _save_config(self):
        """Save configuration to current path."""
        self._save_config_to(self._config_path)

    def _save_config_as(self):
        """Save configuration to a new path."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration",
            str(self._config_path.parent),
            "JSON Files (*.json)"
        )
        if path:
            self._save_config_to(Path(path))

    def _save_config_to(self, path: Path):
        """Save configuration to specified path."""
        try:
            items = []
            for i in range(self._tree.topLevelItemCount()):
                items.append(self._tree_item_to_data(
                    self._tree.topLevelItem(i)))

            config = {
                "version": "1.0",
                "items": [item.to_dict() for item in items]
            }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._config_path = path
            self._modified = False
            self._status_label.setText(f"Saved: {path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")

    def _tree_item_to_data(self, item: QTreeWidgetItem) -> MenuItemData:
        """Convert tree item back to MenuItemData."""
        data: MenuItemData = item.data(0, Qt.UserRole)

        # Get children
        children = []
        for i in range(item.childCount()):
            children.append(self._tree_item_to_data(item.child(i)))

        return MenuItemData(
            label=data.label,
            icon=data.icon,
            action=data.action,
            description=data.description,
            angle=data.angle,
            children=children if children else None,
        )

    def _new_config(self):
        """Create new empty configuration."""
        if self._modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "Discard unsaved changes?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return

        self._tree.clear()
        self._modified = False
        self._status_label.setText("New configuration")

    def _load_config_dialog(self):
        """Open file dialog to load configuration."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration",
            str(self._config_path.parent),
            "JSON Files (*.json)"
        )
        if path:
            self._load_config(Path(path))

    def _on_selection_changed(self):
        """Handle tree selection change."""
        items = self._tree.selectedItems()
        if items:
            self._editor_panel.set_item(items[0])
        else:
            self._editor_panel.set_item(None)

    def _on_item_edited(self):
        """Handle item property edit."""
        items = self._tree.selectedItems()
        if not items:
            return

        item = items[0]
        data = self._editor_panel.get_data()
        if data:
            # Update tree item
            display = f"{data.icon} {data.label}" if data.icon else data.label
            item.setText(0, display)
            item.setText(1, data.action)
            item.setData(0, Qt.UserRole, data)
            self._modified = True

    def _add_item(self):
        """Add new root-level item."""
        data = MenuItemData(label="New Item")
        item = self._add_tree_item(data)
        self._tree.setCurrentItem(item)
        self._modified = True

    def _add_child(self):
        """Add child to selected item."""
        items = self._tree.selectedItems()
        if not items:
            QMessageBox.information(
                self, "No Selection", "Select a parent item first.")
            return

        parent = items[0]
        data = MenuItemData(label="New Child")
        item = self._add_tree_item(data, parent)
        parent.setExpanded(True)
        self._tree.setCurrentItem(item)
        self._modified = True

    def _delete_item(self):
        """Delete selected item."""
        items = self._tree.selectedItems()
        if not items:
            return

        item = items[0]
        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if result == QMessageBox.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self._tree.indexOfTopLevelItem(item)
                self._tree.takeTopLevelItem(index)
            self._modified = True

    def _show_context_menu(self, pos: QPoint):
        """Show context menu for tree."""
        menu = QMenu(self)
        menu.addAction("➕ Add Item", self._add_item)
        menu.addAction("➕ Add Child", self._add_child)
        menu.addSeparator()
        menu.addAction("🗑️ Delete", self._delete_item)
        menu.exec(self._tree.mapToGlobal(pos))

    def _preview_menu(self):
        """Preview the current menu configuration."""
        try:
            # Build menu items from tree
            from utils.ui.widgets.radial_menu import RadialMenuItem

            def tree_to_menu_items(parent: QTreeWidgetItem | None = None) -> list[RadialMenuItem]:
                items = []
                count = parent.childCount() if parent else self._tree.topLevelItemCount()

                for i in range(count):
                    tree_item = parent.child(
                        i) if parent else self._tree.topLevelItem(i)
                    data: MenuItemData = tree_item.data(0, Qt.UserRole)

                    # Build children recursively
                    children = None
                    if tree_item.childCount() > 0:
                        children = tree_to_menu_items(tree_item)

                    # Create action wrapper
                    action_cmd = data.action

                    def make_action(cmd: str):
                        def action():
                            print(f"[Preview] Would execute: {cmd}")
                        return action

                    menu_item = RadialMenuItem(
                        label=data.label,
                        action=make_action(action_cmd),
                        icon=data.icon or None,
                        children=children,
                        angle=data.angle,
                    )
                    items.append(menu_item)

                return items

            menu_items = tree_to_menu_items()

            if not menu_items:
                QMessageBox.information(
                    self, "No Items", "Add some menu items first.")
                return

            # Show preview
            from utils.ui.widgets.radial_menu_manager import get_manager
            manager = get_manager()
            manager.show_menu(menu_items)

        except Exception as e:
            import traceback
            QMessageBox.critical(
                self, "Preview Error", f"Failed to preview: {e}\n\n{traceback.format_exc()}")


# =============================================================================
# LAUNCH FUNCTION
# =============================================================================

def launch_editor() -> RadialMenuEditorWindow | None:
    """Launch the radial menu editor window."""
    if not HAS_QT:
        print("[RadialMenuEditor] PySide6 not available")
        return None

    editor = RadialMenuEditorWindow()
    editor.show()
    return editor


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    if DARK_STYLESHEET:
        app.setStyleSheet(DARK_STYLESHEET)

    editor = RadialMenuEditorWindow()
    editor.show()

    sys.exit(app.exec())
