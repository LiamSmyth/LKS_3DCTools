"""
LKS UI - Install Tab.

Shows all LKS action scripts and radial menus with their install status
in 3DCoat's Scripts menu. Provides per-item and batch install/uninstall.

Usage:
    from ui.ui_tab_install import create_install_tab
    tab = create_install_tab(log_success, log_error, log_info, log_warn)
    tabs.add_tab("Install", tab)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from pathlib import Path
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor

from utils.ui.widgets import (
    CollapsibleSection, ButtonGrid,
)
from utils.ui.widgets.sub_header import create_sub_header
from utils.ui.widgets.tab_container import StandardTabBody
from utils.action_discovery import discover_actions, EXCLUDED_SCRIPTS, ActionInfo


# =============================================================================
# HELP TEXT
# =============================================================================

def _load_ui_tooltip(filename: str) -> str:
    """Load HTML help text from ui/data/tooltips/."""
    from utils.ui.widgets.text_resource import TextResource
    return TextResource(f"data/tooltips/{filename}", base_dir=__file__).text


# =============================================================================
# DATA TYPES
# =============================================================================

@dataclass
class _InstallItem:
    """Uniform representation of an installable item (action script or radial menu)."""
    name: str
    installed: bool
    on_install: Callable[[], None] | None = None
    on_uninstall: Callable[[], None] | None = None
    uninstall_warning: str | None = None


# =============================================================================
# WARNING BANNER
# =============================================================================

def _create_warning_banner() -> tuple[QWidget, Callable[[], None]]:
    """Create a restart-warning banner (hidden by default).

    Returns:
        Tuple of (banner_widget, show_warning_callback)
    """
    banner: QWidget = QWidget()
    banner.setVisible(False)
    banner.setStyleSheet(f"""
        QWidget {{
            background-color: {_BANNER_BG};
            border: 1px solid {_BANNER_BORDER};
            border-radius: 4px;
        }}
    """)

    layout: QHBoxLayout = QHBoxLayout(banner)
    layout.setContentsMargins(8, 4, 4, 4)
    layout.setSpacing(6)

    icon: QLabel = QLabel("⚠")
    icon.setStyleSheet(f"font-size: {_BANNER_ICON_SIZE}; border: none;")
    icon.setFixedWidth(_BANNER_ICON_W)
    layout.addWidget(icon)

    msg: QLabel = QLabel("Restart 3DCoat for menu installation changes to take effect.")
    msg.setStyleSheet(f"color: {_BANNER_MSG_COLOR}; font-size: {_BANNER_MSG_SIZE}; border: none;")
    msg.setWordWrap(True)
    layout.addWidget(msg, 1)

    dismiss_btn: QPushButton = QPushButton("✕")
    dismiss_btn.setFixedSize(_BANNER_DISMISS_WH, _BANNER_DISMISS_WH)
    dismiss_btn.setToolTip("Dismiss this warning message")
    dismiss_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent; color: {_BANNER_DISMISS_COLOR};
            border: none; font-size: {_BANNER_DISMISS_SIZE};
        }}
        QPushButton:hover {{ color: {_BANNER_MSG_COLOR}; }}
    """)
    dismiss_btn.clicked.connect(lambda: banner.setVisible(False))
    layout.addWidget(dismiss_btn)

    def show_warning() -> None:
        banner.setVisible(True)

    return banner, show_warning


# =============================================================================
# PATH HELPERS
# =============================================================================

def _get_lks_root() -> Path:
    """Get LKS cModule root directory."""
    return Path(__file__).parent.parent.resolve()


def _get_actions_dir() -> Path:
    """Get actions directory."""
    return _get_lks_root() / "actions"


def _get_radial_library_dir() -> Path:
    """Get radial menus library directory."""
    return _get_lks_root() / "data" / "library" / "radial_menus"


def _maybe_show_restart_on_mismatch(show_restart_warning: Callable[[], None]) -> bool:
    """Show restart banner when disk and live menu state disagree."""
    from utils.menu_cleanup import has_disk_live_mismatch
    if has_disk_live_mismatch():
        show_restart_warning()
        return True
    return False


