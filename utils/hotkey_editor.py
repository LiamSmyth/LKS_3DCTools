"""
Hotkey Editor - A Qt-based editor for 3DCoat hotkeys.

Provides a visual editor for managing, cleaning, and fixing 3DCoat hotkey bindings.
Can be launched standalone from terminal or from the LKS Tools panel.

Features:
- View all hotkey entries in a sortable table
- Filter by room, command name, or binding
- Highlight duplicates, conflicts, and orphan rooms
- One-click cleanup operations (remove duplicates, fix conflicts)
- Versioned backup management
- Search/filter capabilities

Usage:
    # From terminal (standalone, for testing outside 3DCoat):
    python utils/hotkey_editor.py
    python utils/hotkey_editor.py "C:/path/to/Options_Hotkeys.xml"
    
    # From LKS panel (inside 3DCoat):
    from utils.hotkey_editor import launch_hotkey_editor
    launch_hotkey_editor()
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, TYPE_CHECKING

try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QComboBox,
        QTreeWidget,
        QTreeWidgetItem,
        QHeaderView,
        QMessageBox,
        QFileDialog,
        QStatusBar,
        QFrame,
        QSplitter,
        QMenu,
        QDialog,
        QDialogButtonBox,
        QGroupBox,
        QScrollArea,
        QListWidget,
        QListWidgetItem,
        QFormLayout,
        QRadioButton,
        QButtonGroup,
        QCheckBox,
    )
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QBrush, QAction, QKeySequence

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False
    QMainWindow = object  # Fallback for type hints

# =============================================================================
# FLEXIBLE IMPORT: Works both inside 3DCoat and standalone
# =============================================================================
# When running standalone (outside 3DCoat), utils/__init__.py imports coat
# which doesn't exist. We handle this by importing hotkey_utils directly.

# Detect if running inside 3DCoat's embedded Python
RUNNING_IN_3DCOAT: bool = False
try:
    import coat
    RUNNING_IN_3DCOAT = True
except ImportError:
    pass

try:
    # Try the normal import path (works inside 3DCoat)
    from utils.hotkey_utils import (
        HotkeyEntry,
        HotkeysFile,
        HotkeyStats,
        VALID_ROOMS,
        parse_hotkeys_file,
        validate_all,
        remove_duplicates,
        remove_orphan_rooms,
        create_backup,
        list_backups,
        restore_backup,
        save_hotkeys_file,
        get_stats,
        discover_hotkeys_path,
    )
except (ImportError, ModuleNotFoundError):
    # Standalone mode: import from same directory
    # This happens when coat module is not available
    import importlib.util
    _hotkey_utils_path = Path(__file__).parent / "hotkey_utils.py"
    _spec = importlib.util.spec_from_file_location(
        "hotkey_utils", _hotkey_utils_path)
    _hotkey_utils = importlib.util.module_from_spec(_spec)
    sys.modules["hotkey_utils"] = _hotkey_utils
    _spec.loader.exec_module(_hotkey_utils)

    HotkeyEntry = _hotkey_utils.HotkeyEntry
    HotkeysFile = _hotkey_utils.HotkeysFile
    HotkeyStats = _hotkey_utils.HotkeyStats
    VALID_ROOMS = _hotkey_utils.VALID_ROOMS
    parse_hotkeys_file = _hotkey_utils.parse_hotkeys_file
    validate_all = _hotkey_utils.validate_all
    remove_duplicates = _hotkey_utils.remove_duplicates
    remove_orphan_rooms = _hotkey_utils.remove_orphan_rooms
    create_backup = _hotkey_utils.create_backup
    list_backups = _hotkey_utils.list_backups
    restore_backup = _hotkey_utils.restore_backup
    save_hotkeys_file = _hotkey_utils.save_hotkeys_file
    get_stats = _hotkey_utils.get_stats
    discover_hotkeys_path = _hotkey_utils.discover_hotkeys_path


# =============================================================================
# CONSTANTS
# =============================================================================

# Table column indices
COL_COMMAND: int = 0
COL_KEY: int = 1
COL_MODIFIERS: int = 2
COL_ROOM: int = 3
COL_STATUS: int = 4
COL_USER_DEF: int = 5
COL_STACKABLE: int = 6

# Garbage key defaults (intentional "disabled" mapping)
# Some 3DCoat shortcuts can't be unmapped - they respawn with defaults
# Mapping to a garbage key is the only way to disable them
DEFAULT_GARBAGE_KEY: str = "END"
DEFAULT_GARBAGE_CTRL: bool = True
DEFAULT_GARBAGE_ALT: bool = False
DEFAULT_GARBAGE_SHIFT: bool = False

# Status colors
COLOR_DUPLICATE: str = "#ef5350"  # Red
COLOR_CONFLICT: str = "#ffb74d"   # Orange
COLOR_ORPHAN: str = "#ce93d8"     # Purple
COLOR_NORMAL: str = "#e0e0e0"     # Default gray
COLOR_UNASSIGNED: str = "#666666"  # Dim gray
COLOR_GARBAGE: str = "#78909c"    # Blue-gray (intentionally disabled)

# Status icons
ICON_DUPLICATE: str = "⊗"  # Duplicate
ICON_CONFLICT: str = "⚡"   # Conflict
ICON_ORPHAN: str = "?"     # Orphan room
ICON_GARBAGE: str = "🗑️"   # Garbage key (soft disabled)
ICON_OK: str = ""          # No issues


# =============================================================================
# STYLESHEET (extends base LKS style)
# =============================================================================

EDITOR_STYLESHEET: str = """
QMainWindow {
    background-color: #2b2b2b;
}

QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11px;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #90caf9;
}

QPushButton:pressed {
    background-color: #353535;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QPushButton#dangerBtn {
    border-color: #ef5350;
}

QPushButton#dangerBtn:hover {
    background-color: #5a3030;
    border-color: #ff6659;
}

QPushButton#successBtn {
    border-color: #81c784;
}

QPushButton#successBtn:hover {
    background-color: #305030;
    border-color: #a5d6a7;
}

QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
}

QLineEdit:focus {
    border-color: #90caf9;
}

QComboBox {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #90caf9;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    selection-background-color: #264f78;
}

QTreeWidget {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    alternate-background-color: #252525;
    gridline-color: #333333;
}

QTreeWidget::item {
    padding: 2px 4px;
    border: none;
}

QTreeWidget::item:selected {
    background-color: #264f78;
}

QTreeWidget::item:hover {
    background-color: #3a3a3a;
}

QHeaderView::section {
    background-color: #383838;
    color: #e0e0e0;
    padding: 6px 4px;
    border: 1px solid #555555;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #404040;
}

QStatusBar {
    background-color: #252525;
    color: #888888;
    border-top: 1px solid #555555;
}

QFrame#separator {
    background-color: #555555;
    max-height: 1px;
    min-height: 1px;
}

QLabel#sectionHeader {
    color: #90caf9;
    font-weight: bold;
    font-size: 12px;
}

QLabel#statsLabel {
    color: #888888;
    font-size: 10px;
}

QLabel#issueLabel {
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
}

QLabel#issueLabel[issue="duplicate"] {
    background-color: #5a2020;
    color: #ef5350;
}

QLabel#issueLabel[issue="conflict"] {
    background-color: #5a4020;
    color: #ffb74d;
}

QLabel#issueLabel[issue="orphan"] {
    background-color: #402050;
    color: #ce93d8;
}

QDialog {
    background-color: #2b2b2b;
}

QGroupBox {
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 12px;
    padding: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #90caf9;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #264f78;
}

