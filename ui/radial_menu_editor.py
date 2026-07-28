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

from utils.radial_menu_migrations import CURRENT_VERSION, migrate_file
from utils.ui.widgets import add_tooltip
from utils.ui.widgets.markdown_file_resource import MarkdownFileResource

try:
    from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
        QPushButton, QLineEdit, QLabel, QSpinBox, QDoubleSpinBox,
        QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QSplitter,
        QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QApplication,
        QMenu, QInputDialog, QTabWidget, QTextEdit
    )
    from PySide6.QtGui import QAction, QIcon, QDrag, QHideEvent
    from lks_utils.gui_qt.widgets.q_dial_enum_picker import QDialEnumPicker
    from lks_utils.gui_qt.widgets.dial_enum_option import DialEnumOption
    from lks_utils.gui_qt.widgets.svg_icon_picker import QSvgIconPicker
    from utils.ui.widgets.badge_button import _make_icon_from_svg

    try:
        from utils.ui.styles import COLOR_ACCENT
    except ImportError:
        COLOR_ACCENT = "#90caf9"

    def _make_colored_icon(name: str, color: str, size: int = 16) -> QIcon:
        """Render an SVG asset to a coloured QIcon (toolbar / tree decoration)."""
        return _make_icon_from_svg(name, color=color, size=size)

    from ui.radial_menu_theme import TREE_ICON_SIZE

    _ICON_SAVE_RADIAL = _make_colored_icon('save', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_SAVE_AS_RADIAL = _make_colored_icon('save_as', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_NEW_FILE = _make_colored_icon('new_file', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_LOAD = _make_colored_icon('folder_open', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_PREVIEW = _make_colored_icon('visibility', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_ADD = _make_colored_icon('add', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_ADD_CHILD = _make_colored_icon('add_child', COLOR_ACCENT, TREE_ICON_SIZE)
    _ICON_DELETE = _make_colored_icon('delete', COLOR_ACCENT, TREE_ICON_SIZE)

    HAS_QT = True
except ImportError:
    HAS_QT = False
    COLOR_ACCENT = "#90caf9"
    TREE_ICON_SIZE = 24
    QHideEvent = object  # type: ignore[misc,assignment]

    def _make_colored_icon(name: str, color: str, size: int = 16) -> QIcon:  # type: ignore[misc]
        raise RuntimeError("Qt not available")

    _ICON_ADD_CHILD = None  # type: ignore[assignment]

# Try to import styles
try:
    from utils.ui.styles import DARK_STYLESHEET
except ImportError:
    DARK_STYLESHEET = ""

try:
    from ui.radial_menu_theme import (
        TREE_ICON_SIZE,
        apply_action_list_theme,
        apply_tree_item_row_hint,
        apply_tree_list_theme,
        emoji_to_icon,
        transparent_placeholder_icon,
    )
except ImportError:
    apply_action_list_theme = None  # type: ignore[assignment]
    apply_tree_item_row_hint = None  # type: ignore[assignment]
    apply_tree_list_theme = None  # type: ignore[assignment]

    def emoji_to_icon(emoji: str, size: int | None = None) -> QIcon:  # type: ignore[misc]
        return QIcon()

    def transparent_placeholder_icon(size: int | None = None) -> QIcon:  # type: ignore[misc]
        return QIcon()


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================

_BRANCH_ARROW_SCALE: float = 0.5
_WIN_MIN_W: int = 800
_WIN_MIN_H: int = 600
_TREE_COL_ITEM_W: int = 200
_SPLITTER_LEFT: int = 400
_SPLITTER_RIGHT: int = 400
_PICKER_MIN_W: int = 500
_PICKER_MIN_H: int = 400
_PICK_BTN_W: int = 30
_ENUM_PICKER_W: int = 150
_ENUM_PICKER_H: int = 22

# Tooltip resources (ui/data/tooltips/)
_TT_ITEM_LABEL = MarkdownFileResource(
    "data/tooltips/radial_item_label.md", base_dir=__file__
)
_TT_ITEM_ICON = MarkdownFileResource(
    "data/tooltips/radial_item_icon.md", base_dir=__file__
)
_TT_ITEM_TYPE = MarkdownFileResource(
    "data/tooltips/radial_item_type.md", base_dir=__file__
)
_TT_ITEM_ACTION = MarkdownFileResource(
    "data/tooltips/radial_item_action.md", base_dir=__file__
)
_TT_ITEM_ANGLE = MarkdownFileResource(
    "data/tooltips/radial_item_angle.md", base_dir=__file__
)
_TT_ITEM_SIDE = MarkdownFileResource(
    "data/tooltips/radial_item_side.md", base_dir=__file__
)
_TT_ITEM_DESC = MarkdownFileResource(
    "data/tooltips/radial_item_description.md", base_dir=__file__
)
_TT_TOOLBAR_NEW = MarkdownFileResource(
    "data/tooltips/radial_toolbar_new.md", base_dir=__file__
)
_TT_TOOLBAR_LOAD = MarkdownFileResource(
    "data/tooltips/radial_toolbar_load.md", base_dir=__file__
)
_TT_TOOLBAR_SAVE = MarkdownFileResource(
    "data/tooltips/radial_toolbar_save.md", base_dir=__file__
)
_TT_TOOLBAR_SAVE_AS = MarkdownFileResource(
    "data/tooltips/radial_toolbar_save_as.md", base_dir=__file__
)
_TT_TOOLBAR_PREVIEW = MarkdownFileResource(
    "data/tooltips/radial_menu_preview.md", base_dir=__file__
)
_TT_TOOLBAR_ADD_ITEM = MarkdownFileResource(
    "data/tooltips/radial_toolbar_add_item.md", base_dir=__file__
)
_TT_TOOLBAR_ADD_CHILD = MarkdownFileResource(
    "data/tooltips/radial_toolbar_add_child.md", base_dir=__file__
)
_TT_TOOLBAR_DELETE = MarkdownFileResource(
    "data/tooltips/radial_toolbar_delete.md", base_dir=__file__
)
_TT_TREE = MarkdownFileResource(
    "data/tooltips/radial_tree.md", base_dir=__file__
)


# =============================================================================
# HELPERS
# =============================================================================

def _is_svg_icon(icon_str: str) -> bool:
    """Return True if *icon_str* is an SVG filename or path (case-insensitive)."""
    return bool(icon_str and Path(icon_str).suffix.lower() == ".svg")


def _svg_basename(icon_str: str) -> str:
    """Return SVG stem (``visibility.svg`` / full path → ``visibility``)."""
    return Path(icon_str).stem


def tree_display_text(data: MenuItemData) -> str:
    """Label-only tree text — icons always go in the decoration column."""
    return data.label


def render_tree_item_icon(icon_str: str) -> QIcon:
    """Return a fixed-size decoration icon for a tree row.

    Always returns a ``TREE_ICON_SIZE`` pixmap (SVG, emoji, or transparent
    placeholder) so siblings share the same text column.
    """
    if not icon_str:
        return transparent_placeholder_icon(TREE_ICON_SIZE)
    if _is_svg_icon(icon_str):
        try:
            icon: QIcon = _make_colored_icon(
                _svg_basename(icon_str), COLOR_ACCENT, TREE_ICON_SIZE)
            if not icon.isNull():
                return icon
        except Exception:
            pass
        return transparent_placeholder_icon(TREE_ICON_SIZE)
    return emoji_to_icon(icon_str, TREE_ICON_SIZE)


def apply_tree_item_visuals(item: QTreeWidgetItem, data: MenuItemData) -> None:
    """Set label text, decoration icon, and row height for a tree item."""
    item.setText(0, tree_display_text(data))
    item.setText(1, data.action)
    item.setIcon(0, render_tree_item_icon(data.icon))
    if apply_tree_item_row_hint is not None:
        apply_tree_item_row_hint(item)

# =============================================================================
# CONSTANTS
# =============================================================================

# Default config path (in data/state/ folder)
_DATA_DIR: Path = Path(__file__).parent.parent / "data"
_STATE_DIR: Path = _DATA_DIR / "state"
DEFAULT_CONFIG_PATH: Path = _STATE_DIR / "radial_menu_config.json"

# Common 3DCoat commands that users might want to map
COMMON_3DCOAT_COMMANDS: list[tuple[str, str]] = [
    # Ghost/Visibility
    ("$Toggle_ghosting", "Toggle Ghost (Native)"),
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

# Valid node types for serialization
_NODE_TYPES: tuple[str, str, str] = ("action", "branch", "list")


@dataclass
class MenuItemData:
    """Data for a single menu item.

    Node types:
        ``action`` — ring item that invokes a 3DCoat command (has action, no children).
        ``branch`` — ring item that opens a submenu (has children, no direct action).
        ``list``   — list panel displayed beside the ring (has children, no direct action).
    """
    label: str
    icon: str = ""
    action: str = ""  # 3DCoat command like "$CommandName" (only for 'action' type)
    description: str = ""
    angle: float | None = None
    children: list[MenuItemData] | None = None
    node_type: str = "action"  # "action", "branch", or "list"
    list_side: str = "right"   # "left" or "right" (only meaningful for list nodes)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        data = {"label": self.label}
        # Always serialise the type so the config is self-describing.
        data["type"] = self.node_type
        if self.node_type == "list":
            data["side"] = self.list_side
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
    def _infer_node_type(cls, raw_type: str, data: dict) -> str:
        """Resolve the canonical node type with backward compatibility.

        Old formats: ``"list"`` and ``"leaf"`` → ``"list"``, absent/empty → inferred.
        """
        if raw_type in ("list", "leaf"):
            return "list"
        if raw_type in _NODE_TYPES:
            return raw_type
        # Legacy config with no explicit type — infer from structure.
        if data.get("children"):
            return "branch"
        return "action"

    @classmethod
    def from_dict(cls, data: dict) -> MenuItemData:
        """Create from dict (parsed JSON)."""
        children = None
        if "children" in data:
            children = [cls.from_dict(c) for c in data["children"]]
        raw_type: str = data.get("type", "")
        node_type: str = cls._infer_node_type(raw_type, data)
        return cls(
            label=data["label"],
            icon=data.get("icon", ""),
            action=data.get("action", ""),
            description=data.get("description", ""),
            angle=data.get("angle"),
            children=children,
            node_type=node_type,
            list_side=data.get("side", "right"),
        )


# =============================================================================
# ACTION PICKER DIALOG
# =============================================================================

class ActionPickerDialog(QDialog):
    """Dialog for picking an action (3DCoat command or LKS action)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick Action")
        self.setMinimumSize(_PICKER_MIN_W, _PICKER_MIN_H)
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
        if apply_action_list_theme is not None:
            apply_action_list_theme(self._lks_list)
        self._tabs.addTab(self._lks_list, "LKS Actions")

        # Tab 2: Common 3DCoat Commands
        self._coat_list = QListWidget()
        self._coat_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        if apply_action_list_theme is not None:
            apply_action_list_theme(self._coat_list)
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
        add_tooltip(self._label_edit, _TT_ITEM_LABEL)
        layout.addRow("Label:", self._label_edit)

        # Icon picker (SVG-based with visual preview)
        icon_layout = QHBoxLayout()
        _svg_dir = Path(__file__).resolve().parent.parent / "utils" / "ui" / "data"
        self._icon_combo = QSvgIconPicker(
            svg_directory=str(_svg_dir),
            parent=self,
        )
        self._icon_combo.currentValueChanged.connect(self._on_icon_changed)
        add_tooltip(self._icon_combo, _TT_ITEM_ICON)
        icon_layout.addWidget(self._icon_combo)
        layout.addRow("Icon:", icon_layout)

        # Node type: Action / Branch / List
        self._type_values: list[str] = ["action", "branch", "list"]
        self._type_combo = QDialEnumPicker(
            options=[
                DialEnumOption(value="action", label="Action"),
                DialEnumOption(value="branch", label="Branch"),
                DialEnumOption(value="list", label="List"),
            ],
            current_index=0,
            width=_ENUM_PICKER_W,
            height=_ENUM_PICKER_H,
        )
        self._type_combo.current_index_changed.connect(lambda idx: self._on_type_changed(idx))
        add_tooltip(self._type_combo, _TT_ITEM_TYPE)
        layout.addRow("Type:", self._type_combo)

        # Action (3DCoat command)
        action_layout = QHBoxLayout()
        self._action_edit = QLineEdit()
        self._action_edit.setPlaceholderText("$CommandName")
        self._action_edit.textChanged.connect(self._on_property_changed)
        add_tooltip(self._action_edit, _TT_ITEM_ACTION)
        action_layout.addWidget(self._action_edit)
        self._pick_action_btn = QPushButton("...")
        self._pick_action_btn.setFixedWidth(_PICK_BTN_W)
        self._pick_action_btn.clicked.connect(self._pick_action)
        add_tooltip(self._pick_action_btn, _TT_ITEM_ACTION)
        action_layout.addWidget(self._pick_action_btn)
        self._action_label_row: int = layout.rowCount()  # track for label lookup
        layout.addRow("Action:", action_layout)

        # Angle (optional, for root items)
        self._angle_spin = QDoubleSpinBox()
        self._angle_spin.setRange(0, 360)
        self._angle_spin.setDecimals(0)
        self._angle_spin.setSpecialValueText("Auto")
        self._angle_spin.valueChanged.connect(self._on_property_changed)
        add_tooltip(self._angle_spin, _TT_ITEM_ANGLE)
        self._angle_label_row: int = layout.rowCount()
        layout.addRow("Angle:", self._angle_spin)

        # Side (only for list type)
        self._side_combo = QDialEnumPicker(
            options=[
                DialEnumOption(value="right", label="Right"),
                DialEnumOption(value="left", label="Left"),
            ],
            current_index=0,
            width=_ENUM_PICKER_W,
            height=_ENUM_PICKER_H,
        )
        self._side_combo.current_index_changed.connect(lambda idx: self._on_property_changed())
        add_tooltip(self._side_combo, _TT_ITEM_SIDE)
        self._side_label_row: int = layout.rowCount()
        layout.addRow("Side:", self._side_combo)

        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description...")
        self._desc_edit.textChanged.connect(self._on_property_changed)
        add_tooltip(self._desc_edit, _TT_ITEM_DESC)
        layout.addRow("Description:", self._desc_edit)

        # Start disabled
        self.setEnabled(False)

        # Initial state: default "Action" type — side hidden
        self._side_combo.setVisible(False)
        self._set_row_visible(layout, self._side_label_row, False)

    def _on_type_changed(self, index: int) -> None:
        """Handle type combo change.

        ``action`` → action + angle enabled, side hidden.
        ``branch`` → action disabled (branches don't invoke commands),
                      angle enabled, side hidden.
        ``list``   → action + angle disabled, side visible.
        """
        node_type: str = self._type_combo.current_value()
        is_action: bool = (node_type == "action")
        is_list: bool = (node_type == "list")

        self._action_edit.setEnabled(is_action)
        self._pick_action_btn.setEnabled(is_action)
        self._angle_spin.setEnabled(not is_list)
        self._side_combo.setVisible(is_list)
        self._set_row_visible(self.layout(), self._side_label_row, is_list)
        self._on_property_changed()

    @staticmethod
    def _set_row_visible(layout: QFormLayout, row: int, visible: bool) -> None:
        """Show/hide a form row by its row index."""
        if 0 <= row < layout.rowCount():
            label_item = layout.itemAt(row, QFormLayout.LabelRole)
            field_item = layout.itemAt(row, QFormLayout.FieldRole)
            if label_item and label_item.widget():
                label_item.widget().setVisible(visible)
            if field_item and field_item.widget():
                field_item.widget().setVisible(visible)

    def _pick_action(self):
        """Open action picker dialog."""
        dialog = ActionPickerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            action = dialog.get_selected_action()
            self._action_edit.setText(action)

    def _on_icon_changed(self, path: str) -> None:
        """Handle icon selection change.
        
        Clear the QSvgIconPicker button text for SVG icons so only the
        rendered pixmap shows — the filename text is redundant visual noise.
        """
        if _is_svg_icon(path):
            self._icon_combo._button.setText("")
        self._on_property_changed()

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

            # Type value → index lookup
            type_idx: int = self._type_values.index(data.node_type) if data.node_type in self._type_values else 0

            # Side value → index lookup
            side_values: list[str] = ["right", "left"]
            side: str = data.list_side or "right"
            side_idx: int = side_values.index(side) if side in side_values else 0

            self._label_edit.setText(data.label)
            self._icon_combo.setCurrentSvgPath(data.icon)
            # Clear button text for SVG icons — icon renders as pixmap
            if _is_svg_icon(data.icon):
                self._icon_combo._button.setText("")
            self._action_edit.setText(data.action)
            self._angle_spin.setValue(
                data.angle if data.angle is not None else 0)
            self._desc_edit.setText(data.description)

            self._type_combo.set_current_index(type_idx)
            is_action: bool = (data.node_type == "action")
            is_list: bool = (data.node_type == "list")
            self._side_combo.setVisible(is_list)
            self._set_row_visible(self.layout(), self._side_label_row, is_list)
            self._side_combo.set_current_index(side_idx)
            self._action_edit.setEnabled(is_action)
            self._pick_action_btn.setEnabled(is_action)
            self._angle_spin.setEnabled(not is_list)

    def get_data(self) -> MenuItemData | None:
        """Get current data from form."""
        if not self._current_item:
            return None

        angle = self._angle_spin.value()
        node_type: str = self._type_combo.current_value()
        list_side: str = self._side_combo.current_value()
        return MenuItemData(
            label=self._label_edit.text(),
            icon=self._icon_combo.currentSvgPath(),
            action=self._action_edit.text(),
            description=self._desc_edit.text(),
            angle=angle if angle > 0 else None,
            node_type=node_type,
            list_side=list_side,
        )


# =============================================================================
# MAIN EDITOR WINDOW
# =============================================================================

class RadialMenuEditorWindow(QWidget):
    """Main radial menu configuration editor window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radial Menu Editor")
        self.setMinimumSize(_WIN_MIN_W, _WIN_MIN_H)

        self._config_path: Path = DEFAULT_CONFIG_PATH
        self._modified: bool = False
        self._preview_active: bool = False

        # Apply dark stylesheet BEFORE building UI so child tree widgets
        # inherit the (stripped) branch rules from the cascade.
        if DARK_STYLESHEET:
            self.setStyleSheet(DARK_STYLESHEET)

        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        self._new_btn = QPushButton("New")
        self._new_btn.setIcon(_ICON_NEW_FILE)
        add_tooltip(self._new_btn, _TT_TOOLBAR_NEW)
        self._new_btn.clicked.connect(self._new_config)
        toolbar.addWidget(self._new_btn)

        self._load_btn = QPushButton("Load")
        self._load_btn.setIcon(_ICON_LOAD)
        add_tooltip(self._load_btn, _TT_TOOLBAR_LOAD)
        self._load_btn.clicked.connect(self._load_config_dialog)
        toolbar.addWidget(self._load_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.setIcon(_ICON_SAVE_RADIAL)
        add_tooltip(self._save_btn, _TT_TOOLBAR_SAVE)
        self._save_btn.clicked.connect(self._save_config)
        toolbar.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("Save As...")
        self._save_as_btn.setIcon(_ICON_SAVE_AS_RADIAL)
        add_tooltip(self._save_as_btn, _TT_TOOLBAR_SAVE_AS)
        self._save_as_btn.clicked.connect(self._save_config_as)
        toolbar.addWidget(self._save_as_btn)

        toolbar.addStretch()

        self._preview_btn = QPushButton("Preview Radial (Hold)")
        self._preview_btn.setIcon(_ICON_PREVIEW)
        add_tooltip(self._preview_btn, _TT_TOOLBAR_PREVIEW)
        self._preview_btn.pressed.connect(self._on_preview_pressed)
        self._preview_btn.released.connect(self._on_preview_released)
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
        # Theme after darken_treeview (API sizing only — no tree QSS).
        if apply_tree_list_theme is not None:
            apply_tree_list_theme(self._tree)

        left_layout.addWidget(self._tree)

        # Tree buttons
        tree_buttons = QHBoxLayout()
        self._add_item_btn = QPushButton("Add Item")
        self._add_item_btn.setIcon(_ICON_ADD)
        add_tooltip(self._add_item_btn, _TT_TOOLBAR_ADD_ITEM)
        self._add_item_btn.clicked.connect(self._add_item)
        tree_buttons.addWidget(self._add_item_btn)

        self._add_child_btn = QPushButton("Add Child")
        add_child_icon: QIcon = _ICON_ADD_CHILD if _ICON_ADD_CHILD is not None else _ICON_ADD
        self._add_child_btn.setIcon(add_child_icon)
        add_tooltip(self._add_child_btn, _TT_TOOLBAR_ADD_CHILD)
        self._add_child_btn.clicked.connect(self._add_child)
        tree_buttons.addWidget(self._add_child_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setIcon(_ICON_DELETE)
        add_tooltip(self._delete_btn, _TT_TOOLBAR_DELETE)
        self._delete_btn.clicked.connect(self._delete_item)
        tree_buttons.addWidget(self._delete_btn)

        left_layout.addLayout(tree_buttons)

        splitter.addWidget(left_widget)

        # Right: Item editor
        self._editor_panel = MenuItemEditorPanel()
        self._editor_panel.itemChanged.connect(self._on_item_edited)
        splitter.addWidget(self._editor_panel)

        splitter.setSizes([_SPLITTER_LEFT, _SPLITTER_RIGHT])
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
            config, _migrated = migrate_file(path, write=True)

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
                "version": CURRENT_VERSION,
                "name": path.stem,
                "radius": 128,
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
            node_type=data.node_type,
            list_side=data.list_side,
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
            item.setData(0, Qt.UserRole, data)
            apply_tree_item_visuals(item, data)
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
        add_child_icon: QIcon = _ICON_ADD_CHILD if _ICON_ADD_CHILD is not None else _ICON_ADD
        menu.addAction(_ICON_ADD, "Add Item", self._add_item)
        menu.addAction(add_child_icon, "Add Child", self._add_child)
        menu.addSeparator()
        menu.addAction(_ICON_DELETE, "Delete", self._delete_item)
        menu.exec(self._tree.mapToGlobal(pos))

    def _build_preview_menu_items(
        self,
        parent: QTreeWidgetItem | None = None,
    ) -> list:
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
            from utils.ui.widgets.radial_menu_manager import get_manager

            menu_items = self._build_preview_menu_items()
            if not menu_items:
                QMessageBox.information(
                    self, "No Items", "Add some menu items first.")
                return

            get_manager().show_menu(
                menu_items,
                menu_name=self._config_path.stem if self._config_path else "Preview",
            )
            self._preview_active = True
            self._status_label.setText("Preview active (release to close)")
        except Exception as e:
            self._preview_active = False
            import traceback
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to preview: {e}\n\n{traceback.format_exc()}",
            )

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
            self._status_label.setText(f"Preview hide failed: {e}")
            return
        self.raise_()
        self.activateWindow()
        self._status_label.setText("Ready")

    def hideEvent(self, event: QHideEvent) -> None:
        """Ensure a held preview cannot stick open if the window is hidden."""
        self._hide_preview_menu()
        super().hideEvent(event)

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
