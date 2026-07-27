"""
LKS UI - Main Panel.

Main panel window with header, side ribbons (outliner LHS, log RHS),
center tabs, and footer.

Usage:
    from ui.ui_main import LKSMainPanel
    panel = LKSMainPanel()
    panel.show()
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
)
from PySide6.QtCore import Qt

from utils.ui.styles import DARK_STYLESHEET, COLOR_ACCENT
from utils.ui.widgets import TabWidget, ActivityLog, SideRibbon, Side, make_badge_button
from utils.ui.widgets.badge_button import _make_icon_from_svg
from utils.lks_settings import get_ui_state, save_ui_state
from utils.invocation_logger import get_invocation_logger


# =============================================================================
# CONSTANTS
# =============================================================================

BASE_PANEL_WIDTH: int = 350
BASE_PANEL_HEIGHT: int = 600
OUTLINER_RIBBON_WIDTH: int = 280
LOG_RIBBON_WIDTH: int = 320


def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


# =============================================================================
# LOG PROXY
# =============================================================================

class _LogProxy:
    """Delegates log calls to the current ActivityLog, surviving expand/collapse.

    Buffers messages when no target widget is connected yet (before the log
    ribbon has been expanded once). Buffered messages are flushed when a
    new target is set. Stays connected while the ribbon is collapsed so
    hidden ActivityLog still receives appends.

    Optional ``on_emit`` notifies after every write so a collapsed ribbon
    can pulse without forcing expansion.
    """

    def __init__(self) -> None:
        self._target: ActivityLog | None = None
        self._buffer: list[tuple[str, str]] = []  # (level, message)
        self._on_emit: Callable[[], None] | None = None

    def set_on_emit(self, callback: Callable[[], None] | None) -> None:
        """Set a no-arg callback invoked after each log write (any level)."""
        self._on_emit = callback

    def set_target(self, target: ActivityLog | None) -> None:
        self._target = target
        if target is not None and self._buffer:
            for level, message in self._buffer:
                _dispatch = getattr(target, f"log_{level}", target.log_info)
                _dispatch(message)
            self._buffer.clear()

    def _emit(self, level: str, message: str) -> None:
        if self._target is not None:
            _dispatch = getattr(self._target, f"log_{level}", self._target.log_info)
            _dispatch(message)
        else:
            self._buffer.append((level, message))
        if self._on_emit is not None:
            self._on_emit()

    def log_success(self, message: str) -> None:
        self._emit("success", message)

    def log_error(self, message: str) -> None:
        self._emit("error", message)

    def log_info(self, message: str) -> None:
        self._emit("info", message)

    def log_warn(self, message: str) -> None:
        self._emit("warn", message)

    def log_debug(self, message: str) -> None:
        self._emit("debug", message)

    def log_progress(self, message: str) -> None:
        """Log a progress/step message (info level, with arrow prefix)."""
        self._emit("info", f"  → {message}")

    # Convenience aliases for direct callable use
    def info(self) -> Callable[[str], None]:
        return self.log_info

    def warn(self) -> Callable[[str], None]:
        return self.log_warn

    def error(self) -> Callable[[str], None]:
        return self.log_error


# =============================================================================
# MAIN PANEL CLASS
# =============================================================================

class LKSMainPanel(QWidget):
    """Main LKS Tools panel with side ribbons (outliner LHS, log RHS)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LKS Tools")

        # Base size — ribbons add to this when expanded
        self._base_width: int = BASE_PANEL_WIDTH
        self._base_height: int = BASE_PANEL_HEIGHT
        self.resize(self._base_width, self._base_height)
        self.setMinimumSize(320, 500)

        # Apply "always on top" window flag if enabled in settings
        ui_state = get_ui_state()
        flags: Qt.WindowType = Qt.WindowType.Window
        if ui_state.panel_always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setStyleSheet(DARK_STYLESHEET)

        # Position window in top-left area of screen
        self.move(100, 100)

        self._refresh_tree: Callable[[], None] | None = None

        # Side ribbon instances (populated in _build_ui)
        self._lhs_ribbon: SideRibbon | None = None
        self._rhs_ribbon: SideRibbon | None = None

        # Track previous extra widths to compute delta on toggle
        self._prev_lhs_extra: int = 0
        self._prev_rhs_extra: int = 0

        self._build_ui()

    # =========================================================================
    # BUILD UI
    # =========================================================================

    def _build_ui(self) -> None:
        """Build the panel UI with side ribbons."""
        outer: QVBoxLayout = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # --- Header ---
        header: QWidget = self._create_header()
        outer.addWidget(header)

        # --- Log proxy (stays connected while RHS ribbon is collapsed) ---
        self._log = _LogProxy()
        self._log.set_on_emit(self._on_log_message_emitted)

        # --- Content row: LHS ribbon | center tabs | RHS ribbon ---
        content_row: QHBoxLayout = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        # LHS ribbon — outliner
        self._lhs_ribbon = SideRibbon(
            edge=Side.LEFT,
            label="Outliner",
            content_factory=self._create_outliner_factory(),
            on_toggled=self._recalc_window_size,
            expanded_width=OUTLINER_RIBBON_WIDTH,
        )
        content_row.addWidget(self._lhs_ribbon)

        # Center — tabs (stretch, but allow shrinking to 0 so ribbon
        # handle drags only squish the center, never grow the window)
        self._tabs: TabWidget = TabWidget()
        self._tabs.setMinimumWidth(0)
        self._load_tabs()
        content_row.addWidget(self._tabs, 1)

        # RHS ribbon — activity log
        self._rhs_ribbon = SideRibbon(
            edge=Side.RIGHT,
            label="Log",
            content_factory=self._create_log_factory(),
            on_toggled=self._recalc_window_size,
            expanded_width=LOG_RIBBON_WIDTH,
        )
        # Clear attention text tint when user expands; never detach the log proxy
        self._rhs_ribbon.toggled.connect(self._on_log_ribbon_toggled)
        content_row.addWidget(self._rhs_ribbon)

        outer.addLayout(content_row, 1)

        # Install global exception hook
        self._install_excepthook()

        # --- Footer ---
        footer: QWidget = self._create_footer()
        outer.addWidget(footer)

    # =========================================================================
    # CONTENT FACTORIES
    # =========================================================================

    def _create_outliner_factory(self) -> Callable[[], QWidget]:
        """Create a factory that builds a fresh outliner content widget."""
        log_ref: _LogProxy = self._log

        def factory() -> QWidget:
            from ui.ui_tab_outliner import create_outliner_tab
            widget, refresh_fn = create_outliner_tab(
                log_success=log_ref.log_success,
                log_error=log_ref.log_error,
            )
            widget._lks_refresh_fn = refresh_fn  # type: ignore[attr-defined]
            self._refresh_tree = refresh_fn
            return widget

        return factory

    def _create_log_factory(self) -> Callable[[], QWidget]:
        """Create a factory that builds a fresh ActivityLog widget."""
        log_ref: _LogProxy = self._log

        def factory() -> QWidget:
            new_log: ActivityLog = ActivityLog(
                max_lines=500,
                min_height=120,
                max_height=0,  # No max — fill the ribbon
            )
            new_log.setMinimumHeight(120)

            # Proxy + invocation logger stay pointed at this widget even
            # while the ribbon is later collapsed (content is only hidden).
            log_ref.set_target(new_log)
            get_invocation_logger().set_log_widget(log_ref)

            # Direct write (bypasses proxy) — no attention flash on first open
            new_log.log_success("Log ready")
            return new_log

        return factory

    # =========================================================================
    # HEADER / FOOTER
    # =========================================================================

    def _create_header(self) -> QWidget:
        """Create header with title and status."""
        container: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        title: QLabel = QLabel("LKS Tools")
        title.setToolTip("LKS sculpt tools panel for 3DCoat work")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #90caf9;")
        layout.addWidget(title)

        layout.addStretch()

        self._status_label: QLabel = QLabel("Ready")
        self._status_label.setToolTip("Current operation status")
        self._status_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._status_label)

        return container

    def _create_footer(self) -> QWidget:
        """Create footer with action buttons."""
        container: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Revert UI button (left-aligned)
        def _on_revert_ui() -> None:
            try:
                from utils.lks_settings import reset_ui_state
                reset_ui_state()
                self._log.log_success("UI state reverted to defaults. Restart panel to apply.")
            except Exception as e:
                self._log.log_error(f"Failed to revert UI state: {e}")

        revert_btn = make_badge_button(
            icon_name="revert",
            text="Revert UI",
            tooltip=_load_ui_tooltip("revert_ui.md"),
            color="#888",
        )
        revert_btn.clicked.connect(_on_revert_ui)
        layout.addWidget(revert_btn)

        layout.addStretch()

        # Always on top pin button (toggle) — uses theme COLOR_ACCENT
        ui_state = get_ui_state()
        pinned: bool = ui_state.panel_always_on_top

        # Pre-render both icon states so we can swap on toggle
        self._pin_icon_outline = _make_icon_from_svg("pin", color=COLOR_ACCENT)
        self._pin_icon_filled = _make_icon_from_svg("pin_filled", color=COLOR_ACCENT)

        pin_btn = make_badge_button(
            icon_name="pin",
            text="Pin",
            tooltip=_load_ui_tooltip("pin_button.md"),
            color=COLOR_ACCENT,
        )
        pin_btn.setCheckable(True)
        pin_btn.setChecked(pinned)
        pin_btn.setIcon(self._pin_icon_filled if pinned else self._pin_icon_outline)
        pin_btn.toggled.connect(self._toggle_pin)
        layout.addWidget(pin_btn)

        return container

    # =========================================================================
    # WINDOW RESIZE
    # =========================================================================

    def _recalc_window_size(self) -> None:
        """Resize the window horizontally when ribbons expand/collapse.

        When the LHS outliner expands/collapses, the window x-position is
        adjusted so the ribbon stays anchored at its original screen position.
        The LHS panel content appears to the left of the ribbon (via
        expand_direction="left"), so the window must shift left by the same
        amount to keep the ribbon in place.
        """
        lhs_expanded: bool = (
            self._lhs_ribbon is not None and self._lhs_ribbon.is_expanded
        )
        rhs_expanded: bool = (
            self._rhs_ribbon is not None and self._rhs_ribbon.is_expanded
        )

        lhs_extra: int = OUTLINER_RIBBON_WIDTH if lhs_expanded else 0
        rhs_extra: int = LOG_RIBBON_WIDTH if rhs_expanded else 0

        lhs_delta: int = lhs_extra - self._prev_lhs_extra
        rhs_delta: int = rhs_extra - self._prev_rhs_extra
        width_delta: int = lhs_delta + rhs_delta

        if width_delta == 0:
            return

        frame_x: int = self.x()
        frame_y: int = self.y()
        geo_w: int = self.geometry().width()
        geo_h: int = self.geometry().height()
        # Batch resize+reposition into a single paint cycle to avoid
        # a one-frame flash of the intermediate state.
        self.setUpdatesEnabled(False)
        self.resize(geo_w + width_delta, geo_h)
        if lhs_delta != 0:
            self.move(frame_x - lhs_delta, frame_y)
        self.setUpdatesEnabled(True)
        self._prev_lhs_extra = lhs_extra
        self._prev_rhs_extra = rhs_extra

    # =========================================================================
    # TABS
    # =========================================================================

    def _load_tabs(self) -> None:
        """Load tab modules (excluding outliner, which is in a side ribbon)."""
        log: _LogProxy = self._log

        # Getting Started Tab (always first, default on first launch)
        from ui.ui_tab_getting_started import create_getting_started_tab
        getting_started_tab: QWidget | None = create_getting_started_tab()
        if getting_started_tab is not None:
            idx: int = self._tabs.add_tab("Getting Started", getting_started_tab)
            self._tabs.set_tab_icon(idx, _make_icon_from_svg("home", color="#90caf9"))
            self._getting_started_idx: int = idx

        # Tools Tab
        from ui.ui_tab_tools import create_tools_tab
        tools_tab: QWidget = create_tools_tab(
            log_success=log.log_success,
            log_error=log.log_error,
            log_info=log.log_info,
            refresh_tree=self._do_refresh_tree,
        )
        idx = self._tabs.add_tab("Tools", tools_tab)
        self._tabs.set_tab_icon(idx, _make_icon_from_svg("wrench", color="#90caf9"))

        # Radial Menu Tab
        from ui.ui_tab_radial_menu import create_radial_menu_tab
        radial_tab: QWidget = create_radial_menu_tab(
            log_success=log.log_success,
            log_error=log.log_error,
        )
        idx = self._tabs.add_tab("Radial", radial_tab)
        self._tabs.set_tab_icon(idx, _make_icon_from_svg("radial", color="#90caf9"))

        # Hotkey Tab
        from ui.ui_tab_hotkey import create_hotkey_tab
        hotkey_tab: QWidget = create_hotkey_tab(
            log_success=log.log_success,
            log_error=log.log_error,
            log_info=log.log_info,
            log_warn=log.log_warn,
            parent=self,
        )
        idx = self._tabs.add_tab("Hotkey", hotkey_tab)
        self._tabs.set_tab_icon(idx, _make_icon_from_svg("hotkey", color="#90caf9"))

        # Install Tab
        from ui.ui_tab_install import create_install_tab
        install_tab: QWidget = create_install_tab(
            log_success=log.log_success,
            log_error=log.log_error,
            log_info=log.log_info,
            log_warn=log.log_warn,
        )
        idx = self._tabs.add_tab("Install", install_tab)
        self._tabs.set_tab_icon(idx, _make_icon_from_svg("install", color="#90caf9"))

        # Dev Tab
        from ui.ui_tab_dev import create_dev_tab
        dev_tab: QWidget = create_dev_tab(
            log_success=log.log_success,
            log_error=log.log_error,
            log_info=log.log_info,
            log_warn=log.log_warn,
            panel=self,
        )
        idx = self._tabs.add_tab("Dev", dev_tab)
        self._tabs.set_tab_icon(idx, _make_icon_from_svg("dev", color="#90caf9"))

        # ── First-launch & active-tab persistence ──────────────────────
        self._tabs.tab_changed.connect(self._on_active_tab_changed)

        ui_state = get_ui_state()
        if not ui_state.panel_has_been_launched:
            ui_state.panel_has_been_launched = True
            ui_state.active_tab_index = 0
            save_ui_state()
            self._tabs.set_current_index(0)
        else:
            last_idx: int = int(ui_state.active_tab_index)
            tab_count: int = self._tabs.tab_count()
            if 0 <= last_idx < tab_count:
                self._tabs.set_current_index(last_idx)

    def _on_active_tab_changed(self, index: int) -> None:
        """Persist the active tab index across sessions."""
        try:
            ui_state = get_ui_state()
            ui_state.active_tab_index = index
            save_ui_state()
        except Exception:
            pass  # Best-effort — don't let persistence failure block the UI

    # =========================================================================
    # EXCEPTION HOOK
    # =========================================================================

    def _install_excepthook(self) -> None:
        """Install a global exception hook routing errors to the log."""
        import sys
        import traceback

        log_ref: _LogProxy = self._log

        def _lks_excepthook(
            exc_type: type,
            exc_value: BaseException,
            exc_tb: object,
        ) -> None:
            tb_lines: list[str] = traceback.format_exception(
                exc_type, exc_value, exc_tb
            )
            full_text: str = "".join(tb_lines)
            for line in full_text.rstrip().splitlines():
                if line.strip():
                    log_ref.log_error(line)
            sys.__excepthook__(exc_type, exc_value, exc_tb)

        sys.excepthook = _lks_excepthook

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def _on_log_message_emitted(self) -> None:
        """Pulse the RHS Log ribbon when a message arrives while collapsed."""
        if self._rhs_ribbon is not None and not self._rhs_ribbon.is_expanded:
            self._rhs_ribbon.signal_attention()

    def _on_log_ribbon_toggled(self, expanded: bool) -> None:
        """Clear unread attention when the log ribbon expands.

        Content is hidden on collapse, not destroyed. The log proxy and
        invocation logger stay connected so appends reach the hidden
        ActivityLog; only the ribbon label attention tint is cleared here.
        """
        if expanded and self._rhs_ribbon is not None:
            self._rhs_ribbon.clear_attention()

    def _toggle_pin(self, pinned: bool) -> None:
        """Toggle always-on-top window flag, icon, and save to settings."""
        ui_state = get_ui_state()
        ui_state.panel_always_on_top = pinned
        save_ui_state()

        # Swap icon between filled and outline to show state
        btn = self.sender()
        if btn is not None and hasattr(self, "_pin_icon_filled"):
            btn.setIcon(self._pin_icon_filled if pinned else self._pin_icon_outline)

        flags: Qt.WindowType = Qt.WindowType.Window
        if pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.show()
        self._recalc_window_size()
        self._log.log_success(
            f"Panel {'pinned' if pinned else 'unpinned'}")

    def _do_refresh_tree(self) -> None:
        """Refresh the outliner tree (only when expanded)."""
        if self._lhs_ribbon and self._lhs_ribbon.is_expanded and self._refresh_tree:
            self._refresh_tree()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def log_info(self, text: str) -> None:
        self._log.log_info(text)

    def log_success(self, text: str) -> None:
        self._log.log_success(text)

    def log_error(self, text: str) -> None:
        self._log.log_error(text)

    def log_warn(self, text: str) -> None:
        self._log.log_warn(text)

    def refresh_tree(self) -> None:
        """Public method to refresh the outliner tree."""
        self._do_refresh_tree()

    def rebuild_ui(self) -> None:
        """
        Rebuild all tab and ribbon content with freshly imported module code.

        This is called after a hot-reload to pick up UI code changes without
        closing and reopening the panel window. All existing tabs and ribbons
        are destroyed and recreated from the reloaded modules.
        """
        # Save current tab index (defensive: current_index may not exist on all TabWidget versions)
        try:
            current_idx: int = self._tabs.current_index()
        except AttributeError:
            current_idx = 0

        # --- Rebuild tabs ---
        while self._tabs.tab_count() > 0:
            self._tabs.remove_tab(0)
        self._load_tabs()

        # Restore tab index if still valid, otherwise default to first tab
        if 0 <= current_idx < self._tabs.tab_count():
            self._tabs.set_current_index(current_idx)

        # --- Refresh outliner if expanded ---
        self._do_refresh_tree()

        self._log.log_success("Panel rebuilt with updated code")