def _log_uninstall_result(
    result: object,
    log_success: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    show_restart_warning: Callable[[], None],
    label: str,
) -> None:
    """Log MenuUninstallResult fields and surface restart when needed."""
    from utils.menu_cleanup import MenuUninstallResult

    if not isinstance(result, MenuUninstallResult):
        return

    if result.deleted_xml:
        log_success(f"{label}: deleted {result.deleted_count} XML file(s)")
        for name in result.deleted_xml[:5]:
            log_info(f"  - {name}")
        if len(result.deleted_xml) > 5:
            log_info(f"  ... and {len(result.deleted_xml) - 5} more")
    else:
        log_info(f"{label}: no XML files deleted")

    if result.unregistered_radials:
        log_success(
            f"Unregistered {len(result.unregistered_radials)} radial menu(s)"
        )
        for name in result.unregistered_radials[:5]:
            log_info(f"  - {name}")
        if len(result.unregistered_radials) > 5:
            log_info(f"  ... and {len(result.unregistered_radials) - 5} more")

    if result.live_pending_restart:
        log_warn(
            f"{len(result.live_pending_restart)} live menu item(s) remain "
            "until 3DCoat restart."
        )
        for menu_id in result.live_pending_restart[:5]:
            log_info(f"  - {menu_id}")
        if len(result.live_pending_restart) > 5:
            log_info(f"  ... and {len(result.live_pending_restart) - 5} more")

    if result.needs_restart:
        show_restart_warning()


# =============================================================================
# TABLE LAYOUT (shared by Action Scripts and Radial Menus sections)
# =============================================================================

# Fixed column widths for uniform alignment (matching outliner compact style)
_COL_NAME_W: int = 200
_COL_STATUS_W: int = 50
_COL_BUTTON_W: int = 80
_TABLE_MAX_HEIGHT: int = 300
_BUTTON_H_PAD: int = 8  # Horizontal padding within button column

# Tree widget text sizing (matches outliner)
_TREE_FONT_SIZE: str = "10px"
_TREE_ITEM_PADDING: str = "0px 2px"
_HEADER_PADDING: str = "1px 2px"
_HEADER_FONT_SIZE: str = "9px"

_TABLE_STYLESHEET: str = (
    f"QTreeWidget {{ font-size: {_TREE_FONT_SIZE}; }}"
    f"QTreeWidget::item {{ padding: {_TREE_ITEM_PADDING}; }}"
    f"QHeaderView::section {{ padding: {_HEADER_PADDING}; font-size: {_HEADER_FONT_SIZE}; }}"
)

# =============================================================================
# WARNING BANNER COLORS
# =============================================================================

_BANNER_BG: str = "#5d4037"
_BANNER_BORDER: str = "#8d6e63"
_BANNER_ICON_SIZE: str = "14px"
_BANNER_ICON_W: int = 20
_BANNER_MSG_COLOR: str = "#ffcc80"
_BANNER_MSG_SIZE: str = "11px"
_BANNER_DISMISS_COLOR: str = "#bcaaa4"
_BANNER_DISMISS_SIZE: str = "12px"
_BANNER_DISMISS_WH: int = 20

# =============================================================================
# ACTION BUTTON COLORS
# =============================================================================

_UNINSTALL_BG: str = "#c62828"
_UNINSTALL_BG_HOVER: str = "#e53935"
_UNINSTALL_BORDER: str = "#e53935"
_INSTALL_BG: str = "#2e7d32"
_INSTALL_BG_HOVER: str = "#43a047"
_INSTALL_BORDER: str = "#43a047"
_BTN_TEXT_COLOR: str = "#fff"
_BTN_BORDER_RADIUS: str = "3px"
_BTN_PADDING: str = "2px 6px"
_BTN_FONT_SIZE: str = "10px"