QRadioButton {
    spacing: 6px;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
}
"""


# =============================================================================
# EDITOR WINDOW
# =============================================================================

if HAS_QT:

    class HotkeyEditorWindow(QMainWindow):
        """
        Main window for the Hotkey Editor.

        Provides a visual interface for viewing, filtering, and cleaning
        3DCoat hotkey bindings.
        """

        def __init__(
            self,
            hotkeys_path: Path | None = None,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)

            self._hotkeys_path: Path | None = hotkeys_path
            self._hotkeys_file: HotkeysFile | None = None
            self._filtered_entries: list[HotkeyEntry] = []

            # Garbage key settings (for "soft disabling" unmappable shortcuts)
            self._garbage_key: str = DEFAULT_GARBAGE_KEY
            self._garbage_ctrl: bool = DEFAULT_GARBAGE_CTRL
            self._garbage_alt: bool = DEFAULT_GARBAGE_ALT
            self._garbage_shift: bool = DEFAULT_GARBAGE_SHIFT

            self._setup_window()
            self._build_ui()

            # Show warning if running inside 3DCoat
            if RUNNING_IN_3DCOAT:
                self._show_3dcoat_warning()
            # Center on screen
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    (geo.width() - self.width()) // 2,
                    (geo.height() - self.height()) // 2,
                )

        def _show_3dcoat_warning(self) -> None:
            """Show warning about editing while 3DCoat is running."""
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Warning: Running Inside 3DCoat")
            msg.setText(
                "<h3>⚠️ Changes Will Be Lost When 3DCoat Exits</h3>"
            )
            msg.setInformativeText(
                "<p>3DCoat saves its in-memory hotkey state when it closes, "
                "which will <b>overwrite any edits you make here</b>.</p>"
                "<p><b>To preserve your changes:</b></p>"
                "<ol>"
                "<li>Close 3DCoat completely</li>"
                "<li>Run the editor standalone (outside 3DCoat)</li>"
                "<li>Make your edits and save</li>"
                "<li>Reopen 3DCoat</li>"
                "</ol>"
                "<p><b>Standalone Launch:</b><br>"
                f"<code>python {Path(__file__).name}</code></p>"
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)

            # Add "Copy Command" button
            copy_btn = msg.addButton(
                "📋 Copy Standalone Command", QMessageBox.ActionRole)
            copy_btn.clicked.connect(self._copy_standalone_command)

            msg.exec()

        def _copy_standalone_command(self) -> None:
            """Copy standalone launch command to clipboard."""
            # Get Python executable path
            python_exe = sys.executable
            editor_path = Path(__file__).absolute()

            # Build command
            cmd = f'"{python_exe}" "{editor_path}"'

            clipboard = QApplication.clipboard()
            clipboard.setText(cmd)

            QMessageBox.information(
                self,
                "Command Copied",
                f"Standalone launch command copied to clipboard:\n\n{cmd}\n\n"
                "Paste this in your terminal after closing 3DCoat."
            )

        def _setup_window(self) -> None:
            """Configure window properties."""
            self.setWindowTitle(
                "3DCoat Hotkey Editor" +
                (" ⚠️ RUNNING IN 3DCOAT - Changes will be lost!" if RUNNING_IN_3DCOAT else "")
            )
            self.setMinimumSize(800, 600)
            self.resize(1000, 700)
            self.setStyleSheet(EDITOR_STYLESHEET)

        def _build_ui(self) -> None:
            """Build the main UI layout."""
            central = QWidget()
            self.setCentralWidget(central)

            layout = QVBoxLayout(central)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(8)

            # --- Warning banner if running in 3DCoat ---
            if RUNNING_IN_3DCOAT:
                warning_banner = self._create_warning_banner()
                layout.addWidget(warning_banner)

            # --- Header with file controls ---
            layout.addWidget(self._create_file_controls())

            # --- Filter bar ---
            layout.addWidget(self._create_filter_bar())

            # --- Main content (table + stats) ---
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self._create_table())
            splitter.addWidget(self._create_sidebar())
            splitter.setSizes([700, 300])
            layout.addWidget(splitter, 1)

            # --- Status bar ---
            self._status_bar = QStatusBar()
            self.setStatusBar(self._status_bar)
            self._status_bar.showMessage("No file loaded")

        def _create_warning_banner(self) -> QWidget:
            """Create warning banner for in-3DCoat editing."""
            banner = QFrame()
            banner.setObjectName("warningBanner")
            banner.setStyleSheet("""
                QFrame#warningBanner {
                    background-color: #5a3030;
                    border: 2px solid #ef5350;
                    border-radius: 6px;
                    padding: 8px;
                }
                QLabel {
                    color: #ffcdd2;
                }
                QPushButton {
                    background-color: #ef5350;
                    border: none;
                    padding: 4px 12px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #ff6659;
                }
            """)

            layout = QHBoxLayout(banner)
            layout.setContentsMargins(8, 8, 8, 8)

            icon_label = QLabel("⚠️")
            icon_label.setStyleSheet("font-size: 24px;")
            layout.addWidget(icon_label)

            text_label = QLabel(
                "<b>WARNING:</b> Changes will be lost when 3DCoat exits. "
                "Close 3DCoat and run standalone for persistent edits."
            )
            text_label.setWordWrap(True)
            layout.addWidget(text_label, 1)

            copy_btn = QPushButton("📋 Copy Standalone Command")
            copy_btn.clicked.connect(self._copy_standalone_command)
            layout.addWidget(copy_btn)

            return banner

        def _create_file_controls(self) -> QWidget:
            """Create file open/save/backup controls."""
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            # File path label
            self._file_label = QLabel("No file loaded")
            self._file_label.setStyleSheet("color: #888;")
            layout.addWidget(self._file_label, 1)

            # Open button
            btn_open = QPushButton("📂 Open")
            btn_open.setToolTip("Open hotkeys file")
            btn_open.clicked.connect(self._on_open_file)
            layout.addWidget(btn_open)

            # Auto-detect button
            btn_detect = QPushButton("🔍 Auto-Detect")
            btn_detect.setToolTip("Find hotkeys file automatically")
            btn_detect.clicked.connect(self._on_auto_detect)
            layout.addWidget(btn_detect)

            # Save button
            btn_save = QPushButton("💾 Save")
            btn_save.setObjectName("successBtn")
            btn_save.setToolTip("Save changes (creates backup first)")
            btn_save.clicked.connect(self._on_save)
            layout.addWidget(btn_save)

            # Reload button
            btn_reload = QPushButton("🔄 Reload")
            btn_reload.setToolTip("Reload file from disk")
            btn_reload.clicked.connect(self._on_reload)
            layout.addWidget(btn_reload)

            return container

        def _create_filter_bar(self) -> QWidget:
            """Create search/filter controls."""
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            # Search input
            layout.addWidget(QLabel("Search:"))
            self._search_input = QLineEdit()
            self._search_input.setPlaceholderText("Filter by command name...")
            self._search_input.textChanged.connect(self._on_filter_changed)
            layout.addWidget(self._search_input, 1)

            # Room filter
            layout.addWidget(QLabel("Room:"))
            self._room_combo = QComboBox()
            self._room_combo.addItem("(All Rooms)", "")
            self._room_combo.currentIndexChanged.connect(
                self._on_filter_changed)
            layout.addWidget(self._room_combo)

            # Issues filter
            layout.addWidget(QLabel("Show:"))
            self._issues_combo = QComboBox()
            self._issues_combo.addItem("All Entries", "all")
            self._issues_combo.addItem("Assigned Only", "assigned")
            self._issues_combo.addItem("Issues Only", "issues")
            self._issues_combo.addItem("Duplicates", "duplicates")
            self._issues_combo.addItem("Conflicts", "conflicts")
            self._issues_combo.addItem("Orphan Rooms", "orphans")
            self._issues_combo.currentIndexChanged.connect(
                self._on_filter_changed)
            layout.addWidget(self._issues_combo)

            return container

        def _create_table(self) -> QWidget:
            """Create the main hotkey table."""
            self._table = QTreeWidget()
            self._table.setAlternatingRowColors(True)
            self._table.setRootIsDecorated(False)
            self._table.setSortingEnabled(True)
            self._table.setSelectionMode(QTreeWidget.ExtendedSelection)

            # Enable context menu
            self._table.setContextMenuPolicy(Qt.CustomContextMenu)
            self._table.customContextMenuRequested.connect(
                self._on_table_context_menu)

            # Enable double-click editing
            self._table.itemDoubleClicked.connect(self._on_cell_double_click)

            # Columns
            self._table.setHeaderLabels([
                "Command", "Key", "Modifiers", "Room", "Status", "User", "Stack"
            ])

            # Column sizing - Interactive allows user to resize
            header = self._table.header()
            header.setSectionResizeMode(COL_COMMAND, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_KEY, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_MODIFIERS, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_ROOM, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_STATUS, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_USER_DEF, QHeaderView.Interactive)
            header.setSectionResizeMode(COL_STACKABLE, QHeaderView.Interactive)
            header.setStretchLastSection(False)

            # Set initial column widths
            header.resizeSection(COL_COMMAND, 300)
            header.resizeSection(COL_KEY, 80)
            header.resizeSection(COL_MODIFIERS, 100)
            header.resizeSection(COL_ROOM, 100)
            header.resizeSection(COL_STATUS, 60)
            header.resizeSection(COL_USER_DEF, 50)
            header.resizeSection(COL_STACKABLE, 50)

            return self._table

        def _create_sidebar(self) -> QWidget:
            """Create the sidebar with stats and actions."""
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)

            # --- Statistics Section ---
            stats_header = QLabel("📊 Statistics")
            stats_header.setObjectName("sectionHeader")
            layout.addWidget(stats_header)

            self._stats_label = QLabel("No file loaded")
            self._stats_label.setObjectName("statsLabel")
            self._stats_label.setWordWrap(True)
            layout.addWidget(self._stats_label)

            # Separator
            sep1 = QFrame()
            sep1.setObjectName("separator")
            sep1.setFrameShape(QFrame.HLine)
            layout.addWidget(sep1)

            # --- Issues Summary ---
            issues_header = QLabel("⚠️ Issues")
            issues_header.setObjectName("sectionHeader")
            layout.addWidget(issues_header)

            self._issues_container = QWidget()
            self._issues_layout = QVBoxLayout(self._issues_container)
            self._issues_layout.setContentsMargins(0, 0, 0, 0)
            self._issues_layout.setSpacing(4)
            layout.addWidget(self._issues_container)

            # Separator
            sep2 = QFrame()
            sep2.setObjectName("separator")
            sep2.setFrameShape(QFrame.HLine)
            layout.addWidget(sep2)

            # --- Cleanup Actions ---
            actions_header = QLabel("🧹 Cleanup Actions")
            actions_header.setObjectName("sectionHeader")
            layout.addWidget(actions_header)

            btn_remove_dups = QPushButton("Remove Duplicates")
            btn_remove_dups.setObjectName("dangerBtn")
            btn_remove_dups.setToolTip("Remove exact duplicate entries")
            btn_remove_dups.clicked.connect(self._on_remove_duplicates)
            layout.addWidget(btn_remove_dups)

            btn_remove_orphans = QPushButton("Remove Orphan Rooms")
            btn_remove_orphans.setObjectName("dangerBtn")
            btn_remove_orphans.setToolTip(
                "Remove entries with invalid room names")
            btn_remove_orphans.clicked.connect(self._on_remove_orphans)
            layout.addWidget(btn_remove_orphans)

            btn_remove_unassigned = QPushButton("Remove Unassigned")
            btn_remove_unassigned.setObjectName("dangerBtn")
            btn_remove_unassigned.setToolTip(
                "Remove entries with no hotkey binding (uninvokable)")
            btn_remove_unassigned.clicked.connect(self._on_remove_unassigned)
            layout.addWidget(btn_remove_unassigned)

            btn_resolve_conflicts = QPushButton("⚡ Resolve Conflicts...")
            btn_resolve_conflicts.setObjectName("dangerBtn")
            btn_resolve_conflicts.setToolTip(
                "Open dialog to resolve hotkey conflicts one by one")
            btn_resolve_conflicts.clicked.connect(self._on_resolve_conflicts)
            layout.addWidget(btn_resolve_conflicts)

            # Separator
            sep3 = QFrame()
            sep3.setObjectName("separator")
            sep3.setFrameShape(QFrame.HLine)
            layout.addWidget(sep3)

            # --- Garbage Key Config ---
            garbage_header = QLabel("🗑️ Garbage Key")
            garbage_header.setObjectName("sectionHeader")
            layout.addWidget(garbage_header)

            self._garbage_label = QLabel(
                f"{self._garbage_key}\n"
                f"{'Ctrl+' if self._garbage_ctrl else ''}"
                f"{'Alt+' if self._garbage_alt else ''}"
                f"{'Shift+' if self._garbage_shift else ''}"
            )
            self._garbage_label.setObjectName("statsLabel")
            self._garbage_label.setWordWrap(True)
            layout.addWidget(self._garbage_label)

            btn_config_garbage = QPushButton("⚙️ Configure...")
            btn_config_garbage.setToolTip(
                "Configure the garbage key combo for 'soft disabling' unmappable shortcuts"
            )
            btn_config_garbage.clicked.connect(self._on_configure_garbage_key)
            layout.addWidget(btn_config_garbage)

            # Separator
            sep4 = QFrame()
            sep4.setObjectName("separator")
            sep4.setFrameShape(QFrame.HLine)
            layout.addWidget(sep4)

            # --- Backup Management ---
            backup_header = QLabel("💾 Backups")
            backup_header.setObjectName("sectionHeader")
            layout.addWidget(backup_header)

            btn_create_backup = QPushButton("Create Backup")
            btn_create_backup.setToolTip("Create a manual backup now")
            btn_create_backup.clicked.connect(self._on_create_backup)
            layout.addWidget(btn_create_backup)

            btn_restore_backup = QPushButton("Restore Backup...")
            btn_restore_backup.setToolTip("Restore from a previous backup")
            btn_restore_backup.clicked.connect(self._on_restore_backup)
            layout.addWidget(btn_restore_backup)

            self._backup_count_label = QLabel("0 backups available")
            self._backup_count_label.setObjectName("statsLabel")
            layout.addWidget(self._backup_count_label)

            layout.addStretch()

            return container

        # =====================================================================
        # FILE OPERATIONS
        # =====================================================================

        def _load_file(self, path: Path) -> None:
            """Load a hotkeys file."""
            self._hotkeys_path = path
            self._hotkeys_file = parse_hotkeys_file(path)

            if self._hotkeys_file.parse_errors:
                QMessageBox.warning(
                    self,
                    "Parse Errors",
                    f"Some errors occurred while parsing:\n\n" +
                    "\n".join(self._hotkeys_file.parse_errors[:5])
                )

            # Run validation
            validate_all(self._hotkeys_file)

            # Update UI
            self._file_label.setText(str(path))
            self._file_label.setStyleSheet("color: #81c784;")
            self._update_room_filter()
            self._update_table()
            self._update_stats()
            self._update_backup_count()

            self._status_bar.showMessage(
                f"Loaded {len(self._hotkeys_file.entries)} entries from {path.name}"
            )

        def _on_open_file(self) -> None:
            """Handle open file button."""
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Hotkeys File",
                str(Path.home() / "Documents"),
                "XML Files (*.xml);;All Files (*)"
            )
            if path:
                self._load_file(Path(path))

        def _on_auto_detect(self) -> None:
            """Try to auto-detect the hotkeys file."""
            path = discover_hotkeys_path()
            if path:
                self._load_file(path)
            else:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    "Could not find Options_Hotkeys.xml.\n\n"
                    "Try opening the file manually."
                )

        def _on_save(self) -> None:
            """Save the current file."""
            if not self._hotkeys_file:
                return

            reply = QMessageBox.question(
                self,
                "Save Changes",
                "Save changes to hotkeys file?\n\n"
                "A backup will be created automatically.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                try:
                    backup_path = save_hotkeys_file(self._hotkeys_file)
                    self._update_backup_count()
                    self._status_bar.showMessage(
                        f"Saved! Backup: {backup_path.name if backup_path else 'none'}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save: {e}")

        def _on_reload(self) -> None:
            """Reload the current file from disk."""
            if self._hotkeys_path:
                self._load_file(self._hotkeys_path)

        # =====================================================================
        # FILTERING
        # =====================================================================

        def _update_room_filter(self) -> None:
            """Update the room filter combo with available rooms."""
            self._room_combo.blockSignals(True)
            self._room_combo.clear()
            self._room_combo.addItem("(All Rooms)", "")

            if self._hotkeys_file:
                rooms = sorted(self._hotkeys_file.get_unique_rooms())
                for room in rooms:
                    display = room if room else "(Global)"
                    self._room_combo.addItem(display, room)

            self._room_combo.blockSignals(False)

        def _on_filter_changed(self) -> None:
            """Handle filter changes."""
            self._update_table()

        def _get_filtered_entries(self) -> list[HotkeyEntry]:
            """Get entries matching current filters."""
            if not self._hotkeys_file:
                return []

            entries = self._hotkeys_file.entries

            # Search filter
            search = self._search_input.text().lower().strip()
            if search:
                entries = [e for e in entries if search in e.id.lower()]

            # Room filter
            room_filter = self._room_combo.currentData()
            if room_filter is not None and room_filter != "":
                entries = [e for e in entries if e.room == room_filter]
            elif self._room_combo.currentIndex() > 0:
                # "(Global)" selected - filter for empty room
                selected_room = self._room_combo.currentData()
                if selected_room == "":
                    entries = [e for e in entries if e.room == ""]

            # Issues filter
            issues_filter = self._issues_combo.currentData()
            if issues_filter == "assigned":
                entries = [e for e in entries if e.is_assigned]
            elif issues_filter == "issues":
                entries = [e for e in entries if e.has_issues()]
            elif issues_filter == "duplicates":
                entries = [e for e in entries if e.is_duplicate]
            elif issues_filter == "conflicts":
                entries = [e for e in entries if len(e.conflict_ids) > 0]
            elif issues_filter == "orphans":
                entries = [e for e in entries if e.is_orphan_room]

            return entries

        # =====================================================================
        # TABLE UPDATES
        # =====================================================================

        def _update_table(self) -> None:
            """Rebuild the table with filtered entries."""
            self._table.clear()

            entries = self._get_filtered_entries()
            self._filtered_entries = entries

            for entry in entries:
                item = QTreeWidgetItem()

                # Command
                item.setText(COL_COMMAND, entry.id)

                # Key
                item.setText(
                    COL_KEY, entry.code if entry.is_assigned else "[None]")

                # Modifiers
                item.setText(COL_MODIFIERS, entry.modifier_string or "[None]")

                # Room
                item.setText(COL_ROOM, entry.display_room)

                # Status
                status_parts: list[str] = []
                is_garbage = self._is_garbage_key(entry)
                if is_garbage:
                    status_parts.append(ICON_GARBAGE)
                if entry.is_duplicate:
                    status_parts.append(ICON_DUPLICATE)
                if entry.conflict_ids:
                    status_parts.append(ICON_CONFLICT)
                if entry.is_orphan_room:
                    status_parts.append(ICON_ORPHAN)
                item.setText(COL_STATUS, " ".join(status_parts))

                # User defined
                item.setText(
                    COL_USER_DEF, "✓" if entry.user_defined > 0 else "")

                # Stackable
                item.setText(
                    COL_STACKABLE, "✓" if entry.allow_stack else "")

                # Coloring based on issues
                if is_garbage:
                    self._set_row_color(item, COLOR_GARBAGE)
                elif entry.is_duplicate:
                    self._set_row_color(item, COLOR_DUPLICATE)
                elif entry.conflict_ids:
                    self._set_row_color(item, COLOR_CONFLICT)
                elif entry.is_orphan_room:
                    self._set_row_color(item, COLOR_ORPHAN)
                elif not entry.is_assigned:
                    self._set_row_color(item, COLOR_UNASSIGNED)

                # Store entry reference
                item.setData(COL_COMMAND, Qt.UserRole, entry)

                self._table.addTopLevelItem(item)

            # Update status bar
            total = len(
                self._hotkeys_file.entries) if self._hotkeys_file else 0
            shown = len(entries)
            self._status_bar.showMessage(f"Showing {shown} of {total} entries")

        def _is_garbage_key(self, entry: HotkeyEntry) -> bool:
            """Check if entry is mapped to the garbage key combination."""
            return (
                entry.code == self._garbage_key and
                entry.ctrl == self._garbage_ctrl and
                entry.alt == self._garbage_alt and
                entry.shift == self._garbage_shift
            )

        def _set_row_color(self, item: QTreeWidgetItem, color: str) -> None:
            """Set the text color for all columns in a row."""
            brush = QBrush(QColor(color))
            for col in range(item.columnCount()):
                item.setForeground(col, brush)

        # =====================================================================
        # STATS & ISSUES
        # =====================================================================

        def _update_stats(self) -> None:
            """Update the statistics display."""
            if not self._hotkeys_file:
                self._stats_label.setText("No file loaded")
                return

            stats = get_stats(self._hotkeys_file)

            text = f"""
