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

        # Registration controls
        reg_group = QGroupBox("Hotkey Registration")
        reg_layout = QVBoxLayout(reg_group)
        reg_layout.setContentsMargins(4, 4, 4, 4)
        reg_layout.setSpacing(4)

        # Status label
        self._reg_status_label = QLabel("Status: Not registered")
        self._reg_status_label.setStyleSheet("color: #888;")
        reg_layout.addWidget(self._reg_status_label)

        # Description
        desc = QLabel(
            "Register this menu as an action to assign hotkeys via 3DCoat Preferences.\n"
            "Auto-register saves to library and registers immediately."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaa; font-size: 10pt;")
        reg_layout.addWidget(desc)

        # Auto-register checkbox
        self._auto_register_checkbox = QCheckBox("Auto-register when saving to library")
        self._auto_register_checkbox.setChecked(True)
        self._auto_register_checkbox.setToolTip(
            "Automatically register menu as hotkey-mappable action when saving to library"
        )
        reg_layout.addWidget(self._auto_register_checkbox)

        # Manual register/unregister buttons
        reg_buttons_row = QHBoxLayout()
        reg_buttons_row.setSpacing(4)

        self._register_btn = QPushButton("✅ Register")
        self._register_btn.setToolTip("Register current menu as hotkey-mappable action")
        self._register_btn.clicked.connect(self._register_current_menu)
        reg_buttons_row.addWidget(self._register_btn)

        self._unregister_btn = QPushButton("❌ Unregister")
        self._unregister_btn.setToolTip("Unregister menu (remove from Scripts menu)")
        self._unregister_btn.clicked.connect(self._unregister_current_menu)
        reg_buttons_row.addWidget(self._unregister_btn)

        self._sync_all_btn = QPushButton("🔄 Sync All")
        self._sync_all_btn.setToolTip("Sync all library menus with registration state")
        self._sync_all_btn.clicked.connect(self._sync_all_menus)
        reg_buttons_row.addWidget(self._sync_all_btn)

        reg_buttons_row.addStretch()
        reg_layout.addLayout(reg_buttons_row)

        main_layout.addWidget(reg_group)

        # Preview button
        preview_row = QHBoxLayout()
        preview_row.setSpacing(4)

        preview_row.addStretch()

        self._preview_btn = QPushButton("👁️ Preview")
        self._preview_btn.setToolTip("Preview current menu configuration")
        self._preview_btn.clicked.connect(self._preview_menu)
        preview_row.addWidget(self._preview_btn)

        main_layout.addLayout(preview_row)

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

            config = {
                "version": "1.0",
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
        """Handle successful save (update internal state and register if needed)."""
        self._config_path = path
        
        # Auto-register if enabled and saved to library
        if self._auto_register_checkbox.isChecked():
            is_library = path.parent == _LIBRARY_DIR
            if is_library:
                self._register_menu(path)
        
        # Update registration status
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

    def _preview_menu(self) -> None:
        """Preview the current menu configuration."""
        try:
            # Build menu items from tree
            from utils.ui.widgets.radial_menu import RadialMenuItem

            def tree_to_menu_items(
                parent: QTreeWidgetItem | None = None
            ) -> list[RadialMenuItem]:
                items = []
                count = (
                    parent.childCount() if parent
                    else self._tree.topLevelItemCount()
                )

                for i in range(count):
                    tree_item = (
                        parent.child(i) if parent
                        else self._tree.topLevelItem(i)
                    )
                    data: MenuItemData = tree_item.data(0, Qt.UserRole)

                    # Build children recursively
                    children = None
                    if tree_item.childCount() > 0:
                        children = tree_to_menu_items(tree_item)

                    # Create action wrapper that actually executes the command
                    action_cmd = data.action

                    def make_action(cmd: str):
                        def action():
                            if cmd.startswith("$"):
                                try:
                                    import coat
                                    coat.ui.cmd(cmd)
                                    self._log_success(f"Executed: {cmd}")
                                except Exception as e:
                                    self._log_error(f"Failed: {cmd} - {e}")
                            else:
                                self._log_success(f"Preview: {cmd}")
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
                self._log_error("Add some menu items first")
                return

            # Show preview
            from utils.ui.widgets.radial_menu_manager import get_manager
            manager = get_manager()
            manager.show_menu(menu_items)
            self._log_success("Preview opened (release key to close)")

        except Exception as e:
            import traceback
            self._log_error(f"Preview failed: {e}")
            traceback.print_exc()

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
            self._reg_status_label.setText("Status: Not in library (save to library to register)")
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
            self._reg_status_label.setText("❌ Not registered (click Register to enable hotkey assignment)")
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