# Status colors
_STATUS_INSTALLED_COLOR: str = "#81c784"
_STATUS_UNINSTALLED_COLOR: str = "#ffb74d"
_STATUS_UNINSTALLED_NAME_COLOR: str = "#888888"


def _make_action_button(
    installed: bool,
    on_install: Callable[[], None] | None,
    on_uninstall: Callable[[], None] | None,
    uninstall_warning: str | None,
) -> QPushButton | None:
    """Create an Install or Uninstall button, or None if no action is available."""
    if installed and on_uninstall is not None:
        btn: QPushButton = QPushButton("Uninstall")
        btn.setFixedWidth(_COL_BUTTON_W - _BUTTON_H_PAD)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_UNINSTALL_BG}; color: {_BTN_TEXT_COLOR};
                border: 1px solid {_UNINSTALL_BORDER}; border-radius: {_BTN_BORDER_RADIUS};
                padding: {_BTN_PADDING}; font-size: {_BTN_FONT_SIZE};
            }}
            QPushButton:hover {{ background-color: {_UNINSTALL_BG_HOVER}; }}
        """)
        if uninstall_warning:
            btn.setToolTip(uninstall_warning)
        btn.clicked.connect(on_uninstall)
        return btn
    elif not installed and on_install is not None:
        btn = QPushButton("Install")
        btn.setFixedWidth(_COL_BUTTON_W - _BUTTON_H_PAD)
        btn.setToolTip("Install this item in 3DCoat's Scripts menu")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_INSTALL_BG}; color: {_BTN_TEXT_COLOR};
                border: 1px solid {_INSTALL_BORDER}; border-radius: {_BTN_BORDER_RADIUS};
                padding: {_BTN_PADDING}; font-size: {_BTN_FONT_SIZE};
            }}
            QPushButton:hover {{ background-color: {_INSTALL_BG_HOVER}; }}
        """)
        btn.clicked.connect(on_install)
        return btn
    return None


def _create_install_tree(items: list[_InstallItem]) -> QTreeWidget:
    """Build a QTreeWidget with labeled column headers: Name | Status | (Actions).

    Matches the outliner's compact table pattern: column headers, alternating
    row colors, small font/padding, and per-row inline action buttons.
    """
    tree: QTreeWidget = QTreeWidget()
    tree.setHeaderLabels(["Name", "Status", ""])
    tree.setAlternatingRowColors(True)
    tree.setRootIsDecorated(False)
    tree.setIndentation(0)
    tree.setColumnWidth(0, _COL_NAME_W)
    tree.setColumnWidth(1, _COL_STATUS_W)
    tree.setColumnWidth(2, _COL_BUTTON_W)
    tree.setMaximumHeight(_TABLE_MAX_HEIGHT)
    tree.setStyleSheet(_TABLE_STYLESHEET)

    # Stretch the name column to fill available space
    header: QHeaderView | None = tree.header()
    if header is not None:
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)

    for item_data in items:
        tree_item: QTreeWidgetItem = QTreeWidgetItem()
        tree_item.setText(0, item_data.name)

        # Status column: checkmark (green) or cross (orange), centered
        status_text: str = "✓" if item_data.installed else "✗"
        status_color: str = _STATUS_INSTALLED_COLOR if item_data.installed else _STATUS_UNINSTALLED_COLOR
        tree_item.setText(1, status_text)
        tree_item.setForeground(1, QBrush(QColor(status_color)))
        tree_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)

        # Muted name color for uninstalled items
        if not item_data.installed:
            tree_item.setForeground(0, QBrush(QColor(_STATUS_UNINSTALLED_NAME_COLOR)))

        tree.addTopLevelItem(tree_item)

        # Inline action button in column 2
        btn: QPushButton | None = _make_action_button(
            item_data.installed, item_data.on_install,
            item_data.on_uninstall, item_data.uninstall_warning,
        )
        if btn is not None:
            tree.setItemWidget(tree_item, 2, btn)

    return tree