Total entries: {stats.total_entries}
Assigned: {stats.assigned_entries}
Unassigned: {stats.unassigned_entries}
User-modified: {stats.user_modified}
Default: {stats.default_bindings}
Rooms: {stats.unique_rooms}
""".strip()

            self._stats_label.setText(text)

            # Update issues summary
            self._update_issues_summary(stats)

        def _update_issues_summary(self, stats: HotkeyStats) -> None:
            """Update the issues summary display."""
            # Clear existing
            while self._issues_layout.count():
                child = self._issues_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            if stats.duplicates == 0 and stats.conflicts == 0 and stats.orphan_rooms == 0:
                label = QLabel("✓ No issues found")
                label.setStyleSheet("color: #81c784;")
                self._issues_layout.addWidget(label)
                return

            if stats.duplicates > 0:
                label = QLabel(
                    f"{ICON_DUPLICATE} {stats.duplicates} duplicates")
                label.setStyleSheet(f"color: {COLOR_DUPLICATE};")
                self._issues_layout.addWidget(label)

            if stats.conflicts > 0:
                label = QLabel(f"{ICON_CONFLICT} {stats.conflicts} conflicts")
                label.setStyleSheet(f"color: {COLOR_CONFLICT};")
                self._issues_layout.addWidget(label)

            if stats.orphan_rooms > 0:
                label = QLabel(
                    f"{ICON_ORPHAN} {stats.orphan_rooms} orphan rooms")
                label.setStyleSheet(f"color: {COLOR_ORPHAN};")
                self._issues_layout.addWidget(label)

        def _update_backup_count(self) -> None:
            """Update the backup count label."""
            if not self._hotkeys_path:
                self._backup_count_label.setText("0 backups available")
                return

            backups = list_backups(self._hotkeys_path)
            self._backup_count_label.setText(
                f"{len(backups)} backups available")

        # =====================================================================
        # CLEANUP ACTIONS
        # =====================================================================

        def _on_remove_duplicates(self) -> None:
            """Remove duplicate entries (excluding garbage key mappings)."""
            if not self._hotkeys_file:
                return

            # Count duplicates (excluding garbage key entries)
            dup_count = sum(
                1 for e in self._hotkeys_file.entries
                if e.is_duplicate and not self._is_garbage_key(e)
            )
            if dup_count == 0:
                QMessageBox.information(
                    self, "No Duplicates", "No duplicates found.")
                return

            reply = QMessageBox.question(
                self,
                "Remove Duplicates",
                f"Remove {dup_count} duplicate entries?\n\n"
                "This will keep the first occurrence of each unique entry.\n"
                "Garbage key mappings will be preserved.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Separate garbage entries from the rest
                garbage_entries = [
                    e for e in self._hotkeys_file.entries if self._is_garbage_key(e)]
                non_garbage_entries = [
                    e for e in self._hotkeys_file.entries if not self._is_garbage_key(e)]

                # Remove duplicates only from non-garbage entries
                unique, removed = remove_duplicates(non_garbage_entries)

                # Combine back: unique non-garbage + all garbage entries
                self._hotkeys_file.entries = unique + garbage_entries

                # Re-validate
                validate_all(self._hotkeys_file)

                # Update UI
                self._update_table()
                self._update_stats()

                self._status_bar.showMessage(f"Removed {removed} duplicates")

        def _on_remove_orphans(self) -> None:
            """Remove entries with orphan rooms."""
            if not self._hotkeys_file:
                return

            # Count orphans
            orphan_count = sum(
                1 for e in self._hotkeys_file.entries if e.is_orphan_room)
            if orphan_count == 0:
                QMessageBox.information(
                    self, "No Orphans", "No orphan rooms found.")
                return

            # Show orphan rooms
            orphan_rooms = {
                e.room for e in self._hotkeys_file.entries if e.is_orphan_room}
            rooms_text = "\n".join(f"  • {r}" for r in sorted(orphan_rooms))

            reply = QMessageBox.question(
                self,
                "Remove Orphan Rooms",
                f"Remove {orphan_count} entries with invalid rooms?\n\n"
                f"Rooms to remove:\n{rooms_text}\n\n"
                f"Valid rooms: {', '.join(sorted(VALID_ROOMS - {''}))}",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                filtered, removed = remove_orphan_rooms(
                    self._hotkeys_file.entries)
                self._hotkeys_file.entries = filtered

                # Re-validate
                validate_all(self._hotkeys_file)

                # Update UI
                self._update_room_filter()
                self._update_table()
                self._update_stats()

                self._status_bar.showMessage(
                    f"Removed {removed} orphan entries")

        def _on_remove_unassigned(self) -> None:
            """Remove entries with no hotkey binding (unassigned), excluding garbage keys."""
            if not self._hotkeys_file:
                return

            # Count unassigned entries (excluding garbage key entries)
            unassigned = [
                e for e in self._hotkeys_file.entries
                if not e.is_assigned and not self._is_garbage_key(e)
            ]

            if not unassigned:
                QMessageBox.information(
                    self, "No Unassigned", "No unassigned entries found.")
                return

            reply = QMessageBox.question(
                self,
                "Remove Unassigned",
                f"Remove {len(unassigned)} entries with no hotkey binding?\n\n"
                "These entries have no key assigned ([None]) and are uninvokable.\n"
                "They just clutter the hotkeys file.\n\n"
                "Garbage key mappings will be preserved.\n\n"
                "Remove these entries?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Remove unassigned entries
                unassigned_ids = {id(e) for e in unassigned}
                self._hotkeys_file.entries = [
                    e for e in self._hotkeys_file.entries
                    if id(e) not in unassigned_ids
                ]

                # Re-validate
                validate_all(self._hotkeys_file)

                # Update UI
                self._update_room_filter()
                self._update_table()
                self._update_stats()

                self._status_bar.showMessage(
                    f"Removed {len(unassigned)} unassigned entries")

        def _on_resolve_conflicts(self) -> None:
            """Open the conflict resolution dialog."""
            if not self._hotkeys_file:
                return

            # Check if there are any conflicts
            conflict_count = sum(
                1 for e in self._hotkeys_file.entries if len(e.conflict_ids) > 0
            )
            if conflict_count == 0:
                QMessageBox.information(
                    self, "No Conflicts", "No hotkey conflicts found."
                )
                return

            # Open dialog
            dialog = ConflictResolutionDialog(self._hotkeys_file, self)
            dialog.setStyleSheet(EDITOR_STYLESHEET)

            if dialog.exec() == QDialog.Accepted:
                # Re-validate and update
                validate_all(self._hotkeys_file)
                self._update_room_filter()
                self._update_table()
                self._update_stats()

                if dialog.has_changes():
                    self._status_bar.showMessage(
                        "Conflicts resolved. Remember to save!")
            elif dialog.has_changes():
                # User cancelled but made changes - they're already applied to entries
                validate_all(self._hotkeys_file)
                self._update_table()
                self._update_stats()
                self._status_bar.showMessage("Changes applied (not saved)")

        # =====================================================================
        # BACKUP ACTIONS
        # =====================================================================

        def _on_create_backup(self) -> None:
            """Create a manual backup."""
            if not self._hotkeys_path:
                return

            try:
                backup_path = create_backup(self._hotkeys_path)
                self._update_backup_count()
                QMessageBox.information(
                    self,
                    "Backup Created",
                    f"Backup saved to:\n{backup_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to create backup: {e}")

        def _on_configure_garbage_key(self) -> None:
            """Open dialog to configure the garbage key combination."""
            dialog = QDialog(self)
            dialog.setWindowTitle("Configure Garbage Key")
            dialog.setMinimumWidth(400)

            layout = QVBoxLayout(dialog)

            # Explanation
            info = QLabel(
                "<b>Garbage Key Combo</b><br><br>"
                "Some 3DCoat shortcuts cannot be unmapped - they respawn with defaults. "
                "Mapping them to an unused 'garbage key' combination is the only way to disable them.<br><br>"
                "Choose a key combo that you will never use for actual shortcuts."
            )
            info.setWordWrap(True)
            layout.addWidget(info)

            # Key selection
            form = QFormLayout()

            key_input = QLineEdit(self._garbage_key)
            key_input.setPlaceholderText(
                "e.g., key_ScrollLock, key_Pause, key_NumLock")
            form.addRow("Key:", key_input)

            ctrl_check = QCheckBox("Ctrl")
            ctrl_check.setChecked(self._garbage_ctrl)

            alt_check = QCheckBox("Alt")
            alt_check.setChecked(self._garbage_alt)

            shift_check = QCheckBox("Shift")
            shift_check.setChecked(self._garbage_shift)

            mod_layout = QHBoxLayout()
            mod_layout.addWidget(ctrl_check)
            mod_layout.addWidget(alt_check)
            mod_layout.addWidget(shift_check)
            mod_layout.addStretch()

            form.addRow("Modifiers:", mod_layout)
            layout.addLayout(form)

            # Buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                # Update garbage key settings
                self._garbage_key = key_input.text().strip() or DEFAULT_GARBAGE_KEY
                self._garbage_ctrl = ctrl_check.isChecked()
                self._garbage_alt = alt_check.isChecked()
                self._garbage_shift = shift_check.isChecked()

                # Update label
                self._garbage_label.setText(
                    f"{self._garbage_key}\n"
                    f"{'Ctrl+' if self._garbage_ctrl else ''}"
                    f"{'Alt+' if self._garbage_alt else ''}"
                    f"{'Shift+' if self._garbage_shift else ''}"
                )

                # Re-validate table (garbage key status may have changed)
                self._update_table()
                self._status_bar.showMessage(
                    "Garbage key configuration updated")

        def _on_restore_backup(self) -> None:
            """Restore from a backup."""
            if not self._hotkeys_path:
                return

            backups = list_backups(self._hotkeys_path)
            if not backups:
                QMessageBox.information(
                    self, "No Backups", "No backups available.")
                return

            # Simple selection dialog - show most recent 10
            items = [
                f"{b.name} ({b.stat().st_size // 1024} KB)" for b in backups[:10]]

            from PySide6.QtWidgets import QInputDialog
            item, ok = QInputDialog.getItem(
                self,
                "Restore Backup",
                "Select backup to restore:",
                items,
                0,
                False,
            )

            if ok and item:
                idx = items.index(item)
                backup_path = backups[idx]

                reply = QMessageBox.question(
                    self,
                    "Confirm Restore",
                    f"Restore from {backup_path.name}?\n\n"
                    "Current file will be backed up first.",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    try:
                        restore_backup(backup_path, self._hotkeys_path)
                        self._load_file(self._hotkeys_path)
                        self._status_bar.showMessage(
                            f"Restored from {backup_path.name}")
                    except Exception as e:
                        QMessageBox.critical(
                            self, "Error", f"Failed to restore: {e}")

        # =====================================================================
        # CONTEXT MENU & SELECTION ACTIONS
        # =====================================================================

        def _on_table_context_menu(self, pos) -> None:
            """Show context menu for table items."""
            selected_items = self._table.selectedItems()
            if not selected_items:
                return

            menu = QMenu(self)

            # Get selected entries
            selected_entries = [
                item.data(COL_COMMAND, Qt.UserRole)
                for item in selected_items
                if item.data(COL_COMMAND, Qt.UserRole) is not None
            ]

            count = len(selected_entries)

            # Edit actions
            if count == 1:
                # Single entry edit options
                entry = selected_entries[0]
                edit_menu = menu.addMenu("📝 Edit...")

                edit_key_action = edit_menu.addAction("🎹 Edit Key Binding...")
                edit_key_action.triggered.connect(
                    lambda: self._edit_key_binding([entry])
                )

                edit_room_action = edit_menu.addAction("🏠 Edit Room...")
                edit_room_action.triggered.connect(
                    lambda: self._edit_room([entry])
                )

                edit_cmd_action = edit_menu.addAction("📛 Edit Command ID...")
                edit_cmd_action.triggered.connect(
                    lambda: self._edit_command([entry])
                )

                unmap_action = edit_menu.addAction("🚫 Unmap Key")
                unmap_action.triggered.connect(self._bulk_unmap_keys)

                garbage_action = edit_menu.addAction("🗑️ Map to Garbage Key")
                garbage_action.triggered.connect(self._bulk_map_to_garbage)

            elif count > 1:
                # Multi-edit actions
                edit_menu = menu.addMenu(f"📝 Edit {count} Selected...")

                edit_key_action = edit_menu.addAction("🎹 Set Key Binding...")
                edit_key_action.triggered.connect(
                    lambda: self._edit_key_binding(selected_entries)
                )

                # Change room - use dynamically detected rooms from file
                room_menu = edit_menu.addMenu("🏠 Change Room")
                if self._hotkeys_file:
                    available_rooms = [""] + sorted(
                        r for r in self._hotkeys_file.get_unique_rooms() if r
                    )
                    for room in available_rooms:
                        display_name = "(Global)" if room == "" else room
                        action = room_menu.addAction(display_name)
                        action.setData(("room", room))
                        action.triggered.connect(
                            lambda checked, r=room: self._bulk_set_room(r)
                        )

                # Unmap keys
                unmap_action = edit_menu.addAction("🚫 Unmap Keys")
                unmap_action.triggered.connect(self._bulk_unmap_keys)

                # Map to garbage key
                garbage_action = edit_menu.addAction("🗑️ Map to Garbage Key")
                garbage_action.triggered.connect(self._bulk_map_to_garbage)

            # View XML action (single entry only)
            if count == 1:
                menu.addSeparator()
                view_xml_action = menu.addAction("📄 View XML...")
                view_xml_action.triggered.connect(
                    lambda: self._view_entry_xml(selected_entries[0])
                )

            # Delete action
            menu.addSeparator()
            delete_action = menu.addAction(
                f"🗑️ Delete {count} Entr{'ies' if count > 1 else 'y'}")
            delete_action.triggered.connect(self._delete_selected_entries)

            menu.exec_(self._table.mapToGlobal(pos))

        def _view_entry_xml(self, entry: HotkeyEntry) -> None:
            """Show the XML representation of an entry in a dialog."""
            xml_text = entry.to_xml()

            dialog = QDialog(self)
            dialog.setWindowTitle(f"XML: {entry.id}")
            dialog.setMinimumSize(500, 300)
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            # Info label
            allow_stack_str = "✓" if entry.allow_stack else "✗"
            user_def_str = str(
                entry.user_defined) if entry.user_defined > 0 else "0 (default)"

            info = QLabel(f"<b>Command:</b> {entry.id}<br>"
                          f"<b>Room:</b> {entry.room or '(Global)'}<br>"
                          f"<b>Binding:</b> {entry.display_key}<br>"
                          f"<b>AllowStack:</b> {allow_stack_str}<br>"
                          f"<b>UserDefined:</b> {user_def_str}")
            info.setWordWrap(True)
            layout.addWidget(info)

            # XML text area
            from PySide6.QtWidgets import QTextEdit
            text_edit = QTextEdit()
            text_edit.setPlainText(xml_text)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet(
                "font-family: 'Consolas', 'Courier New', monospace; "
                "font-size: 11px; background-color: #1e1e1e;"
            )
            layout.addWidget(text_edit, 1)

            # Copy button
            button_layout = QHBoxLayout()
            copy_btn = QPushButton("📋 Copy to Clipboard")
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard(xml_text))
            button_layout.addWidget(copy_btn)
            button_layout.addStretch()

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            dialog.exec()

        def _copy_to_clipboard(self, text: str) -> None:
            """Copy text to clipboard."""
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._status_bar.showMessage("Copied to clipboard", 2000)

        def _get_selected_entries(self) -> list[HotkeyEntry]:
            """Get HotkeyEntry objects for selected table items."""
            selected_items = self._table.selectedItems()
            return [
                item.data(COL_COMMAND, Qt.UserRole)
                for item in selected_items
                if item.data(COL_COMMAND, Qt.UserRole) is not None
            ]

        def _bulk_set_room(self, room: str) -> None:
            """Set the room for all selected entries."""
            entries = self._get_selected_entries()
            if not entries:
                return

            for entry in entries:
                entry.room = room

            # Re-validate and update
            validate_all(self._hotkeys_file)
            self._update_room_filter()
            self._update_table()
            self._update_stats()

            display_room = "(Global)" if room == "" else room
            self._status_bar.showMessage(
                f"Changed room to '{display_room}' for {len(entries)} entries"
            )

        def _bulk_unmap_keys(self) -> None:
            """Unmap (set to unassigned) all selected entries."""
            entries = self._get_selected_entries()
            if not entries:
                return

            for entry in entries:
                entry.code = "key_00"
                entry.ctrl = False
                entry.alt = False
                entry.shift = False

            # Re-validate and update
            validate_all(self._hotkeys_file)
            self._update_table()
            self._update_stats()

            self._status_bar.showMessage(f"Unmapped {len(entries)} entries")

        def _bulk_map_to_garbage(self) -> None:
            """Map all selected entries to the garbage key combination."""
            entries = self._get_selected_entries()
            if not entries:
                return

            for entry in entries:
                entry.code = self._garbage_key
                entry.ctrl = self._garbage_ctrl
                entry.alt = self._garbage_alt
                entry.shift = self._garbage_shift

            # Re-validate and update
            validate_all(self._hotkeys_file)
            self._update_table()
            self._update_stats()

            self._status_bar.showMessage(
                f"Mapped {len(entries)} entr{'ies' if len(entries) > 1 else 'y'} to garbage key"
            )

        def _delete_selected_entries(self) -> None:
            """Delete the selected entries from the hotkeys file."""
            entries = self._get_selected_entries()
            if not entries or not self._hotkeys_file:
                return

            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Delete {len(entries)} hotkey entr{'ies' if len(entries) > 1 else 'y'}?\n\n"
                "This will permanently remove these entries from the file.\n"
                "Remember to save to apply changes.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

            # Remove entries
            entries_to_delete = set(id(e) for e in entries)
            self._hotkeys_file.entries = [
                e for e in self._hotkeys_file.entries
                if id(e) not in entries_to_delete
            ]

            # Re-validate and update
            validate_all(self._hotkeys_file)
            self._update_room_filter()
            self._update_table()
            self._update_stats()

            self._status_bar.showMessage(f"Deleted {len(entries)} entries")

        # =====================================================================
        # CELL EDITING
        # =====================================================================

        def _on_cell_double_click(self, item: QTreeWidgetItem, column: int) -> None:
            """Handle double-click on a cell to edit it."""
            entry: HotkeyEntry | None = item.data(COL_COMMAND, Qt.UserRole)
            if not entry:
                return

            # Check if Shift is held for multi-edit mode
            modifiers = QApplication.keyboardModifiers()
            is_multi_edit = bool(modifiers & Qt.ShiftModifier)

            if is_multi_edit:
                # Multi-edit: apply to all selected entries
                entries = self._get_selected_entries()
                if not entries:
                    entries = [entry]
            else:
                # Single edit
                entries = [entry]

            if column == COL_COMMAND:
                self._edit_command(entries)
            elif column == COL_KEY or column == COL_MODIFIERS:
                self._edit_key_binding(entries)
            elif column == COL_ROOM:
                self._edit_room(entries)
            elif column == COL_STACKABLE:
                self._edit_stackable(entries)
            # Status and User columns are not editable

        def _edit_command(self, entries: list[HotkeyEntry]) -> None:
            """Edit the command ID for entries."""
            if not entries:
                return

            # For single entry, show current value
            current = entries[0].id if len(entries) == 1 else ""
            placeholder = "Enter command ID..." if len(entries) > 1 else ""

            from PySide6.QtWidgets import QInputDialog
            new_id, ok = QInputDialog.getText(
                self,
                "Edit Command",
                f"Command ID{f' (editing {len(entries)} entries)' if len(entries) > 1 else ''}:",
                QLineEdit.Normal,
                current,
            )

            if ok and new_id.strip():
                for entry in entries:
                    entry.id = new_id.strip()

                validate_all(self._hotkeys_file)
                self._update_table()
                self._update_stats()
                self._status_bar.showMessage(
                    f"Updated command for {len(entries)} entr{'ies' if len(entries) > 1 else 'y'}"
                )

        def _edit_room(self, entries: list[HotkeyEntry]) -> None:
            """Edit the room for entries using a dropdown."""
            if not entries or not self._hotkeys_file:
                return

            # Get dynamically detected rooms from the loaded file
            available_rooms = sorted(self._hotkeys_file.get_unique_rooms())

            # Create a simple dialog with a combo box
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Room")
            dialog.setMinimumWidth(300)

            layout = QVBoxLayout(dialog)

            label = QLabel(
                f"Select room{f' for {len(entries)} entries' if len(entries) > 1 else ''}:"
            )
            layout.addWidget(label)

            combo = QComboBox()
            combo.addItem("(Global)", "")
            for room in available_rooms:
                if room:  # Skip empty string (already added as Global)
                    combo.addItem(room, room)

            # Set current value for single entry
            if len(entries) == 1:
                current_room = entries[0].room
                for i in range(combo.count()):
                    if combo.itemData(i) == current_room:
                        combo.setCurrentIndex(i)
                        break

            layout.addWidget(combo)

            # Buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                new_room = combo.currentData()
                for entry in entries:
                    entry.room = new_room

                validate_all(self._hotkeys_file)
                self._update_room_filter()
                self._update_table()
                self._update_stats()

                display_room = "(Global)" if new_room == "" else new_room
                self._status_bar.showMessage(
                    f"Set room to '{display_room}' for {len(entries)} entr{'ies' if len(entries) > 1 else 'y'}"
                )

        def _edit_stackable(self, entries: list[HotkeyEntry]) -> None:
            """Toggle the stackable (allow_stack) flag for entries."""
            if not entries:
                return

            # Determine current state
            current_state = entries[0].allow_stack if len(
                entries) == 1 else False

            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Stackable")
            layout = QVBoxLayout(dialog)

            # Info label
            info = QLabel(
                f"Editing {len(entries)} entr{'ies' if len(entries) > 1 else 'y'}.\n\n"
                "Stackable shortcuts can coexist with other shortcuts using the same key binding.\n"
                "Non-stackable shortcuts will conflict with others on the same key."
            )
            info.setWordWrap(True)
            layout.addWidget(info)

            # Checkbox
            checkbox = QCheckBox("Allow Stacking")
            checkbox.setChecked(current_state)
            layout.addWidget(checkbox)

            # Buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                new_state = checkbox.isChecked()
                for entry in entries:
                    entry.allow_stack = new_state

                validate_all(self._hotkeys_file)
                self._update_table()
                self._update_stats()

                state_str = "stackable" if new_state else "non-stackable"
                self._status_bar.showMessage(
                    f"Set {len(entries)} entr{'ies' if len(entries) > 1 else 'y'} to {state_str}"
                )

        def _edit_key_binding(self, entries: list[HotkeyEntry]) -> None:
            """Edit the key binding for entries using a key capture dialog."""
            if not entries:
                return

            dialog = KeyCaptureDialog(self, entries)
            if dialog.exec() == QDialog.Accepted:
                key_code, ctrl, alt, shift = dialog.get_binding()

                for entry in entries:
                    entry.code = key_code
                    entry.ctrl = ctrl
                    entry.alt = alt
                    entry.shift = shift

                validate_all(self._hotkeys_file)
                self._update_table()
                self._update_stats()
                self._status_bar.showMessage(
                    f"Updated binding for {len(entries)} entr{'ies' if len(entries) > 1 else 'y'}"
                )

    # =============================================================================
    # KEY CAPTURE DIALOG
    # =============================================================================

    class KeyCaptureDialog(QDialog):
        """
        Dialog for capturing a key binding.

        Shows current binding and allows user to press a new key
        or manually select from dropdowns.
        """

        def __init__(
            self,
            parent: QWidget | None,
            entries: list[HotkeyEntry],
        ) -> None:
            super().__init__(parent)
            self._entries = entries
            self._captured_key: str = ""
            self._ctrl: bool = False
            self._alt: bool = False
            self._shift: bool = False

            # Initialize from first entry if single
            if len(entries) == 1:
                entry = entries[0]
                self._captured_key = entry.code if entry.is_assigned else ""
                self._ctrl = entry.ctrl
                self._alt = entry.alt
                self._shift = entry.shift

            self._setup_dialog()
            self._build_ui()
            self._update_display()

        def _setup_dialog(self) -> None:
            """Configure dialog properties."""
            count = len(self._entries)
            title = "Edit Key Binding"
            if count > 1:
                title += f" ({count} entries)"
            self.setWindowTitle(title)
            self.setMinimumWidth(350)
            self.setModal(True)

        def _build_ui(self) -> None:
            """Build the dialog UI."""
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            # Instructions
            instructions = QLabel(
                "Press a key to capture it, or use the controls below.\n"
                "Focus the 'Press Key' area and press your desired key."
            )
            instructions.setWordWrap(True)
            layout.addWidget(instructions)

            # Key capture area
            capture_group = QGroupBox("Key Capture")
            capture_layout = QVBoxLayout(capture_group)

            self._capture_display = QLabel("(none)")
            self._capture_display.setAlignment(Qt.AlignCenter)
            self._capture_display.setStyleSheet(
                "font-size: 18px; font-weight: bold; padding: 20px; "
                "background-color: #1e1e1e; border: 2px solid #555; border-radius: 4px;"
            )
            self._capture_display.setFocusPolicy(Qt.StrongFocus)
            capture_layout.addWidget(self._capture_display)

            # Capture button
            self._capture_btn = QPushButton(
                "🎯 Click here, then press a key...")
            self._capture_btn.setFocusPolicy(Qt.StrongFocus)
            self._capture_btn.setMinimumHeight(40)
            self._capture_btn.installEventFilter(self)
            capture_layout.addWidget(self._capture_btn)

            layout.addWidget(capture_group)

            # Modifier checkboxes
            mod_group = QGroupBox("Modifiers")
            mod_layout = QHBoxLayout(mod_group)

            self._ctrl_check = QCheckBox("Ctrl")
            self._ctrl_check.setChecked(self._ctrl)
            self._ctrl_check.stateChanged.connect(self._on_modifier_changed)
            mod_layout.addWidget(self._ctrl_check)

            self._alt_check = QCheckBox("Alt")
            self._alt_check.setChecked(self._alt)
            self._alt_check.stateChanged.connect(self._on_modifier_changed)
            mod_layout.addWidget(self._alt_check)

            self._shift_check = QCheckBox("Shift")
            self._shift_check.setChecked(self._shift)
            self._shift_check.stateChanged.connect(self._on_modifier_changed)
            mod_layout.addWidget(self._shift_check)

            layout.addWidget(mod_group)

            # Manual key entry
            manual_group = QGroupBox("Manual Entry")
            manual_layout = QHBoxLayout(manual_group)

            manual_layout.addWidget(QLabel("Key code:"))
            self._key_input = QLineEdit()
            self._key_input.setPlaceholderText("e.g., A, F1, SPACE, ESCAPE")
            if self._captured_key and self._captured_key != "key_00":
                self._key_input.setText(self._captured_key)
            self._key_input.textChanged.connect(self._on_key_input_changed)
            manual_layout.addWidget(self._key_input, 1)

            layout.addWidget(manual_group)

            # Unmap button
            unmap_btn = QPushButton("🚫 Unmap (Clear Binding)")
            unmap_btn.clicked.connect(self._on_unmap)
            layout.addWidget(unmap_btn)

            # Button bar
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def eventFilter(self, obj, event) -> bool:
            """Capture key presses on the capture button."""
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QKeyEvent

            if obj == self._capture_btn and event.type() == QEvent.KeyPress:
                key_event: QKeyEvent = event
                key = key_event.key()

                # Ignore modifier-only keys
                if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
                    return True

                # Get key name
                key_name = self._key_to_string(key)
                if key_name:
                    self._captured_key = key_name
                    self._key_input.setText(key_name)

                    # Capture modifiers from the key press
                    mods = key_event.modifiers()
                    self._ctrl = bool(mods & Qt.ControlModifier)
                    self._alt = bool(mods & Qt.AltModifier)
                    self._shift = bool(mods & Qt.ShiftModifier)

                    self._ctrl_check.setChecked(self._ctrl)
                    self._alt_check.setChecked(self._alt)
                    self._shift_check.setChecked(self._shift)

                    self._update_display()

                return True

            return super().eventFilter(obj, event)

        def _key_to_string(self, key: int) -> str:
            """Convert Qt key code to string representation."""
            # Common key mappings
            key_map = {
                Qt.Key_A: "A", Qt.Key_B: "B", Qt.Key_C: "C", Qt.Key_D: "D",
                Qt.Key_E: "E", Qt.Key_F: "F", Qt.Key_G: "G", Qt.Key_H: "H",
                Qt.Key_I: "I", Qt.Key_J: "J", Qt.Key_K: "K", Qt.Key_L: "L",
                Qt.Key_M: "M", Qt.Key_N: "N", Qt.Key_O: "O", Qt.Key_P: "P",
                Qt.Key_Q: "Q", Qt.Key_R: "R", Qt.Key_S: "S", Qt.Key_T: "T",
                Qt.Key_U: "U", Qt.Key_V: "V", Qt.Key_W: "W", Qt.Key_X: "X",
                Qt.Key_Y: "Y", Qt.Key_Z: "Z",
                Qt.Key_0: "0", Qt.Key_1: "1", Qt.Key_2: "2", Qt.Key_3: "3",
                Qt.Key_4: "4", Qt.Key_5: "5", Qt.Key_6: "6", Qt.Key_7: "7",
                Qt.Key_8: "8", Qt.Key_9: "9",
                Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
                Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
                Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
                Qt.Key_Space: "SPACE", Qt.Key_Return: "RETURN", Qt.Key_Enter: "ENTER",
                Qt.Key_Escape: "ESCAPE", Qt.Key_Tab: "TAB", Qt.Key_Backspace: "BACKSPACE",
                Qt.Key_Delete: "DELETE", Qt.Key_Insert: "INSERT",
                Qt.Key_Home: "HOME", Qt.Key_End: "END",
                Qt.Key_PageUp: "PAGEUP", Qt.Key_PageDown: "PAGEDOWN",
                Qt.Key_Left: "LEFT", Qt.Key_Right: "RIGHT",
                Qt.Key_Up: "UP", Qt.Key_Down: "DOWN",
                Qt.Key_Minus: "MINUS", Qt.Key_Plus: "PLUS", Qt.Key_Equal: "EQUAL",
                Qt.Key_BracketLeft: "LBRACKET", Qt.Key_BracketRight: "RBRACKET",
                Qt.Key_Semicolon: "SEMICOLON", Qt.Key_Apostrophe: "APOSTROPHE",
                Qt.Key_Comma: "COMMA", Qt.Key_Period: "PERIOD",
                Qt.Key_Slash: "SLASH", Qt.Key_Backslash: "BACKSLASH",
                Qt.Key_QuoteLeft: "GRAVE",
            }
            return key_map.get(key, "")

        def _on_modifier_changed(self) -> None:
            """Handle modifier checkbox changes."""
            self._ctrl = self._ctrl_check.isChecked()
            self._alt = self._alt_check.isChecked()
            self._shift = self._shift_check.isChecked()
            self._update_display()

        def _on_key_input_changed(self, text: str) -> None:
            """Handle manual key input changes."""
            self._captured_key = text.strip().upper() if text.strip() else ""
            self._update_display()

        def _on_unmap(self) -> None:
            """Clear the key binding."""
            self._captured_key = "key_00"
            self._ctrl = False
            self._alt = False
            self._shift = False
            self._key_input.setText("")
            self._ctrl_check.setChecked(False)
            self._alt_check.setChecked(False)
            self._shift_check.setChecked(False)
            self._update_display()

        def _update_display(self) -> None:
            """Update the key binding display."""
            if not self._captured_key or self._captured_key == "key_00":
                self._capture_display.setText("(unassigned)")
                self._capture_display.setStyleSheet(
                    "font-size: 18px; font-weight: bold; padding: 20px; "
                    "background-color: #1e1e1e; border: 2px solid #555; "
                    "border-radius: 4px; color: #666;"
                )
            else:
                parts = []
                if self._ctrl:
                    parts.append("Ctrl")
                if self._alt:
                    parts.append("Alt")
                if self._shift:
                    parts.append("Shift")
                parts.append(self._captured_key)

                self._capture_display.setText(" + ".join(parts))
                self._capture_display.setStyleSheet(
                    "font-size: 18px; font-weight: bold; padding: 20px; "
                    "background-color: #1e1e1e; border: 2px solid #90caf9; "
                    "border-radius: 4px; color: #90caf9;"
                )

        def get_binding(self) -> tuple[str, bool, bool, bool]:
            """Get the captured binding as (key_code, ctrl, alt, shift)."""
            key = self._captured_key if self._captured_key else "key_00"
            return (key, self._ctrl, self._alt, self._shift)

    # =============================================================================
    # CONFLICT RESOLUTION DIALOG
    # =============================================================================

    # Resolution action types
    RESOLUTION_KEEP: str = "keep"
    RESOLUTION_UNMAP: str = "unmap"
    RESOLUTION_DELETE: str = "delete"
    RESOLUTION_REMAP: str = "remap"
    RESOLUTION_GARBAGE: str = "garbage"

    class ConflictResolutionDialog(QDialog):
        """
        Dialog for resolving hotkey conflicts.

        Shows groups of conflicting hotkeys and allows the user to
        select a resolution action for each entry:
        - Keep: Keep this binding (only one per group)
        - Unmap: Clear the key binding but keep the entry
        - Delete: Remove the entry entirely
        - Remap: Change to a different key binding

        Conflicts include:
        - Same key binding in the same room
        - Room-specific bindings that conflict with Global bindings
        """

        def __init__(
            self,
            hotkeys_file: HotkeysFile,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self._hotkeys_file: HotkeysFile = hotkeys_file
            self._conflict_groups: dict[str, list[HotkeyEntry]] = {}
            self._changes_made: bool = False

            # Track resolution state per entry: entry_id -> (action, remap_binding)
            # remap_binding is (code, ctrl, alt, shift) if action is REMAP
            self._resolutions: dict[int, tuple[str, tuple | None]] = {}

            # Track widgets for updating
            self._entry_widgets: dict[int, dict] = {}

            self._setup_dialog()
            self._build_ui()
            self._refresh_conflicts()

        def _setup_dialog(self) -> None:
            """Configure dialog properties."""
            self.setWindowTitle("Resolve Hotkey Conflicts")
            self.setMinimumSize(800, 600)
            self.resize(900, 700)
            self.setModal(True)

        def _build_ui(self) -> None:
            """Build the dialog UI."""
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            # Header
            header = QLabel(
                "⚡ Hotkey Conflicts\n"
                "Each group shows commands sharing the same key binding (including Global conflicts).\n"
                "For each entry, select an action. Only ONE entry per group can be 'Keep'."
            )
            header.setWordWrap(True)
            header.setStyleSheet("color: #ffb74d; font-weight: bold;")
            layout.addWidget(header)

            # Status label
            self._status_label = QLabel()
            self._status_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(self._status_label)

            # Scroll area for conflict groups
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            self._groups_container = QWidget()
            self._groups_layout = QVBoxLayout(self._groups_container)
            self._groups_layout.setSpacing(12)
            self._groups_layout.setContentsMargins(4, 4, 4, 4)
            scroll.setWidget(self._groups_container)

            layout.addWidget(scroll, 1)

            # Button bar
            button_layout = QHBoxLayout()

            btn_refresh = QPushButton("🔄 Recalculate Conflicts")
            btn_refresh.clicked.connect(self._refresh_conflicts)
            button_layout.addWidget(btn_refresh)

            button_layout.addStretch()

            self._btn_apply = QPushButton("✅ Apply Resolutions")
            self._btn_apply.setObjectName("successBtn")
            self._btn_apply.setToolTip("Apply all selected resolutions")
            self._btn_apply.clicked.connect(self._apply_resolutions)
            button_layout.addWidget(self._btn_apply)

            self._btn_commit = QPushButton("✅ Apply && Close")
            self._btn_commit.setObjectName("successBtn")
            self._btn_commit.setToolTip(
                "Apply resolutions and close (only enabled when all groups resolved)")
            self._btn_commit.clicked.connect(self._apply_and_close)
            button_layout.addWidget(self._btn_commit)

            btn_cancel = QPushButton("Cancel")
            btn_cancel.clicked.connect(self.reject)
            button_layout.addWidget(btn_cancel)

            layout.addLayout(button_layout)

        def _refresh_conflicts(self) -> None:
            """Recalculate conflicts and rebuild the UI."""
            # Clear resolutions
            self._resolutions.clear()
            self._entry_widgets.clear()

            # Find conflicts with global awareness
            self._conflict_groups = self._find_conflicts_with_global()

            # Initialize all entries to "keep" by default (user must change all but one)
            for entries in self._conflict_groups.values():
                for entry in entries:
                    self._resolutions[id(entry)] = (RESOLUTION_KEEP, None)

            # Rebuild group widgets
            self._rebuild_groups_ui()
            self._update_status()

        def _find_conflicts_with_global(self) -> dict[str, list[HotkeyEntry]]:
            """
            Find conflicts including Global+Room conflicts.

            A conflict occurs when:
            - Multiple entries share the same binding in the same room
            - A room-specific entry shares a binding with a Global entry
            """
            # Build index: (code, ctrl, alt, shift) -> list of entries
            binding_index: dict[tuple, list[HotkeyEntry]] = {}

            for entry in self._hotkeys_file.entries:
                if not entry.is_assigned:
                    continue
                if entry.is_duplicate:
                    continue
                # Skip garbage key entries - they're intentionally mapped to unused key
                if self._is_garbage_key(entry):
                    continue

                binding_tuple = (entry.code, entry.ctrl,
                                 entry.alt, entry.shift)
                if binding_tuple not in binding_index:
                    binding_index[binding_tuple] = []
                binding_index[binding_tuple].append(entry)

            # Find conflicts
            conflicts: dict[str, list[HotkeyEntry]] = {}

            for binding_tuple, entries in binding_index.items():
                if len(entries) < 2:
                    continue

                # Group by room, but Global ("") conflicts with everything
                global_entries = [e for e in entries if e.room == ""]
                room_entries: dict[str, list[HotkeyEntry]] = {}

                for entry in entries:
                    if entry.room:
                        if entry.room not in room_entries:
                            room_entries[entry.room] = []
                        room_entries[entry.room].append(entry)

                # Check for conflicts
                # 1. Multiple globals = conflict
                if len(global_entries) > 1:
                    key = f"|{binding_tuple[0]}|{binding_tuple[1]}|{binding_tuple[2]}|{binding_tuple[3]}"
                    if key not in conflicts:
                        conflicts[key] = []
                    conflicts[key].extend(global_entries)

                # 2. Multiple in same room = conflict
                for room, room_list in room_entries.items():
                    if len(room_list) > 1:
                        key = f"{room}|{binding_tuple[0]}|{binding_tuple[1]}|{binding_tuple[2]}|{binding_tuple[3]}"
                        if key not in conflicts:
                            conflicts[key] = []
                        conflicts[key].extend(room_list)

                # 3. Global + any room-specific = conflict
                if global_entries:
                    for room, room_list in room_entries.items():
                        # Combine global + room entries as a conflict group
                        key = f"{room}+Global|{binding_tuple[0]}|{binding_tuple[1]}|{binding_tuple[2]}|{binding_tuple[3]}"
                        if key not in conflicts:
                            conflicts[key] = []
                        # Add global entries if not already
                        for ge in global_entries:
                            if ge not in conflicts[key]:
                                conflicts[key].append(ge)
                        for re in room_list:
                            if re not in conflicts[key]:
                                conflicts[key].append(re)

            # Filter to only actual conflicts (2+ entries with not all allow_stack)
            filtered: dict[str, list[HotkeyEntry]] = {}
            for key, group in conflicts.items():
                if len(group) > 1 and not all(e.allow_stack for e in group):
                    # Remove duplicates by id
                    seen_ids = set()
                    unique = []
                    for e in group:
                        if id(e) not in seen_ids:
                            seen_ids.add(id(e))
                            unique.append(e)
                    if len(unique) > 1:
                        filtered[key] = unique

            return filtered

        def _rebuild_groups_ui(self) -> None:
            """Rebuild the conflict group widgets."""
            # Clear existing
            while self._groups_layout.count():
                child = self._groups_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            if not self._conflict_groups:
                label = QLabel("✅ No conflicts to resolve.")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #81c784; font-size: 14px;")
                self._groups_layout.addWidget(label)
                self._groups_layout.addStretch()
                return

            for binding_key, entries in self._conflict_groups.items():
                group_widget = self._create_conflict_group(
                    binding_key, entries)
                self._groups_layout.addWidget(group_widget)

            self._groups_layout.addStretch()

        def _create_conflict_group(
            self, binding_key: str, entries: list[HotkeyEntry]
        ) -> QWidget:
            """Create a widget for a single conflict group."""
            # Parse binding key: "Room|Code|Ctrl|Alt|Shift" or "Room+Global|..."
            parts = binding_key.split("|")
            room_part = parts[0] if parts[0] else "(Global)"
            key = parts[1] if len(parts) > 1 else "?"

            # Build modifier string
            mods = []
            if len(parts) > 2 and parts[2] == "True":
                mods.append("Ctrl")
            if len(parts) > 3 and parts[3] == "True":
                mods.append("Alt")
            if len(parts) > 4 and parts[4] == "True":
                mods.append("Shift")
            mod_str = "+".join(mods) + "+" if mods else ""
            binding_display = f"{mod_str}{key}"

            group = QGroupBox(f"⚡ {binding_display} — {room_part}")
            group.setStyleSheet("QGroupBox { font-weight: bold; }")
            layout = QVBoxLayout(group)
            layout.setSpacing(8)

            # Store group info for validation
            group_entry_ids = [id(e) for e in entries]

            # Entry rows with resolution options
            for entry in entries:
                entry_widget = self._create_entry_row(entry, group_entry_ids)
                layout.addWidget(entry_widget)

            return group

        def _create_entry_row(
            self, entry: HotkeyEntry, group_entry_ids: list[int]
        ) -> QWidget:
            """Create a row widget for a single entry with resolution options."""
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 4, 0, 4)
            layout.setSpacing(8)

            # Command name + room
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            cmd_label = QLabel(f"<b>{entry.id}</b>")
            cmd_label.setStyleSheet("font-family: monospace;")
            info_layout.addWidget(cmd_label)

            room_display = entry.room if entry.room else "(Global)"
            room_label = QLabel(f"Room: {room_display}")
            room_label.setStyleSheet("color: #888; font-size: 10px;")
            info_layout.addWidget(room_label)

            layout.addLayout(info_layout, 1)

            # Resolution combo box
            combo = QComboBox()
            combo.addItem("✓ Keep", RESOLUTION_KEEP)
            combo.addItem("🚫 Unmap", RESOLUTION_UNMAP)
            combo.addItem("🗑️ Delete", RESOLUTION_DELETE)
            combo.addItem("🔄 Remap...", RESOLUTION_REMAP)
            combo.addItem(f"{ICON_GARBAGE} Map to Garbage Key",
                          RESOLUTION_GARBAGE)
            combo.setMinimumWidth(150)

            # Remap display label
            remap_label = QLabel("")
            remap_label.setStyleSheet("color: #90caf9; font-size: 10px;")
            remap_label.setVisible(False)

            # Status indicator
            status_label = QLabel("")
            status_label.setMinimumWidth(30)

            # Store widget refs
            entry_id = id(entry)
            self._entry_widgets[entry_id] = {
                "combo": combo,
                "remap_label": remap_label,
                "status_label": status_label,
                "entry": entry,
                "group_ids": group_entry_ids,
            }

            # Connect combo change
            combo.currentIndexChanged.connect(
                lambda idx, eid=entry_id: self._on_resolution_changed(eid)
            )

            layout.addWidget(combo)
            layout.addWidget(remap_label)
            layout.addWidget(status_label)

            return container

        def _on_resolution_changed(self, entry_id: int) -> None:
            """Handle resolution combo change."""
            widgets = self._entry_widgets.get(entry_id)
            if not widgets:
                return

            combo: QComboBox = widgets["combo"]
            remap_label: QLabel = widgets["remap_label"]
            entry: HotkeyEntry = widgets["entry"]

            action = combo.currentData()

            if action == RESOLUTION_REMAP:
                # Open remap dialog
                remap_binding = self._prompt_remap(entry)
                if remap_binding:
                    self._resolutions[entry_id] = (
                        RESOLUTION_REMAP, remap_binding)
                    # Show new binding
                    code, ctrl, alt, shift = remap_binding
                    parts = []
                    if ctrl:
                        parts.append("Ctrl")
                    if alt:
                        parts.append("Alt")
                    if shift:
                        parts.append("Shift")
            elif action == RESOLUTION_GARBAGE:
                # Map to garbage key (no confirmation needed)
                garbage_binding = (
                    self._garbage_key,
                    self._garbage_ctrl,
                    self._garbage_alt,
                    self._garbage_shift,
                )
                self._resolutions[entry_id] = (
                    RESOLUTION_GARBAGE, garbage_binding)
                # Show garbage key binding
                parts = []
                if self._garbage_ctrl:
                    parts.append("Ctrl")
                if self._garbage_alt:
                    parts.append("Alt")
                if self._garbage_shift:
                    parts.append("Shift")
                    parts.append(code)
                    remap_label.setText(f"→ {'+'.join(parts)}")
                    remap_label.setVisible(True)
                else:
                    # Cancelled, revert to Keep
                    combo.blockSignals(True)
                    combo.setCurrentIndex(0)
                    combo.blockSignals(False)
                    self._resolutions[entry_id] = (RESOLUTION_KEEP, None)
                    remap_label.setVisible(False)
            else:
                self._resolutions[entry_id] = (action, None)
                remap_label.setVisible(False)

            self._update_status()
            self._update_entry_statuses()

        def _prompt_remap(self, entry: HotkeyEntry) -> tuple | None:
            """
            Prompt user to enter a new key binding.
            Returns (code, ctrl, alt, shift) or None if cancelled.
            Validates that the new binding doesn't conflict.
            """
            while True:
                dialog = KeyCaptureDialog(self, [entry])
                if dialog.exec() != QDialog.Accepted:
                    return None

                new_binding = dialog.get_binding()
                code, ctrl, alt, shift = new_binding

                if code == "key_00":
                    # Empty binding is like unmap
                    QMessageBox.information(
                        self, "Empty Binding",
                        "You entered an empty binding. Use 'Unmap' instead."
                    )
                    continue

                # Check for conflicts with the new binding
                conflicts = self._check_binding_conflicts(
                    entry, code, ctrl, alt, shift
                )

                if not conflicts:
                    return new_binding

                # Show conflict warning
                conflict_list = "\n".join(f"  • {e.id} ({e.room or 'Global'})"
                                          for e in conflicts[:5])
                if len(conflicts) > 5:
                    conflict_list += f"\n  ... and {len(conflicts) - 5} more"

                reply = QMessageBox.warning(
                    self,
                    "Binding Conflict",
                    f"This binding conflicts with:\n{conflict_list}\n\n"
                    "Try a different key?",
                    QMessageBox.Retry | QMessageBox.Cancel,
                )

                if reply != QMessageBox.Retry:
                    return None

        def _check_binding_conflicts(
            self,
            entry: HotkeyEntry,
            code: str,
            ctrl: bool,
            alt: bool,
            shift: bool,
        ) -> list[HotkeyEntry]:
            """
            Check if a binding would conflict with any other entry.
            Returns list of conflicting entries (excluding the entry itself).
            """
            conflicts: list[HotkeyEntry] = []
            entry_room = entry.room

            for other in self._hotkeys_file.entries:
                if id(other) == id(entry):
                    continue
                if not other.is_assigned:
                    continue
                if other.code != code:
                    continue
                if other.ctrl != ctrl or other.alt != alt or other.shift != shift:
                    continue

                # Same binding - check room conflict
                # Conflict if: same room, or one is Global
                if other.room == entry_room:
                    conflicts.append(other)
                elif other.room == "" or entry_room == "":
                    conflicts.append(other)

            # Also check against pending remaps in this dialog
            for eid, (action, remap) in self._resolutions.items():
                if action == RESOLUTION_REMAP and remap and eid != id(entry):
                    r_code, r_ctrl, r_alt, r_shift = remap
                    if r_code == code and r_ctrl == ctrl and r_alt == alt and r_shift == shift:
                        # Find the entry
                        for widgets in self._entry_widgets.values():
                            if id(widgets["entry"]) == eid:
                                other_entry = widgets["entry"]
                                if other_entry.room == entry_room or other_entry.room == "" or entry_room == "":
                                    if other_entry not in conflicts:
                                        conflicts.append(other_entry)

            return conflicts

        def _update_status(self) -> None:
            """Update the overall status display."""
            unresolved_groups = 0
            total_groups = len(self._conflict_groups)

            for binding_key, entries in self._conflict_groups.items():
                keep_count = 0
                for entry in entries:
                    action, _ = self._resolutions.get(
                        id(entry), (RESOLUTION_KEEP, None))
                    if action == RESOLUTION_KEEP:
                        keep_count += 1

                if keep_count != 1:
                    unresolved_groups += 1

            if total_groups == 0:
                self._status_label.setText("✅ No conflicts!")
                self._status_label.setStyleSheet(
                    "color: #81c784; font-size: 12px;")
                self._btn_commit.setEnabled(True)
                self._btn_apply.setEnabled(False)
            elif unresolved_groups == 0:
                self._status_label.setText(
                    f"✅ All {total_groups} conflict group(s) resolved! Ready to apply."
                )
                self._status_label.setStyleSheet(
                    "color: #81c784; font-size: 12px;")
                self._btn_commit.setEnabled(True)
                self._btn_apply.setEnabled(True)
            else:
                self._status_label.setText(
                    f"⚠️ {unresolved_groups}/{total_groups} group(s) need resolution. "
                    f"Each group must have exactly ONE 'Keep'."
                )
                self._status_label.setStyleSheet(
                    "color: #ffb74d; font-size: 12px;")
                self._btn_commit.setEnabled(False)
                self._btn_apply.setEnabled(True)

        def _update_entry_statuses(self) -> None:
            """Update status indicators on all entry rows."""
            # Check each group
            for binding_key, entries in self._conflict_groups.items():
                keep_count = 0
                keep_entries = []
                for entry in entries:
                    action, _ = self._resolutions.get(
                        id(entry), (RESOLUTION_KEEP, None))
                    if action == RESOLUTION_KEEP:
                        keep_count += 1
                        keep_entries.append(entry)

                # Update status labels
                for entry in entries:
                    entry_id = id(entry)
                    widgets = self._entry_widgets.get(entry_id)
                    if not widgets:
                        continue

                    status_label: QLabel = widgets["status_label"]
                    action, remap = self._resolutions.get(
                        entry_id, (RESOLUTION_KEEP, None))

                    if action == RESOLUTION_KEEP:
                        if keep_count == 1:
                            status_label.setText("✓")
                            status_label.setStyleSheet("color: #81c784;")
                        else:
                            status_label.setText("⚠️")
                            status_label.setStyleSheet("color: #ffb74d;")
                            status_label.setToolTip(
                                f"{keep_count} entries set to 'Keep' - only 1 allowed"
                            )
                    elif action == RESOLUTION_REMAP:
                        # Check if remap conflicts
                        if remap:
                            conflicts = self._check_binding_conflicts(
                                entry, remap[0], remap[1], remap[2], remap[3]
                            )
                            if conflicts:
                                status_label.setText("⚠️")
                                status_label.setStyleSheet("color: #ef5350;")
                                status_label.setToolTip(
                                    "Remap still conflicts!")
                            else:
                                status_label.setText("→")
                                status_label.setStyleSheet("color: #90caf9;")
                                status_label.setToolTip("")
                    else:
                        status_label.setText("")
                        status_label.setToolTip("")

        def _apply_resolutions(self) -> None:
            """Apply all selected resolutions without closing."""
            changes = 0

            # Process in order: deletes first, then unmaps, then remaps
            entries_to_delete: list[int] = []

            for entry_id, (action, remap) in self._resolutions.items():
                # Find entry
                entry = None
                for e in self._hotkeys_file.entries:
                    if id(e) == entry_id:
                        entry = e
                        break

                if not entry:
                    continue

                if action == RESOLUTION_DELETE:
                    entries_to_delete.append(entry_id)
                    changes += 1
                elif action == RESOLUTION_UNMAP:
                    entry.code = "key_00"
                    entry.ctrl = False
                    entry.alt = False
                    entry.shift = False
                    changes += 1
                elif action == RESOLUTION_REMAP and remap:
                    entry.code, entry.ctrl, entry.alt, entry.shift = remap
                    changes += 1
                elif action == RESOLUTION_GARBAGE and remap:
                    # Map to garbage key
                    entry.code, entry.ctrl, entry.alt, entry.shift = remap
                    changes += 1

            # Delete entries
            if entries_to_delete:
                self._hotkeys_file.entries = [
                    e for e in self._hotkeys_file.entries
                    if id(e) not in entries_to_delete
                ]

            if changes > 0:
                self._changes_made = True

            # Refresh
            self._refresh_conflicts()

            QMessageBox.information(
                self,
                "Resolutions Applied",
                f"Applied {changes} resolution(s).\n"
                f"Remaining conflicts: {len(self._conflict_groups)}"
            )

        def _apply_and_close(self) -> None:
            """Apply resolutions and close the dialog."""
            self._apply_resolutions()
            if not self._conflict_groups:
                self.accept()
            # If there are still conflicts, don't close

        def has_changes(self) -> bool:
            """Check if any changes were made."""
            return self._changes_made


# =============================================================================
# LAUNCHER FUNCTIONS
# =============================================================================

def launch_hotkey_editor(
    path: Path | str | None = None,
    parent: "QWidget | None" = None,
) -> "HotkeyEditorWindow | None":
    """
    Launch the hotkey editor window.

    Can be called from inside 3DCoat (LKS panel) or standalone.

    Args:
        path: Path to hotkeys file (auto-detects if None)
        parent: Parent widget (for modal behavior)

    Returns:
        The editor window instance, or None if Qt not available
    """
    if not HAS_QT:
        print("ERROR: PySide6 not available")
        return None

    # Ensure QApplication exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # Convert path
    hotkeys_path: Path | None = None
    if path:
        hotkeys_path = Path(path)
    else:
        hotkeys_path = discover_hotkeys_path()

    # Create and show window
    window = HotkeyEditorWindow(hotkeys_path, parent)
    window.show()

    return window


def run_standalone(path: str | None = None) -> int:
    """
    Run the editor as a standalone application.

    Args:
        path: Path to hotkeys file (optional)

    Returns:
        Exit code
    """
    if not HAS_QT:
        print("ERROR: PySide6 is required. Install with: pip install PySide6")
        return 1

    app = QApplication(sys.argv)

    # Parse path argument
    hotkeys_path: Path | None = None
    if path:
        hotkeys_path = Path(path)
    elif len(sys.argv) > 1:
        hotkeys_path = Path(sys.argv[1])

    window = HotkeyEditorWindow(hotkeys_path)
    window.show()

    return app.exec()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Allow running as: python -m utils.hotkey_editor [path]
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(run_standalone(path_arg))
