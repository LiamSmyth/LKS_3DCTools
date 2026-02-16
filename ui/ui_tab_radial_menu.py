"""
LKS UI - Radial Menu Editor Tab.

Tab content for editing radial menu configuration.
Integrates the RadialMenuEditorWindow content as a tab widget.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QDoubleSpinBox,
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
    QMenu, QTabWidget, QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QPoint

from ui.radial_menu_editor import (
    MenuItemData, ActionPickerDialog, MenuItemEditorPanel,
    DEFAULT_CONFIG_PATH, COMMON_ICONS,
)
from utils.ui.widgets import SaveLoadLibrary

import json
from pathlib import Path

# Library directory for radial menu presets
_DATA_DIR: Path = Path(__file__).parent.parent / "data"
_LIBRARY_DIR: Path = _DATA_DIR / "library" / "radial_menus"


# =============================================================================
# TAB FACTORY
# =============================================================================

def create_radial_menu_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
) -> QWidget:
    """
    Create the Radial Menu editor tab.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages

    Returns:
        QWidget containing the radial menu editor
    """
    return RadialMenuEditorTab(log_success, log_error)


# =============================================================================
# EDITOR TAB
# =============================================================================

class RadialMenuEditorTab(QWidget):
    """Radial Menu editor as a panel tab."""

    def __init__(
        self,
        log_success: Callable[[str], None],
        log_error: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._log_success = log_success
        self._log_error = log_error
        self._config_path: Path = DEFAULT_CONFIG_PATH
        self._modified: bool = False

        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Title
        title_label = QLabel("Radial Menu Editor")
        title_label.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #90caf9; padding: 4px;"
        )
        main_layout.addWidget(title_label)

        # Save/Load/Library widget
        self._save_load_widget = SaveLoadLibrary(
            library_dir=_LIBRARY_DIR,
            default_filename="radial_menu.json",
            file_extension=".json",
            on_save=self._save_to_path,
            on_load=self._load_from_path,
            log_success=self._log_success,
            log_error=self._log_error,
        )
        self._save_load_widget.saved.connect(self._on_saved)
        self._save_load_widget.loaded.connect(self._on_loaded)
        main_layout.addWidget(self._save_load_widget)

        # Main content: splitter with tree and editor
        splitter = QSplitter(Qt.Vertical)

        # Top: Menu tree with buttons
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(4)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Item", "Action"])
        self._tree.setColumnWidth(0, 150)
        self._tree.setDragDropMode(QTreeWidget.InternalMove)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        tree_layout.addWidget(self._tree)

        # Tree buttons row
        tree_buttons = QHBoxLayout()
        tree_buttons.setSpacing(4)

        self._add_item_btn = QPushButton("➕")
        self._add_item_btn.setToolTip("Add root item")
        self._add_item_btn.setFixedWidth(30)
        self._add_item_btn.clicked.connect(self._add_item)
        tree_buttons.addWidget(self._add_item_btn)

        self._add_child_btn = QPushButton("➕📁")
        self._add_child_btn.setToolTip("Add child to selected")
        self._add_child_btn.setFixedWidth(40)
        self._add_child_btn.clicked.connect(self._add_child)
        tree_buttons.addWidget(self._add_child_btn)

        self._delete_btn = QPushButton("🗑️")
        self._delete_btn.setToolTip("Delete selected")
        self._delete_btn.setFixedWidth(30)
        self._delete_btn.clicked.connect(self._delete_item)
        tree_buttons.addWidget(self._delete_btn)

        tree_buttons.addStretch()
        tree_layout.addLayout(tree_buttons)

        splitter.addWidget(tree_widget)

        # Bottom: Item editor panel
        self._editor_panel = MenuItemEditorPanel()
        self._editor_panel.itemChanged.connect(self._on_item_edited)
        splitter.addWidget(self._editor_panel)

        splitter.setSizes([200, 150])
        main_layout.addWidget(splitter)

        # Registration controls (at bottom)
        reg_group = QGroupBox("Hotkey Registration")
        reg_layout = QVBoxLayout(reg_group)
        reg_layout.setContentsMargins(4, 4, 4, 4)
        reg_layout.setSpacing(4)

        # Status label
        self._reg_status_label = QLabel("Status: Not registered")
        self._reg_status_label.setStyleSheet("color: #888;")
        reg_layout.addWidget(self._reg_status_label)

        # Register/unregister buttons
        reg_buttons_row = QHBoxLayout()
        reg_buttons_row.setSpacing(4)

        self._register_btn = QPushButton("✅ Register")
        self._register_btn.setToolTip(
            "Register selected library menu as hotkey-mappable action")
        self._register_btn.clicked.connect(self._register_current_menu)
        reg_buttons_row.addWidget(self._register_btn)

        self._unregister_btn = QPushButton("❌ Unregister")
        self._unregister_btn.setToolTip(
            "Unregister selected library menu")
        self._unregister_btn.clicked.connect(self._unregister_current_menu)
        reg_buttons_row.addWidget(self._unregister_btn)

        self._unregister_all_btn = QPushButton("🗑️ Unregister All")
        self._unregister_all_btn.setToolTip(
            "Unregister all radial menus (requires 3DCoat restart to take effect)")
        self._unregister_all_btn.clicked.connect(self._unregister_all_menus)
        reg_buttons_row.addWidget(self._unregister_all_btn)

        reg_buttons_row.addStretch()
        reg_layout.addLayout(reg_buttons_row)

        main_layout.addWidget(reg_group)

        # About Hotkeys help menu (at bottom)
        from utils.ui.widgets import HelpMenu
        help_menu = HelpMenu(
            title="Hotkeys",
            content=(
                "<b>How to create a hotkey-mapped radial menu:</b><br/><br/>"
                "<b>1. Create the menu:</b><br/>"
                "   • Use the editor below to design your radial menu structure<br/>"
                "   • Add items, set icons, and configure actions<br/><br/>"
                "<b>2. Save to library:</b><br/>"
                "   • Click 💾 Save and choose 'Library' as the save location<br/>"
                "   • Give your menu a descriptive name<br/><br/>"
                "<b>3. Register for hotkey mapping:</b><br/>"
                "   • Select your menu from the library dropdown<br/>"
                "   • Click ✅ Register<br/>"
                "   • Restart 3DCoat<br/><br/>"
                "<b>4. Assign a shortcut:</b><br/>"
                "   • In 3DCoat: Scripts menu → Find your menu by name<br/>"
                "   • Hover over the menu item and press your desired shortcut key<br/>"
                "   • The hotkey will be saved automatically<br/><br/>"
                "<b>To unregister an individual menu:</b><br/>"
                "   • Select it from the library dropdown<br/>"
                "   • Click ❌ Unregister<br/>"
                "   • Restart 3DCoat to remove it from the Scripts menu"
            ),
            max_height=200
        )
        main_layout.addWidget(help_menu)

        # Set initial path in SaveLoadLibrary widget
        if self._config_path.exists():
            is_library = self._config_path.parent == _LIBRARY_DIR
            self._save_load_widget.set_current_path(
                self._config_path, is_library)

    def _save_to_path(self, path: Path) -> None:
        """Save configuration to specified path (called by SaveLoadLibrary)."""
        try:
            items = []
            for i in range(self._tree.topLevelItemCount()):
                items.append(self._tree_item_to_data(
                    self._tree.topLevelItem(i)))

            # Extract display name from path (remove .json extension)
            display_name = path.stem

            config = {
                "version": "1.0",
                "name": display_name,  # Add name field for registry
                "items": [item.to_dict() for item in items]
            }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._modified = False
        except Exception as e:
            raise RuntimeError(f"Save failed: {e}")

    def _load_from_path(self, path: Path) -> None:
        """Load configuration from specified path (called by SaveLoadLibrary)."""
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self._tree.clear()
            items = config.get("items", [])
            for item_data in items:
                self._add_tree_item(MenuItemData.from_dict(item_data))

            self._modified = False
        except Exception as e:
            raise RuntimeError(f"Load failed: {e}")

    def _on_saved(self, path: Path) -> None:
        """Handle successful save (update internal state)."""
        self._config_path = path
        self._update_registration_status()

    def _on_loaded(self, path: Path) -> None:
        """Handle successful load (update internal state)."""
        self._config_path = path
        self._update_registration_status()

    def _load_config(self, path: Path | None = None) -> None:
        """Load configuration from JSON file (legacy method for initial load)."""
        if path is None:
            path = self._config_path

        if not path.exists():
            self._log_error(f"Config not found: {path.name}")
            return

        try:
            self._load_from_path(path)
            self._config_path = path

            # Update SaveLoadLibrary widget
            is_library = path.parent == _LIBRARY_DIR
            self._save_load_widget.set_current_path(path, is_library)

            self._log_success(f"Loaded: {path.name}")
        except Exception as e:
            self._log_error(f"Error loading: {e}")

    def _add_tree_item(
        self,
        data: MenuItemData,
        parent: QTreeWidgetItem | None = None
    ) -> QTreeWidgetItem:
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

    # Note: _save_config removed - now handled by SaveLoadLibrary widget via _save_to_path

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

    def _on_selection_changed(self) -> None:
        """Handle tree selection change."""
        items = self._tree.selectedItems()
        if items:
            self._editor_panel.set_item(items[0])
        else:
            self._editor_panel.set_item(None)

    def _on_item_edited(self) -> None:
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

    def _add_item(self) -> None:
        """Add new root-level item."""
        data = MenuItemData(label="New Item")
        item = self._add_tree_item(data)
        self._tree.setCurrentItem(item)
        self._modified = True

    def _add_child(self) -> None:
        """Add child to selected item."""
        items = self._tree.selectedItems()
        if not items:
            self._log_error("Select a parent item first")
            return

        parent = items[0]
        data = MenuItemData(label="New Child")
        item = self._add_tree_item(data, parent)
        parent.setExpanded(True)
        self._tree.setCurrentItem(item)
        self._modified = True

    def _delete_item(self) -> None:
        """Delete selected item."""
        items = self._tree.selectedItems()
        if not items:
            return

        item = items[0]
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self._tree.indexOfTopLevelItem(item)
            self._tree.takeTopLevelItem(index)
        self._modified = True
        self._log_success("Item deleted")

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show context menu for tree."""
        menu = QMenu(self)
        menu.addAction("➕ Add Item", self._add_item)
        menu.addAction("➕ Add Child", self._add_child)
        menu.addSeparator()
        menu.addAction("🗑️ Delete", self._delete_item)
        menu.exec(self._tree.mapToGlobal(pos))

    # =========================================================================
    # REGISTRY INTEGRATION
    # =========================================================================

    def _update_registration_status(self) -> None:
        """Update registration status label based on current file."""
        if not self._config_path:
            self._reg_status_label.setText("Status: No file loaded")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(False)
            return

        is_library = self._config_path.parent == _LIBRARY_DIR
        if not is_library:
            self._reg_status_label.setText(
                "Status: Not in library (save to library to register)")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(False)
            return

        # Check registration status
        from utils.radial_menu_registry import is_menu_registered, generate_menu_id

        menu_filename = self._config_path.name
        is_registered = is_menu_registered(menu_filename)

        if is_registered:
            menu_id = generate_menu_id(menu_filename)
            self._reg_status_label.setText(
                f"✅ Registered as: {menu_id}\n"
                f"Assign hotkey via: 3DCoat Preferences → Hotkeys → Scripts"
            )
            self._reg_status_label.setStyleSheet("color: #81c784;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(True)
        else:
            self._reg_status_label.setText(
                "❌ Not registered (click Register to enable hotkey assignment)")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(True)
            self._unregister_btn.setEnabled(False)

    def _register_menu(self, path: Path) -> None:
        """Register a menu from library path."""
        if path.parent != _LIBRARY_DIR:
            self._log_error("Menu must be in library to register")
            return

        try:
            from utils.radial_menu_registry import register_menu

            menu_filename = path.name

            # Extract display name from config
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                display_name = config_data.get("name", menu_filename[:-5])
            except Exception:
                display_name = menu_filename[:-5]

            # Register
            was_registered = register_menu(menu_filename, display_name)

            if was_registered:
                self._log_success(
                    f"Registered: {display_name}\n"
                    f"Assign hotkey via: 3DCoat Preferences → Hotkeys → Scripts → Radial: {display_name}"
                )
            else:
                self._log_success(f"Already registered: {display_name}")

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Registration failed: {e}")

    def _register_current_menu(self) -> None:
        """Register the currently loaded menu."""
        if not self._config_path:
            self._log_error("No menu loaded")
            return

        self._register_menu(self._config_path)

    def _unregister_current_menu(self) -> None:
        """Unregister the currently loaded menu."""
        if not self._config_path:
            self._log_error("No menu loaded")
            return

        if self._config_path.parent != _LIBRARY_DIR:
            self._log_error("Menu must be in library to unregister")
            return

        try:
            from utils.radial_menu_registry import unregister_menu

            menu_filename = self._config_path.name
            was_unregistered = unregister_menu(menu_filename)

            if was_unregistered:
                self._log_success(
                    f"Unregistered: {menu_filename}\n"
                    f"Note: Menu item persists in Scripts menu until 3DCoat restart"
                )
            else:
                self._log_error(f"Not registered: {menu_filename}")

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Unregistration failed: {e}")

    def _sync_all_menus(self) -> None:
        """Sync all library menus with registration state."""
        try:
            from utils.radial_menu_registry import sync_all_menus

            registered, unregistered, updated = sync_all_menus()

            self._log_success(
                f"Sync complete:\n"
                f"  Registered: {registered}\n"
                f"  Unregistered: {unregistered}\n"
                f"  Updated: {updated}"
            )

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Sync failed: {e}")

    def _unregister_all_menus(self) -> None:
        """Unregister all radial menus."""
        try:
            from PySide6.QtWidgets import QMessageBox
            
            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Unregister All Menus",
                "⚠️ This will unregister ALL radial menus.\n\n"
                "You will need to restart 3DCoat for the changes to take effect.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                self._log_success("Unregister all cancelled")
                return

            from utils.radial_menu_registry import unregister_all_menus

            count = unregister_all_menus()

            if count > 0:
                self._log_success(
                    f"Unregistered {count} menus\n"
                    f"Note: Restart 3DCoat for changes to take effect"
                )
            else:
                self._log_success("No menus were registered")

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Unregister all failed: {e}")
