"""
LKS UI - Radial Menu Editor Tab.

Tab content for editing radial menu configuration.
Integrates the RadialMenuEditorWindow content as a tab widget.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QDoubleSpinBox, QSpinBox,
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
    QMenu, QTabWidget, QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QHideEvent, QIcon

from ui.radial_menu_editor import (
    MenuItemData, ActionPickerDialog, MenuItemEditorPanel,
    DEFAULT_CONFIG_PATH, COMMON_ICONS,
    apply_tree_item_visuals,
)
from ui.radial_menu_theme import (
    TREE_ICON_SIZE,
    apply_tree_list_theme,
)
from utils.ui.widgets import SaveLoadLibrary, add_tooltip
from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
from utils.ui.styles import COLOR_ACCENT
from utils.ui.widgets.badge_button import _make_icon_from_svg
from utils.radial_menu_migrations import CURRENT_VERSION, migrate_file
from utils.radial_menu_config import (
    DEFAULT_MENU_RADIUS,
    clamp_menu_radius,
)

import json
from pathlib import Path

if TYPE_CHECKING:
    from utils.ui.widgets.radial_menu import RadialMenuItem

# =============================================================================
# LAYOUT / SIZING CONSTANTS
# =============================================================================

_BRANCH_ARROW_SCALE: float = 0.5
_TREE_COL_ITEM_W: int = 150
_TREE_BTN_W: int = 30
_TREE_BUTTON_SPACING: int = 4

# Icon accent colors
_COLOR_CHECK: str = "#81c784"
_COLOR_CANCEL: str = "#888"

# Library directory for radial menu presets
_DATA_DIR: Path = Path(__file__).parent.parent / "data"
_LIBRARY_DIR: Path = _DATA_DIR / "library" / "radial_menus"

_TT_PREVIEW = MarkdownFileResource(
    "data/tooltips/radial_menu_preview.md",
    base_dir=__file__,
)
_TT_TREE = MarkdownFileResource(
    "data/tooltips/radial_tree.md",
    base_dir=__file__,
)
_TT_LIBRARY = MarkdownFileResource(
    "data/tooltips/radial_library.md",
    base_dir=__file__,
)
_TT_TOOLBAR_ADD_ITEM = MarkdownFileResource(
    "data/tooltips/radial_toolbar_add_item.md",
    base_dir=__file__,
)
_TT_TOOLBAR_ADD_CHILD = MarkdownFileResource(
    "data/tooltips/radial_toolbar_add_child.md",
    base_dir=__file__,
)
_TT_TOOLBAR_DELETE = MarkdownFileResource(
    "data/tooltips/radial_toolbar_delete.md",
    base_dir=__file__,
)


def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


def _make_colored_icon(name: str, color: str, size: int = TREE_ICON_SIZE) -> QIcon:
    """Create a QIcon from an SVG file with currentColor replaced by color."""
    return _make_icon_from_svg(name, color=color, size=size)


# Icons for save/load buttons — pre-colored with the theme accent.
# Load uses folder_open (not the upload-style load.svg) so it reads as open/load.
_ICON_SAVE: QIcon = _make_colored_icon("save", COLOR_ACCENT)
_ICON_SAVE_AS: QIcon = _make_colored_icon("save_as", COLOR_ACCENT)
_ICON_LOAD: QIcon = _make_colored_icon("folder_open", COLOR_ACCENT)
_ICON_LOAD_LIBRARY: QIcon = _make_colored_icon("folder", COLOR_ACCENT)
_ICON_OPEN_LIBRARY_FOLDER: QIcon = _make_colored_icon("folder_open", COLOR_ACCENT)
_ICON_NEW: QIcon = _make_colored_icon("new_file", COLOR_ACCENT)
_ICON_ADD: QIcon = _make_colored_icon("add", COLOR_ACCENT)
_ICON_ADD_CHILD: QIcon = _make_colored_icon("add_child", COLOR_ACCENT)
_ICON_DELETE: QIcon = _make_colored_icon("delete", COLOR_ACCENT)
_ICON_CHECK: QIcon = _make_colored_icon("check", _COLOR_CHECK)
_ICON_CANCEL: QIcon = _make_colored_icon("cancel", _COLOR_CANCEL)
_ICON_PREVIEW: QIcon = _make_colored_icon("visibility", COLOR_ACCENT)


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
        self._preview_active: bool = False
        self._menu_label: str = ""
        self._menu_radius: int = DEFAULT_MENU_RADIUS

        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        from utils.ui.widgets.tab_container import StandardTabBody

        # Wrap self with a StandardTabBody for consistent header ribbon
        self._tab_body = StandardTabBody(
            title="Radial Menu Editor",
            info_tooltip=_load_ui_tooltip("radial_menu_tab.md"),
            parent=self,
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._tab_body)

        # All content goes into the StandardTabBody's content_layout
        main_layout = self._tab_body.content_layout

        # Title row with info button — now handled by StandardTabBody header ribbon.
        # We just add the save/load/library widget and editor content below.

        # Save/Load/Library widget
        self._save_load_widget = SaveLoadLibrary(
            library_dir=_LIBRARY_DIR,
            default_filename="radial_menu.json",
            file_extension=".json",
            on_save=self._save_to_path,
            on_load=self._load_from_path,
            on_new=self._create_new_menu,
            log_success=self._log_success,
            log_error=self._log_error,
            before_load=self._confirm_before_load,
            icons={
                "new": _ICON_NEW,
                "save": _ICON_SAVE,
                "save_as": _ICON_SAVE_AS,
                "load": _ICON_LOAD,
                "load_library": _ICON_LOAD_LIBRARY,
                "open_library_folder": _ICON_OPEN_LIBRARY_FOLDER,
            },
        )
        self._save_load_widget.saved.connect(self._on_saved)
        self._save_load_widget.loaded.connect(self._on_loaded)
        add_tooltip(self._save_load_widget, _TT_LIBRARY)
        main_layout.addWidget(self._save_load_widget)

        # Menu-level properties (apply to the whole pie, not individual items)
        props_group = QGroupBox("Menu Properties")
        props_form = QFormLayout(props_group)
        props_form.setContentsMargins(4, 4, 4, 4)
        props_form.setSpacing(4)

        self._menu_label_edit = QLineEdit()
        self._menu_label_edit.setPlaceholderText("Defaults to filename")
        self._menu_label_edit.setToolTip(
            "Center label at the pie origin. Leave empty to use the filename."
        )
        self._menu_label_edit.textChanged.connect(self._on_menu_props_changed)
        props_form.addRow("Label:", self._menu_label_edit)

        self._menu_radius_spin = QSpinBox()
        self._menu_radius_spin.setRange(50, 2000)
        self._menu_radius_spin.setSuffix(" px")
        self._menu_radius_spin.setValue(DEFAULT_MENU_RADIUS)
        self._menu_radius_spin.setToolTip(
            "Fixed pie radius. Increase to separate overlapping items "
            "(no automatic expansion)."
        )
        self._menu_radius_spin.valueChanged.connect(self._on_menu_props_changed)
        props_form.addRow("Radius:", self._menu_radius_spin)

        main_layout.addWidget(props_group)

        # Main content: splitter with tree and editor
        splitter = QSplitter(Qt.Vertical)

        # Top: Menu tree with buttons
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(_TREE_BUTTON_SPACING)

        # Hold-to-preview row — sits just above the tree view
        preview_row = QHBoxLayout()
        preview_row.setSpacing(4)
        preview_row.addStretch()
        self._preview_btn = QPushButton("Preview Radial (Hold)")
        self._preview_btn.setIcon(_ICON_PREVIEW)
        add_tooltip(self._preview_btn, _TT_PREVIEW)
        self._preview_btn.pressed.connect(self._on_preview_pressed)
        self._preview_btn.released.connect(self._on_preview_released)
        preview_row.addWidget(self._preview_btn)
        preview_row.addStretch()
        tree_layout.addLayout(preview_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Item", "Action"])
        self._tree.setColumnWidth(0, _TREE_COL_ITEM_W)
        self._tree.setDragDropMode(QTreeWidget.InternalMove)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        add_tooltip(self._tree, _TT_TREE)
        # Force light branch arrows on dark background
        from lks_utils.gui_qt.theme.dark_theme import darken_treeview
        darken_treeview(self._tree, branch_scale=_BRANCH_ARROW_SCALE)
        apply_tree_list_theme(self._tree)
        tree_layout.addWidget(self._tree)

        # Tree buttons row
        tree_buttons = QHBoxLayout()
        tree_buttons.setSpacing(4)

        self._add_item_btn = QPushButton()
        self._add_item_btn.setIcon(_ICON_ADD)
        add_tooltip(self._add_item_btn, _TT_TOOLBAR_ADD_ITEM)
        self._add_item_btn.setFixedWidth(_TREE_BTN_W)
        self._add_item_btn.clicked.connect(self._add_item)
        tree_buttons.addWidget(self._add_item_btn)

        self._add_child_btn = QPushButton()
        self._add_child_btn.setIcon(_ICON_ADD_CHILD)
        add_tooltip(self._add_child_btn, _TT_TOOLBAR_ADD_CHILD)
        self._add_child_btn.setFixedWidth(_TREE_BTN_W)
        self._add_child_btn.clicked.connect(self._add_child)
        tree_buttons.addWidget(self._add_child_btn)

        self._delete_btn = QPushButton()
        self._delete_btn.setIcon(_ICON_DELETE)
        add_tooltip(self._delete_btn, _TT_TOOLBAR_DELETE)
        self._delete_btn.setFixedWidth(_TREE_BTN_W)
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
        reg_group = QGroupBox("Install Radial Menu")
        reg_group.setToolTip(
            "Install a menu from the library so it appears in "
            "3DCoat's Scripts menu for hotkey assignment")
        reg_layout = QVBoxLayout(reg_group)
        reg_layout.setContentsMargins(4, 4, 4, 4)
        reg_layout.setSpacing(4)

        # Status label
        self._reg_status_label = QLabel("Status: Not installed")
        self._reg_status_label.setToolTip(
            "Installation status of the current menu — installed menus "
            "can have a hotkey assigned via 3DCoat Preferences")
        self._reg_status_label.setStyleSheet("color: #888;")
        reg_layout.addWidget(self._reg_status_label)

        # Install/uninstall buttons
        reg_buttons_row = QHBoxLayout()
        reg_buttons_row.setSpacing(4)

        self._register_btn = QPushButton("Install")
        self._register_btn.setIcon(_ICON_CHECK)
        self._register_btn.setToolTip(
            "Install selected library menu as a 3DCoat menu entry (assignable via hotkey)")
        self._register_btn.clicked.connect(self._register_current_menu)
        reg_buttons_row.addWidget(self._register_btn)

        self._unregister_btn = QPushButton("Uninstall")
        self._unregister_btn.setIcon(_ICON_CANCEL)
        self._unregister_btn.setToolTip(
            "Remove selected library menu from 3DCoat menus")
        self._unregister_btn.clicked.connect(self._unregister_current_menu)
        reg_buttons_row.addWidget(self._unregister_btn)

        reg_buttons_row.addStretch()
        reg_layout.addLayout(reg_buttons_row)

        main_layout.addWidget(reg_group)

        # Set initial path in SaveLoadLibrary widget
        if self._config_path.exists():
            is_library = self._config_path.parent == _LIBRARY_DIR
            self._save_load_widget.set_current_path(
                self._config_path, is_library)

    def _on_menu_props_changed(self, *_args: object) -> None:
        """Mark dirty when menu-level label/radius change."""
        self._menu_label = self._menu_label_edit.text().strip()
        self._menu_radius = int(self._menu_radius_spin.value())
        self._modified = True

    def _apply_menu_props_to_ui(
        self,
        label: str,
        radius: int,
        filename_stem: str = "",
    ) -> None:
        """Push menu-level props into the editor controls without marking dirty."""
        self._menu_label_edit.blockSignals(True)
        self._menu_radius_spin.blockSignals(True)
        self._menu_label_edit.setPlaceholderText(
            filename_stem if filename_stem else "Defaults to filename"
        )
        self._menu_label_edit.setText(label)
        self._menu_radius_spin.setValue(clamp_menu_radius(radius))
        self._menu_label = label.strip()
        self._menu_radius = clamp_menu_radius(radius)
        self._menu_label_edit.blockSignals(False)
        self._menu_radius_spin.blockSignals(False)

    def _resolved_preview_label(self) -> str:
        """Center label for preview: explicit label → filename stem → Preview."""
        if self._menu_label.strip():
            return self._menu_label.strip()
        if self._config_path is not None:
            return self._config_path.stem
        return "Preview"

    def _confirm_before_load(self) -> bool:
        """
        Guard callback invoked by SaveLoadLibrary before loading a new item.

        Returns True to proceed with the load, False to cancel.
        Prompts the user to save/discard unsaved changes when present.
        """
        if not self._modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The current menu has unsaved changes.\n\n"
            "Save before switching?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )

        if reply == QMessageBox.Cancel:
            return False

        if reply == QMessageBox.Save:
            current_path = self._save_load_widget.get_current_path()
            if current_path is None:
                # No existing path – route via Save As (returns if user cancels there)
                self._save_load_widget._on_save_as_clicked()
                # If still modified, user cancelled the Save As dialog – abort load
                if self._modified:
                    return False
            else:
                try:
                    self._save_to_path(current_path)
                    self._save_load_widget.saved.emit(current_path)
                except Exception as e:
                    self._log_error(f"Auto-save failed: {e}")
                    return False

        # Discard or successful save – proceed
        self._modified = False
        return True

    def _build_basic_menu_items(self, display_name: str) -> list[MenuItemData]:
        """Return a minimal starter radial using action/branch/list labels only."""
        _ = display_name  # name lives on the config file, not item labels
        return [
            MenuItemData(
                label="action",
                icon="🎯",
                action="",
                description="",
                angle=0.0,
                node_type="action",
            ),
            MenuItemData(
                label="action",
                icon="✨",
                action="",
                description="",
                angle=90.0,
                node_type="action",
            ),
            MenuItemData(
                label="branch",
                icon="📁",
                description="",
                angle=180.0,
                node_type="branch",
                children=[
                    MenuItemData(
                        label="action",
                        icon="▶️",
                        action="",
                        description="",
                        angle=0.0,
                        node_type="action",
                    ),
                ],
            ),
            MenuItemData(
                label="list",
                icon="📋",
                description="",
                angle=270.0,
                node_type="list",
                list_side="right",
                children=[
                    MenuItemData(
                        label="action",
                        icon="▶️",
                        action="",
                        description="",
                        angle=0.0,
                        node_type="action",
                    ),
                ],
            ),
        ]

    def _create_new_menu(self, path: Path) -> None:
        """Build a basic radial, load it into the editor, and save to path."""
        display_name: str = path.stem
        items: list[MenuItemData] = self._build_basic_menu_items(display_name)

        self._tree.clear()
        for item_data in items:
            self._add_tree_item(item_data)

        self._apply_menu_props_to_ui(
            label="",
            radius=DEFAULT_MENU_RADIUS,
            filename_stem=display_name,
        )
        self._save_to_path(path)
        self._config_path = path
        self._modified = False
        self._update_registration_status()

    def _save_to_path(self, path: Path) -> None:
        """Save configuration to specified path (called by SaveLoadLibrary)."""
        try:
            items = []
            for i in range(self._tree.topLevelItemCount()):
                items.append(self._tree_item_to_data(
                    self._tree.topLevelItem(i)))

            # Registry name defaults to filename; optional label overrides center text.
            display_name = path.stem
            label_text: str = self._menu_label_edit.text().strip()
            radius_value: int = clamp_menu_radius(self._menu_radius_spin.value())

            config: dict = {
                "version": CURRENT_VERSION,
                "name": display_name,
                "radius": radius_value,
                "items": [item.to_dict() for item in items],
            }
            if label_text:
                config["label"] = label_text

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._menu_label = label_text
            self._menu_radius = radius_value
            self._modified = False
        except Exception as e:
            raise RuntimeError(f"Save failed: {e}")

    def _load_from_path(self, path: Path) -> None:
        """Load configuration from specified path (called by SaveLoadLibrary)."""
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")

        try:
            config, _migrated = migrate_file(path, write=True)

            self._tree.clear()
            items = config.get("items", [])
            for item_data in items:
                self._add_tree_item(MenuItemData.from_dict(item_data))

            label_raw: object = config.get("label", "")
            label_text: str = (
                label_raw.strip()
                if isinstance(label_raw, str) else ""
            )
            self._apply_menu_props_to_ui(
                label=label_text,
                radius=clamp_menu_radius(
                    config.get("radius", DEFAULT_MENU_RADIUS)
                ),
                filename_stem=path.stem,
            )

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
            # Legacy config file doesn't exist yet — this is normal on first launch.
            # The library-based menu system uses individual JSON files in
            # data/library/radial_menus/ instead.  Suppress the error so the
            # user only sees the warning when a *loaded* config is missing.
            if path == DEFAULT_CONFIG_PATH:
                return
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
        """Add a tree item from MenuItemData with SVG/emoji decoration icons."""
        item = QTreeWidgetItem(["", data.action])
        item.setData(0, Qt.UserRole, data)
        apply_tree_item_visuals(item, data)
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
            node_type=data.node_type,
            list_side=data.list_side,
        )

    def _build_preview_menu_items(
        self,
        parent: QTreeWidgetItem | None = None,
    ) -> list[RadialMenuItem]:
        """Build RadialMenuItem tree from the live editor tree (actions stubbed)."""
        from utils.ui.widgets.radial_menu import RadialMenuItem

        items: list[RadialMenuItem] = []
        count: int = (
            parent.childCount() if parent is not None
            else self._tree.topLevelItemCount()
        )

        for i in range(count):
            tree_item: QTreeWidgetItem | None = (
                parent.child(i) if parent is not None
                else self._tree.topLevelItem(i)
            )
            if tree_item is None:
                continue
            data: MenuItemData | None = tree_item.data(0, Qt.UserRole)
            if data is None:
                continue

            children: list[RadialMenuItem] | None = None
            if tree_item.childCount() > 0:
                children = self._build_preview_menu_items(tree_item)

            # Fully interactive preview; never execute real actions.
            menu_item: RadialMenuItem = RadialMenuItem(
                label=data.label,
                action=lambda: None,
                icon=data.icon or None,
                children=children,
                angle=data.angle,
                is_list=(data.node_type == "list"),
                list_side=data.list_side,
            )
            items.append(menu_item)

        return items

    def _on_preview_pressed(self) -> None:
        """Show a live-tree radial preview while the Preview button is held."""
        try:
            from utils.ui.widgets.radial_menu import RadialMenuItem
            from utils.ui.widgets.radial_menu_manager import get_manager

            menu_items: list[RadialMenuItem] = self._build_preview_menu_items()
            if not menu_items:
                self._log_error("Add some menu items before previewing.")
                return

            get_manager().show_menu(
                menu_items,
                menu_name=self._resolved_preview_label(),
                menu_radius=self._menu_radius,
            )
            self._preview_active = True
        except Exception as e:
            self._preview_active = False
            self._log_error(f"Preview failed: {e}")

    def _on_preview_released(self) -> None:
        """Close the preview radial without invoking an action."""
        self._hide_preview_menu()

    def _hide_preview_menu(self) -> None:
        """Hide an active preview overlay, if any."""
        if not self._preview_active:
            return
        self._preview_active = False
        try:
            from utils.ui.widgets.radial_menu_manager import get_manager

            get_manager().hide_menu()
        except Exception as e:
            self._log_error(f"Preview hide failed: {e}")
        # Radial uses a top-level Qt.ToolTip overlay with WA_ShowWithoutActivating.
        # After dismiss, restore OS activation so QLineEdit typing works again.
        panel = self.window()
        if panel is not None:
            panel.raise_()
            panel.activateWindow()

    def hideEvent(self, event: QHideEvent) -> None:
        """Ensure a held preview cannot stick open if the tab is hidden."""
        self._hide_preview_menu()
        super().hideEvent(event)

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
            item.setData(0, Qt.UserRole, data)
            apply_tree_item_visuals(item, data)
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
        menu.addAction(_ICON_ADD, "Add Item", self._add_item)
        menu.addAction(_ICON_ADD_CHILD, "Add Child", self._add_child)
        menu.addSeparator()
        menu.addAction(_ICON_DELETE, "Delete", self._delete_item)
        menu.exec(self._tree.mapToGlobal(pos))

    # =========================================================================
    # REGISTRY INTEGRATION
    # =========================================================================

    def _update_registration_status(self) -> None:
        """Update install status label based on current file."""
        if not self._config_path:
            self._reg_status_label.setText("Status: No file loaded")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(False)
            return

        is_library = self._config_path.parent == _LIBRARY_DIR
        if not is_library:
            self._reg_status_label.setText(
                "Status: Not in library (save to library to install)")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(False)
            return

        # Check registration status
        from utils.radial_menu_registry import is_menu_registered

        menu_filename = self._config_path.name
        is_registered = is_menu_registered(menu_filename)

        if is_registered:
            scripts_name: str = f"LKS: RadialMenu_{self._config_path.stem}"
            self._reg_status_label.setText(
                f"✅ Installed as: {scripts_name}\n"
                f"Assign hotkey via: 3DCoat Preferences → Hotkeys → Scripts"
            )
            self._reg_status_label.setStyleSheet("color: #81c784;")
            self._register_btn.setEnabled(False)
            self._unregister_btn.setEnabled(True)
        else:
            self._reg_status_label.setText(
                "❌ Not installed (click Install to enable hotkey assignment)")
            self._reg_status_label.setStyleSheet("color: #888;")
            self._register_btn.setEnabled(True)
            self._unregister_btn.setEnabled(False)

    def _register_menu(self, path: Path) -> None:
        """Install a menu from library path."""
        if path.parent != _LIBRARY_DIR:
            self._log_error("Menu must be in library to install")
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
                    f"Installed: {display_name}\n"
                    f"Assign hotkey via: 3DCoat Preferences → Hotkeys → "
                    f"Scripts → LKS: RadialMenu_{display_name}"
                )
            else:
                self._log_success(f"Already installed: {display_name}")

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Install failed: {e}")

    def _register_current_menu(self) -> None:
        """Install the currently loaded menu."""
        if not self._config_path:
            self._log_error("No menu loaded")
            return

        self._register_menu(self._config_path)

    def _unregister_current_menu(self) -> None:
        """Uninstall the currently loaded menu."""
        if not self._config_path:
            self._log_error("No menu loaded")
            return

        if self._config_path.parent != _LIBRARY_DIR:
            self._log_error("Menu must be in library to uninstall")
            return

        try:
            from utils.radial_menu_registry import unregister_menu

            menu_filename = self._config_path.name
            was_unregistered = unregister_menu(menu_filename)

            if was_unregistered:
                self._log_success(
                    f"Uninstalled: {menu_filename}\n"
                    f"Restart 3DCoat if the Scripts entry still shows "
                    f"(disk/live mismatch). Sync All is on the Install tab."
                )
            else:
                self._log_error(f"Not installed: {menu_filename}")

            self._update_registration_status()

        except Exception as e:
            self._log_error(f"Uninstall failed: {e}")