def _replace_tree_in_section(section: CollapsibleSection, tree: QTreeWidget) -> None:
    """Remove any existing QTreeWidget from a section and add the new one."""
    layout: QVBoxLayout = section.content_layout
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if item is not None:
            w = item.widget()
            if isinstance(w, QTreeWidget):
                old = layout.takeAt(i)
                if old is not None:
                    ow = old.widget()
                    if ow is not None:
                        ow.deleteLater()
                    del old
    layout.addWidget(tree)


# =============================================================================
# SECTION BUILDERS
# =============================================================================

def _build_action_scripts_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    show_restart_warning: Callable[[], None],
) -> tuple[CollapsibleSection, Callable[[], None]]:
    """Build Action Scripts section; status reflects ExtraMenuItems XML on disk."""
    section: CollapsibleSection = CollapsibleSection(
        title="Action Scripts",
        color="#64b5f6",
        collapsed=False,
        help_text=_load_ui_tooltip("install_action_scripts.md"),
    )

    actions_dir: Path = _get_actions_dir()
    all_actions: list[ActionInfo] = discover_actions(actions_dir)

    filtered_actions: list[ActionInfo] = [
        a for a in all_actions
        if a.filename not in EXCLUDED_SCRIPTS
        and not a.filename.startswith("LKS_")
    ]

    def _rebuild_action_table() -> None:
        """Rebuild the table from disk; show restart banner on disk/live mismatch."""
        items = _build_items()
        tree = _create_install_tree(items)
        _replace_tree_in_section(section, tree)
        _maybe_show_restart_on_mismatch(show_restart_warning)

    def _build_items() -> list[_InstallItem]:
        from utils.menu_cleanup import menu_xml_exists

        items: list[_InstallItem] = []
        for a in filtered_actions:
            is_installed: bool = menu_xml_exists(a.menu_id)
            if is_installed:
                def make_uninstall_cb(act: ActionInfo) -> Callable[[], None]:
                    def cb() -> None:
                        try:
                            import coat
                            from utils.menu_cleanup import delete_single_menu_xml

                            deleted: bool = delete_single_menu_xml(act.menu_id)
                            if deleted:
                                log_success(f"Uninstalled: {act.display_name}")
                            else:
                                log_warn(
                                    f"No XML file for {act.display_name}."
                                )

                            still_live: bool = False
                            try:
                                still_live = bool(
                                    coat.ui.checkIfMenuItemInserted(act.menu_id)
                                )
                            except Exception:
                                still_live = False

                            if still_live:
                                log_warn(
                                    f"{act.display_name} is still in the live "
                                    "Scripts menu — restart 3DCoat to clear it."
                                )
                                show_restart_warning()

                            _rebuild_action_table()
                        except Exception as e:
                            log_error(f"Failed to uninstall {act.display_name}: {e}")
                    return cb
                items.append(_InstallItem(
                    name=a.display_name,
                    installed=True,
                    on_uninstall=make_uninstall_cb(a),
                    uninstall_warning="Requires 3DCoat restart to take effect",
                ))
            else:
                def make_install_cb(act: ActionInfo) -> Callable[[], None]:
                    def cb() -> None:
                        try:
                            from utils.coat_menu_utils import register_action
                            from utils.menu_cleanup import menu_xml_exists

                            register_action(
                                menu_id=act.menu_id,
                                display_name=act.display_name,
                                script_path=act.path,
                                force=not menu_xml_exists(act.menu_id),
                            )
                            if menu_xml_exists(act.menu_id):
                                log_success(f"Installed: {act.display_name}")
                            else:
                                log_warn(
                                    f"Registered live: {act.display_name}, but "
                                    "ExtraMenuItems XML not on disk yet. Status "
                                    "stays ✗ until 3DCoat writes the file "
                                    "(restart may be needed)."
                                )
                                show_restart_warning()
                            _rebuild_action_table()
                        except Exception as e:
                            log_error(f"Failed to install {act.display_name}: {e}")
                    return cb
                items.append(_InstallItem(
                    name=a.display_name,
                    installed=False,
                    on_install=make_install_cb(a),
                ))
        return items

    # --- Toolbar ---
    toolbar_grid: ButtonGrid = ButtonGrid(columns=2)

    def on_install_all() -> None:
        try:
            from utils.coat_menu_utils import register_action
            from utils.menu_cleanup import menu_xml_exists

            installed_count: int = 0
            skipped_count: int = 0
            for a in filtered_actions:
                # Skip only when XML already on disk; force rewrite otherwise
                if menu_xml_exists(a.menu_id):
                    skipped_count += 1
                    continue
                if register_action(
                    menu_id=a.menu_id,
                    display_name=a.display_name,
                    script_path=a.path,
                    force=True,
                ):
                    installed_count += 1
                else:
                    skipped_count += 1
            log_success(
                f"Installed {installed_count} action scripts"
                + (f", {skipped_count} already installed" if skipped_count else "")
            )
            _rebuild_action_table()
        except Exception as e:
            log_error(f"Install all failed: {e}")

    def on_uninstall_all() -> None:
        """Delete ExtraMenuItems XML for filtered action scripts only (not radials)."""
        try:
            import coat
            from utils.menu_cleanup import delete_single_menu_xml

            deleted_count: int = 0
            live_remaining: list[str] = []
            for a in filtered_actions:
                if delete_single_menu_xml(a.menu_id):
                    deleted_count += 1
                try:
                    if coat.ui.checkIfMenuItemInserted(a.menu_id):
                        live_remaining.append(a.menu_id)
                except Exception:
                    pass

            if deleted_count > 0:
                log_success(
                    f"Uninstalled {deleted_count} action-script menu XML file(s)."
                )
            else:
                log_info("No action-script menu XML files to delete.")

            if live_remaining:
                log_warn(
                    f"{len(live_remaining)} action(s) still live in Scripts — "
                    "restart 3DCoat to clear them."
                )
                show_restart_warning()

            _rebuild_action_table()
        except Exception as e:
            log_error(f"Uninstall all actions failed: {e}")

    toolbar_grid.add_button(
        "Install All",
        on_install_all,
        "Install all action scripts as Scripts menu items",
    )
    toolbar_grid.add_button(
        "Uninstall All",
        on_uninstall_all,
        "Delete ExtraMenuItems XML for all action scripts (not radial menus)",
    )
    section.content_layout.addWidget(toolbar_grid)

    # --- Initial table ---
    tree: QTreeWidget = _create_install_tree(_build_items())
    section.content_layout.addWidget(tree)

    return section, _rebuild_action_table


