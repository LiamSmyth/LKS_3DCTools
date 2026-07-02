"""
Radial Menu Manager - Singleton managing radial menu lifecycle.

Provides a high-level interface for showing radial menus at cursor position,
loading menu configuration, and handling menu events.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .radial_menu import RadialMenuItem

try:
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QCursor
    HAS_QT = True
except ImportError:
    HAS_QT = False


# =============================================================================
# MANAGER CLASS
# =============================================================================

class RadialMenuManager:
    """
    Singleton managing radial menu widget lifecycle.

    Responsibilities:
    - Create and own RadialMenuWidget instance
    - Show menu at cursor position with given items
    - Load menu configuration from settings/config
    - Handle menu close and action invocation

    Usage:
        manager = get_manager()
        manager.show_menu(items)  # Show at cursor position
    """
    _instance: RadialMenuManager | None = None

    def __init__(self):
        """Initialize manager (use get_manager() instead)."""
        if not HAS_QT:
            raise ImportError("PySide6 required for RadialMenuManager")

        # Import here to avoid circular dependency
        from .radial_menu import RadialMenuWidget

        self._widget: RadialMenuWidget = RadialMenuWidget()
        self._current_items: list[RadialMenuItem] = []
        self._trigger_keycode: int | None = None  # Qt keycode for the trigger key

    def show_menu(
        self,
        items: list[RadialMenuItem],
        pos: QPoint | None = None,
        action_id: str | None = None,
    ) -> None:
        """
        Show radial menu at specified position (or cursor if None).

        Args:
            items: List of menu items to display
            pos: Position to show menu at (None = cursor position)
            action_id: 3DCoat action/menu identifier that launched this menu
        """
        # CRITICAL: Close any existing menu first (singleton enforcement)
        if self._widget.isVisible():
            self._widget.releaseKeyboard()  # Release keyboard grab first
            self._widget.hide()
            # Force Qt to process the hide event
            QApplication.processEvents()

        if not items:
            return

        # Store current items
        self._current_items = items

        # Query hotkey for the trigger key
        self._trigger_keycode = self._query_trigger_key(action_id)

        # Load settings from lks_settings
        self._load_settings()

        # Set items on widget
        self._widget.set_items(items)

        # Pass trigger keycode to widget
        self._widget.set_trigger_keycode(self._trigger_keycode)

        # Show at cursor position if not specified
        if pos is None:
            pos = QCursor.pos()

        self._widget.show_at(pos)

    def hide_menu(self) -> None:
        """Hide the menu without invoking action."""
        self._widget.hide()

    def _query_trigger_key(self, action_id: str | None = None) -> int | None:
        """Query hotkeys file to find which key is mapped to this action."""
        try:
            from utils.hotkey_utils import HotkeyEntry, parse_hotkeys_file, get_default_hotkeys_path
            from utils.keycode_map import coat_to_qt_key
            from utils.win32_key_state import binding_is_active

            resolved_action_id: str = action_id or "LKS_RadialMenu_Show"

            # Get hotkeys path
            hotkeys_path = get_default_hotkeys_path()
            if not hotkeys_path or not hotkeys_path.exists():
                return None

            hotkeys_file = parse_hotkeys_file(hotkeys_path)

            candidates: list[tuple[HotkeyEntry, int]] = []
            action_variants: set[str] = {
                resolved_action_id,
                f"${resolved_action_id}",
            }

            if resolved_action_id.startswith("$"):
                action_variants.add(resolved_action_id[1:])

            for entry in hotkeys_file.entries:
                if entry.id not in action_variants or not entry.is_assigned:
                    continue

                qt_key = coat_to_qt_key(entry.code)
                if qt_key is not None:
                    candidates.append((entry, qt_key))

            if not candidates:
                return None

            active_candidates: list[int] = []
            for entry, qt_key in candidates:
                if binding_is_active(
                    qt_key,
                    ctrl=entry.ctrl,
                    alt=entry.alt,
                    shift=entry.shift,
                ):
                    active_candidates.append(qt_key)

            unique_active: list[int] = list(dict.fromkeys(active_candidates))
            if len(unique_active) == 1:
                return unique_active[0]
            if len(unique_active) > 1:
                print(
                    f"[RadialMenuManager] Ambiguous active bindings for {resolved_action_id}: "
                    f"{len(unique_active)} candidates"
                )
                return unique_active[0]

            unique_candidates: list[int] = list(
                dict.fromkeys(qt_key for _, qt_key in candidates))
            if len(unique_candidates) == 1:
                return unique_candidates[0]

            print(
                f"[RadialMenuManager] Ambiguous bindings for {resolved_action_id}: "
                f"{len(unique_candidates)} candidates and none currently held"
            )

            return None
        except Exception as e:
            print(f"[RadialMenuManager] Failed to query trigger key: {e}")
            return None

    def _load_settings(self) -> None:
        """Load radial menu settings from lks_settings."""
        try:
            from utils.lks_settings import get_settings
            settings = get_settings()

            # Update widget constants from settings
            from .radial_menu import (
                DEAD_ZONE_RADIUS, MENU_RADIUS,
                BRANCH_HOVER_RADIUS, BRANCH_DWELL_MS
            )

            # Read settings (with fallback to current constants)
            dead_zone = settings.get(
                "radial_menu_dead_zone_radius", DEAD_ZONE_RADIUS)
            menu_radius = settings.get("radial_menu_menu_radius", MENU_RADIUS)
            branch_hover = settings.get(
                "radial_menu_branch_hover_radius", BRANCH_HOVER_RADIUS)
            branch_dwell = settings.get(
                "radial_menu_branch_dwell_ms", BRANCH_DWELL_MS)

            # Apply to widget
            self._widget.set_geometry_params(
                dead_zone_radius=dead_zone,
                menu_radius=menu_radius,
                branch_hover_radius=branch_hover,
                branch_dwell_ms=branch_dwell,
            )
        except ImportError:
            # lks_settings not available (standalone mode)
            print("[RadialMenuManager] lks_settings not available, using defaults")
        except Exception as e:
            print(f"[RadialMenuManager] Failed to load settings: {e}")


# =============================================================================
# MODULE-LEVEL ACCESSOR
# =============================================================================

def get_manager() -> RadialMenuManager:
    """Get or create the singleton RadialMenuManager instance."""
    if RadialMenuManager._instance is None:
        RadialMenuManager._instance = RadialMenuManager()
    return RadialMenuManager._instance
