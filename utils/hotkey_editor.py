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
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QBrush

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False
    QMainWindow = object  # Fallback for type hints

# =============================================================================
# FLEXIBLE IMPORT: Works both inside 3DCoat and standalone
# =============================================================================
# When running standalone (outside 3DCoat), utils/__init__.py imports coat
# which doesn't exist. We handle this by importing hotkey_utils directly.

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

# Status colors
COLOR_DUPLICATE: str = "#ef5350"  # Red
COLOR_CONFLICT: str = "#ffb74d"   # Orange
COLOR_ORPHAN: str = "#ce93d8"     # Purple
COLOR_NORMAL: str = "#e0e0e0"     # Default gray
COLOR_UNASSIGNED: str = "#666666"  # Dim gray

# Status icons
ICON_DUPLICATE: str = "⊗"  # Duplicate
ICON_CONFLICT: str = "⚡"   # Conflict
ICON_ORPHAN: str = "?"     # Orphan room
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

            self._setup_window()
            self._build_ui()

            # Load file if path provided
            if hotkeys_path:
                self._load_file(hotkeys_path)

        def _setup_window(self) -> None:
            """Configure window properties."""
            self.setWindowTitle("3DCoat Hotkey Editor")
            self.setMinimumSize(800, 600)
            self.resize(1000, 700)
            self.setStyleSheet(EDITOR_STYLESHEET)

            # Center on screen
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    (geo.width() - self.width()) // 2,
                    (geo.height() - self.height()) // 2,
                )

        def _build_ui(self) -> None:
            """Build the main UI layout."""
            central = QWidget()
            self.setCentralWidget(central)

            layout = QVBoxLayout(central)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(8)

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

            # Columns
            self._table.setHeaderLabels([
                "Command", "Key", "Modifiers", "Room", "Status", "User"
            ])

            # Column sizing
            header = self._table.header()
            header.setSectionResizeMode(COL_COMMAND, QHeaderView.Stretch)
            header.setSectionResizeMode(COL_KEY, QHeaderView.Fixed)
            header.setSectionResizeMode(COL_MODIFIERS, QHeaderView.Fixed)
            header.setSectionResizeMode(COL_ROOM, QHeaderView.Fixed)
            header.setSectionResizeMode(COL_STATUS, QHeaderView.Fixed)
            header.setSectionResizeMode(COL_USER_DEF, QHeaderView.Fixed)
            header.resizeSection(COL_KEY, 80)
            header.resizeSection(COL_MODIFIERS, 100)
            header.resizeSection(COL_ROOM, 100)
            header.resizeSection(COL_STATUS, 60)
            header.resizeSection(COL_USER_DEF, 50)

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

            # Separator
            sep3 = QFrame()
            sep3.setObjectName("separator")
            sep3.setFrameShape(QFrame.HLine)
            layout.addWidget(sep3)

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
                item.setText(COL_KEY, entry.code if entry.is_assigned else "-")

                # Modifiers
                item.setText(COL_MODIFIERS, entry.modifier_string or "-")

                # Room
                item.setText(COL_ROOM, entry.display_room)

                # Status
                status_parts: list[str] = []
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

                # Coloring based on issues
                if entry.is_duplicate:
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
            """Remove duplicate entries."""
            if not self._hotkeys_file:
                return

            # Count duplicates
            dup_count = sum(
                1 for e in self._hotkeys_file.entries if e.is_duplicate)
            if dup_count == 0:
                QMessageBox.information(
                    self, "No Duplicates", "No duplicates found.")
                return

            reply = QMessageBox.question(
                self,
                "Remove Duplicates",
                f"Remove {dup_count} duplicate entries?\n\n"
                "This will keep the first occurrence of each unique entry.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                unique, removed = remove_duplicates(self._hotkeys_file.entries)
                self._hotkeys_file.entries = unique

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