def _build_radial_menus_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    show_restart_warning: Callable[[], None],
) -> tuple[CollapsibleSection, Callable[[], None]]:
    """Build Radial Menus section; status uses registry (disk) state."""
    section: CollapsibleSection = CollapsibleSection(
        title="Radial Menus",
        color="#ce93d8",
        collapsed=False,
        help_text=_load_ui_tooltip("install_radial_menus.md"),
    )

    library_dir: Path = _get_radial_library_dir()
    menu_files: list[Path] = []
    if library_dir.exists():
        menu_files = sorted(
            [f for f in library_dir.glob("*.json") if f.name != "README.md"],
            key=lambda p: p.name,
        )

    menu_infos: list[tuple[str, str]] = []  # (filename, display_name)
    for menu_file in menu_files:
        try:
            with open(menu_file, "r", encoding="utf-8") as f:
                config_data: dict = json.load(f)
            display_name: str = config_data.get("name", menu_file.stem)
        except Exception:
            display_name = menu_file.stem
        menu_infos.append((menu_file.name, display_name))

    def _rebuild_radial_table() -> None:
        items = _build_items()
        tree = _create_install_tree(items)
        _replace_tree_in_section(section, tree)
        _maybe_show_restart_on_mismatch(show_restart_warning)

    def _build_items() -> list[_InstallItem]:
        from utils.radial_menu_registry import is_menu_registered

        items: list[_InstallItem] = []
        for filename, display_name in menu_infos:
            is_installed: bool = is_menu_registered(filename)
            if is_installed:
                def make_uninstall_cb(fn: str, dn: str) -> Callable[[], None]:
                    def cb() -> None:
                        try:
                            from utils.radial_menu_registry import unregister_menu
                            unregister_menu(fn)
                            log_success(f"Uninstalled radial menu: {dn}")
                            _rebuild_radial_table()
                        except Exception as e:
                            log_error(f"Failed to uninstall {dn}: {e}")
                    return cb
                items.append(_InstallItem(
                    name=display_name,
                    installed=True,
                    on_uninstall=make_uninstall_cb(filename, display_name),
                    uninstall_warning="Menu item XML persists until 3DCoat restart",
                ))
            else:
                def make_install_cb(fn: str, dn: str) -> Callable[[], None]:
                    def cb() -> None:
                        try:
                            from utils.radial_menu_registry import register_menu
                            register_menu(fn, dn)
                            log_success(f"Installed radial menu: {dn}")
                            _rebuild_radial_table()
                        except Exception as e:
                            log_error(f"Failed to install {dn}: {e}")
                    return cb
                items.append(_InstallItem(
                    name=display_name,
                    installed=False,
                    on_install=make_install_cb(filename, display_name),
                ))
        return items

    # --- Toolbar ---
    toolbar_grid: ButtonGrid = ButtonGrid(columns=3)

    def on_install_all_radial() -> None:
        try:
            from utils.radial_menu_registry import register_menu
            installed: int = 0
            skipped: int = 0
            for filename, display_name in menu_infos:
                if register_menu(filename, display_name):
                    installed += 1
                else:
                    skipped += 1
            log_success(
                f"Installed {installed} radial menus"
                + (f", {skipped} already installed" if skipped else "")
            )
            _rebuild_radial_table()
        except Exception as e:
            log_error(f"Install all radial menus failed: {e}")

    def on_uninstall_all_radial() -> None:
        try:
            from utils.radial_menu_registry import unregister_all_menus
            count: int = unregister_all_menus()
            if count > 0:
                log_warn(
                    f"Uninstalled {count} radial menus. "
                    "Menu item XML persists until 3DCoat restart."
                )
            else:
                log_info("No radial menus to uninstall.")
            _rebuild_radial_table()
        except Exception as e:
            log_error(f"Uninstall all radial menus failed: {e}")

    def on_sync_all() -> None:
        try:
            from utils.radial_menu_registry import sync_all_menus
            registered: int
            unregistered: int
            updated: int
            registered, unregistered, updated = sync_all_menus()
            parts: list[str] = []
            if registered:
                parts.append(f"{registered} registered")
            if unregistered:
                parts.append(f"{unregistered} unregistered")
            if updated:
                parts.append(f"{updated} updated")
            log_success(f"Sync complete: {', '.join(parts) if parts else 'no changes'}")
            _rebuild_radial_table()
        except Exception as e:
            log_error(f"Sync failed: {e}")

    toolbar_grid.add_button(
        "Install All",
        on_install_all_radial,
        "Install all radial menus as hotkey-assignable actions",
    )
    toolbar_grid.add_button(
        "Uninstall All",
        on_uninstall_all_radial,
        "Uninstall all radial menus (menu XML persists until 3DCoat restart)",
    )
    toolbar_grid.add_button(
        "Sync All",
        on_sync_all,
        "Sync library with registry (register new, unregister removed, update existing)",
    )
    section.content_layout.addWidget(toolbar_grid)

    # --- Initial table ---
    tree: QTreeWidget = _create_install_tree(_build_items())
    section.content_layout.addWidget(tree)

    return section, _rebuild_radial_table


