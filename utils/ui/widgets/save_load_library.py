"""
Save/Load/Library Widget - Reusable component for managing saved configurations.

Provides consistent UI for:
- Saving current state to file
- Loading from file
- Storing configurations in a library
- Loading from library
- Deleting library items

Usage:
    widget = SaveLoadLibrary(
        library_dir=Path("data/library/radial_menus"),
        default_filename="default_menu.json",
        on_save=lambda path: save_config(path),
        on_load=lambda path: load_config(path),
        log_success=lambda msg: print(msg),
        log_error=lambda msg: print(msg),
    )
    layout.addWidget(widget)
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, Signal


class SaveLoadLibrary(QWidget):
    """
    Reusable save/load/library management widget.

    Emits signals when save/load operations complete successfully.
    Callbacks handle the actual file I/O.
    """

    # Signals emitted after successful operations
    saved = Signal(Path)  # Emitted after save (current path)
    loaded = Signal(Path)  # Emitted after load (new path)

    def __init__(
        self,
        library_dir: Path,
        default_filename: str,
        file_extension: str = ".json",
        on_save: Callable[[Path], None] | None = None,
        on_load: Callable[[Path], None] | None = None,
        log_success: Callable[[str], None] | None = None,
        log_error: Callable[[str], None] | None = None,
        before_load: Callable[[], bool] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize save/load/library widget.

        Args:
            library_dir: Directory for library storage
            default_filename: Default filename for new saves
            file_extension: File extension (e.g., ".json")
            on_save: Callback(path) to save current state to path
            on_load: Callback(path) to load state from path
            log_success: Optional callback for success messages
            log_error: Optional callback for error messages
            before_load: Optional guard callback invoked before any load.
                Return True to proceed, False to cancel (e.g., prompt for
                unsaved changes).  When False the dropdown reverts.
            parent: Parent widget
        """
        super().__init__(parent)

        self._library_dir: Path = library_dir
        self._default_filename: str = default_filename
        self._file_extension: str = file_extension
        self._on_save: Callable[[Path], None] | None = on_save
        self._on_load: Callable[[Path], None] | None = on_load
        self._log_success: Callable[[str], None] | None = log_success
        self._log_error: Callable[[str], None] | None = log_error
        self._before_load: Callable[[], bool] | None = before_load

        # Track current file (None if never saved)
        self._current_path: Path | None = None
        self._is_library_item: bool = False

        # Suppress combo-signal during programmatic index changes
        self._suppress_combo_signal: bool = False
        self._prev_library_index: int = -1

        self._setup_ui()
        self._refresh_library_list()

    def _setup_ui(self) -> None:
        """Build the widget UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Row 1: Save/Load buttons
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self._save_btn = QPushButton("💾 Save")
        self._save_btn.setToolTip(
            "Save to current file (or Save As if no file loaded)")
        self._save_btn.clicked.connect(self._on_save_clicked)
        row1.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("💾+ Save As")
        self._save_as_btn.setToolTip("Save as new file")
        self._save_as_btn.clicked.connect(self._on_save_as_clicked)
        row1.addWidget(self._save_as_btn)

        self._load_btn = QPushButton("📂 Load")
        self._load_btn.setToolTip("Load from file")
        self._load_btn.clicked.connect(self._on_load_clicked)
        row1.addWidget(self._load_btn)

        main_layout.addLayout(row1)

        # Row 2: Library operations
        row2 = QHBoxLayout()
        row2.setSpacing(4)

        row2.addWidget(QLabel("Library:"))

        self._library_combo = QComboBox()
        self._library_combo.setMinimumWidth(120)
        self._library_combo.currentTextChanged.connect(
            self._on_library_selection_changed)
        row2.addWidget(self._library_combo, stretch=1)

        self._load_lib_btn = QPushButton("📖")
        self._load_lib_btn.setToolTip("Load selected library item")
        self._load_lib_btn.setFixedWidth(30)
        self._load_lib_btn.clicked.connect(self._on_load_library_clicked)
        row2.addWidget(self._load_lib_btn)

        main_layout.addLayout(row2)

        # Row 3: Store/Delete library buttons
        row3 = QHBoxLayout()
        row3.setSpacing(4)

        self._store_btn = QPushButton("📥 Store to Library")
        self._store_btn.setToolTip(
            "Save current state as new library item")
        self._store_btn.clicked.connect(self._on_store_clicked)
        row3.addWidget(self._store_btn)

        self._delete_btn = QPushButton("🗑️ Delete")
        self._delete_btn.setToolTip("Delete selected library item")
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        row3.addWidget(self._delete_btn)

        main_layout.addLayout(row3)

        self._update_button_states()

    def _update_button_states(self) -> None:
        """Update button enabled/disabled states based on current state."""
        has_library_selection = (
            self._library_combo.currentIndex() >= 0 and
            self._library_combo.currentText() != ""
        )

        self._load_lib_btn.setEnabled(has_library_selection)
        self._delete_btn.setEnabled(
            has_library_selection and self._is_library_item)

    def _refresh_library_list(self, keep_selection: str = "") -> None:
        """Refresh the library combo box with available items."""
        self._suppress_combo_signal = True
        try:
            self._library_combo.clear()

            if not self._library_dir.exists():
                self._library_dir.mkdir(parents=True, exist_ok=True)
                return

            # Find all files with matching extension
            items = sorted([
                f.stem for f in self._library_dir.glob(f"*{self._file_extension}")
            ])

            if items:
                self._library_combo.addItems(items)

            # Restore previous selection when refreshing
            if keep_selection:
                idx = self._library_combo.findText(keep_selection)
                if idx >= 0:
                    self._library_combo.setCurrentIndex(idx)
                    self._prev_library_index = idx
        finally:
            self._suppress_combo_signal = False

        self._update_button_states()

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        if self._current_path is None:
            # No current file - route to Save As
            self._on_save_as_clicked()
        else:
            # Save to current file
            try:
                if self._on_save:
                    self._on_save(self._current_path)
                    if self._log_success:
                        self._log_success(f"Saved: {self._current_path.name}")
                    self.saved.emit(self._current_path)
            except Exception as e:
                if self._log_error:
                    self._log_error(f"Save failed: {e}")

    def _on_save_as_clicked(self) -> None:
        """Handle save as button click."""
        # Prompt for new filename
        initial_dir = (
            str(self._current_path.parent) if self._current_path
            else str(self._library_dir.parent)
        )

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            f"{initial_dir}/{self._default_filename}",
            f"Config Files (*{self._file_extension})",
        )

        if not path:
            return  # User cancelled

        path = Path(path)

        try:
            if self._on_save:
                self._on_save(path)
                self._current_path = path
                self._is_library_item = path.parent == self._library_dir

                if self._log_success:
                    self._log_success(f"Saved as: {path.name}")

                self.saved.emit(path)

                # Refresh library if saved to library dir
                if self._is_library_item:
                    self._refresh_library_list(keep_selection=path.stem)
                    idx = self._library_combo.findText(path.stem)
                    self._prev_library_index = idx if idx >= 0 else self._prev_library_index

                self._update_button_states()
        except Exception as e:
            if self._log_error:
                self._log_error(f"Save As failed: {e}")

    def _on_load_clicked(self) -> None:
        """Handle load button click."""
        # Prompt for file
        initial_dir = (
            str(self._current_path.parent) if self._current_path
            else str(self._library_dir.parent)
        )

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            initial_dir,
            f"Config Files (*{self._file_extension})",
        )

        if not path:
            return  # User cancelled

        path = Path(path)

        try:
            if self._on_load:
                self._on_load(path)
                self._current_path = path
                self._is_library_item = path.parent == self._library_dir

                if self._log_success:
                    self._log_success(f"Loaded: {path.name}")

                self.loaded.emit(path)

                # If loaded from library, update combo selection
                if self._is_library_item:
                    self._suppress_combo_signal = True
                    index = self._library_combo.findText(path.stem)
                    if index >= 0:
                        self._library_combo.setCurrentIndex(index)
                        self._prev_library_index = index
                    self._suppress_combo_signal = False

                self._update_button_states()
        except Exception as e:
            if self._log_error:
                self._log_error(f"Load failed: {e}")

    def _on_library_selection_changed(self, text: str) -> None:
        """Handle library combo selection change - auto-loads the selected item."""
        if self._suppress_combo_signal:
            self._update_button_states()
            return

        if not text:
            self._update_button_states()
            return

        path = self._library_dir / f"{text}{self._file_extension}"
        if not path.exists():
            self._update_button_states()
            return

        # Don't reload if this is already the current file
        if self._current_path == path:
            self._update_button_states()
            return

        new_index = self._library_combo.currentIndex()

        # Guard callback: ask about unsaved changes etc.
        if self._before_load is not None:
            if not self._before_load():
                # User cancelled – revert combo to previous selection
                self._suppress_combo_signal = True
                self._library_combo.setCurrentIndex(self._prev_library_index)
                self._suppress_combo_signal = False
                self._update_button_states()
                return

        # Proceed with load
        self._prev_library_index = new_index
        try:
            if self._on_load:
                self._on_load(path)
                self._current_path = path
                self._is_library_item = True

                if self._log_success:
                    self._log_success(f"Loaded from library: {text}")

                self.loaded.emit(path)
        except Exception as e:
            if self._log_error:
                self._log_error(f"Load from library failed: {e}")
            # Revert combo on failure
            self._suppress_combo_signal = True
            self._library_combo.setCurrentIndex(self._prev_library_index)
            self._suppress_combo_signal = False

        self._update_button_states()

    def _on_load_library_clicked(self) -> None:
        """Handle load library button click."""
        selected = self._library_combo.currentText()
        if not selected:
            return

        path = self._library_dir / f"{selected}{self._file_extension}"

        if not path.exists():
            if self._log_error:
                self._log_error(f"Library item not found: {selected}")
            self._refresh_library_list()
            return

        try:
            if self._on_load:
                self._on_load(path)
                self._current_path = path
                self._is_library_item = True

                if self._log_success:
                    self._log_success(f"Loaded from library: {selected}")

                self.loaded.emit(path)
                self._update_button_states()
        except Exception as e:
            if self._log_error:
                self._log_error(f"Load from library failed: {e}")

    def _on_store_clicked(self) -> None:
        """Handle store to library button click."""
        from PySide6.QtWidgets import QInputDialog

        # Prompt for name
        default_name = (
            self._current_path.stem if self._current_path
            else self._default_filename.replace(self._file_extension, "")
        )

        name, ok = QInputDialog.getText(
            self,
            "Store to Library",
            "Enter name for library item:",
            text=default_name,
        )

        if not ok or not name:
            return  # User cancelled

        # Ensure extension
        if not name.endswith(self._file_extension):
            name += self._file_extension

        path = self._library_dir / name

        # Check if exists
        if path.exists():
            reply = QMessageBox.question(
                self,
                "Overwrite?",
                f"Library item '{name}' already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        try:
            if self._on_save:
                self._on_save(path)
                self._current_path = path
                self._is_library_item = True

                if self._log_success:
                    self._log_success(f"Stored to library: {name}")

                self.saved.emit(path)

                # Refresh and select new item
                self._refresh_library_list(keep_selection=path.stem)
                self._suppress_combo_signal = True
                index = self._library_combo.findText(path.stem)
                if index >= 0:
                    self._library_combo.setCurrentIndex(index)
                    self._prev_library_index = index
                self._suppress_combo_signal = False

                self._update_button_states()
        except Exception as e:
            if self._log_error:
                self._log_error(f"Store to library failed: {e}")

    def _on_delete_clicked(self) -> None:
        """Handle delete library item button click."""
        selected = self._library_combo.currentText()
        if not selected:
            return

        # Confirm deletion
        reply = QMessageBox.warning(
            self,
            "Delete Library Item",
            f"Delete '{selected}' from library?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        path = self._library_dir / f"{selected}{self._file_extension}"

        try:
            if path.exists():
                path.unlink()

                if self._log_success:
                    self._log_success(f"Deleted from library: {selected}")

                # If deleted current file, clear current path
                if self._current_path == path:
                    self._current_path = None
                    self._is_library_item = False

                # Refresh list
                self._refresh_library_list()
                self._update_button_states()
        except Exception as e:
            if self._log_error:
                self._log_error(f"Delete failed: {e}")

    def set_current_path(self, path: Path | None, is_library: bool = False) -> None:
        """
        Set the current file path (e.g., after external load).

        Args:
            path: Current file path or None for new/unsaved
            is_library: True if path is in library directory
        """
        self._current_path = path
        self._is_library_item = is_library

        if is_library and path:
            self._suppress_combo_signal = True
            index = self._library_combo.findText(path.stem)
            if index >= 0:
                self._library_combo.setCurrentIndex(index)
                self._prev_library_index = index
            self._suppress_combo_signal = False

        self._update_button_states()

    def get_current_path(self) -> Path | None:
        """Get the current file path."""
        return self._current_path

    def refresh_library(self) -> None:
        """Refresh the library list (call after external changes)."""
        self._refresh_library_list()