def _build_menu_cleanup_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
    show_restart_warning: Callable[[], None],
    refresh_actions: Callable[[], None],
    refresh_radials: Callable[[], None],
) -> CollapsibleSection:
    """Build Menu Cleanup section: uninstall orphans or all LKS menus."""
    section: CollapsibleSection = CollapsibleSection(
        title="Menu Cleanup",
        color="#888",
        collapsed=False,
        help_text=_load_ui_tooltip("install_menu_cleanup.md"),
    )

    cleanup_grid: ButtonGrid = ButtonGrid(columns=2)

    def _refresh_tables() -> None:
        refresh_actions()
        refresh_radials()

    def on_uninstall_orphans() -> None:
        try:
            from utils.menu_cleanup import uninstall_orphans

            result = uninstall_orphans()
            _log_uninstall_result(
                result,
                log_success,
                log_info,
                log_warn,
                show_restart_warning,
                label="Uninstall orphans",
            )
            if (
                not result.deleted_xml
                and not result.unregistered_radials
                and not result.live_pending_restart
            ):
                log_info("No orphan LKS menu registrations found.")
            _refresh_tables()
        except Exception as e:
            log_error(f"Uninstall orphans failed: {e}")

    def on_uninstall_all() -> None:
        try:
            from utils.menu_cleanup import uninstall_all_lks_menus

            result = uninstall_all_lks_menus()
            _log_uninstall_result(
                result,
                log_success,
                log_info,
                log_warn,
                show_restart_warning,
                label="Uninstall all LKS menus",
            )
            if (
                not result.deleted_xml
                and not result.unregistered_radials
                and not result.live_pending_restart
            ):
                log_info("No LKS menu registrations to uninstall.")
            _refresh_tables()
        except Exception as e:
            log_error(f"Uninstall all failed: {e}")

    cleanup_grid.add_button(
        "Uninstall Orphans",
        on_uninstall_orphans,
        "Delete LKS menu XML / unregister radials that no longer point at valid scripts",
    )
    cleanup_grid.add_button(
        "Uninstall All",
        on_uninstall_all,
        "Delete all LKS_*.xml and unregister all radial menus (restart to clear live items)",
    )
    section.content_layout.addWidget(cleanup_grid)

    return section


# =============================================================================
# TAB FACTORY
# =============================================================================

def create_install_tab(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    log_info: Callable[[str], None],
    log_warn: Callable[[str], None],
) -> QWidget:
    """
    Create the Install tab for managing LKS menu item installation.

    Contains three collapsible sections:
    - Action Scripts: Per-script install/uninstall (disk XML status)
    - Radial Menus: Per-menu install/uninstall with sync
    - Menu Cleanup: Orphan and full LKS menu uninstall

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        log_info: Callback for info messages
        log_warn: Callback for warning messages

    Returns:
        QWidget containing the Install tab
    """
    body: StandardTabBody = StandardTabBody(
        title="Install",
        info_tooltip=_load_ui_tooltip("install_tab.md"),
    )

    # Clarifying sub-header
    body.content_layout.addWidget(
        create_sub_header(
            "Adds custom LKS items to 3DCoat's Scripts menu (for hotkeys)"
        )
    )

    # --- Restart warning banner (shown after mismatch / uninstall) ---
    warning_banner, show_restart_warning = _create_warning_banner()
    body.content_layout.addWidget(warning_banner)

    # --- Action Scripts Section ---
    action_section: CollapsibleSection
    refresh_actions: Callable[[], None]
    action_section, refresh_actions = _build_action_scripts_section(
        log_success, log_error, log_info, log_warn, show_restart_warning,
    )
    body.content_layout.addWidget(action_section)

    # --- Radial Menus Section ---
    radial_section: CollapsibleSection
    refresh_radials: Callable[[], None]
    radial_section, refresh_radials = _build_radial_menus_section(
        log_success, log_error, log_info, log_warn, show_restart_warning,
    )
    body.content_layout.addWidget(radial_section)

    # --- Menu Cleanup Section ---
    cleanup_section: CollapsibleSection = _build_menu_cleanup_section(
        log_success,
        log_error,
        log_info,
        log_warn,
        show_restart_warning,
        refresh_actions=refresh_actions,
        refresh_radials=refresh_radials,
    )
    body.content_layout.addWidget(cleanup_section)

    # Show restart banner once if disk and live already disagree
    _maybe_show_restart_on_mismatch(show_restart_warning)

    return body
