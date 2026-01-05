"""
LKS addon registration utilities.

This module handles registering and unregistering the LKS addon with 3DCoat.
It provides:
- Menu action registration using dynamic discovery
- Extension lifecycle management
- Module reload utilities

Usage:
    from utils.registration_utils import register_addon, unregister_addon
    register_addon()    # Register all LKS actions and extension
    unregister_addon()  # Clean up and unregister
"""
from __future__ import annotations

import sys
import importlib
from pathlib import Path
from typing import Callable

import coat

# Import discovery system
from utils.action_discovery import discover_actions, ActionInfo
from utils.coat_menu_utils import get_lks_root, resolve_script_path

# Import hot reload utilities (cache clearing + dynamic discovery)
from utils.hot_reload import (
    discover_lks_modules,
    clear_pycache,
    invalidate_import_caches,
)

# =============================================================================
# CONSTANTS
# =============================================================================

# LKS module root
_LKS_ROOT: Path = get_lks_root()
_ACTIONS_DIR: Path = _LKS_ROOT / "actions"

# Menu name for LKS actions (uses Scripts menu - items prefixed with "LKS: " for grouping)
# Note: Custom top-level menus require cTemplates menu-making scripts.
# Using Scripts ensures actions appear under Scripts menu and in Hotkeys search.
# Valid menu names from menu_sections.txt: File, File.Import, File.Export, Edit, View,
# Windows.Popups, Windows.Sliders, Windows, Scripts, Help, Symmetry, Freeze, Voxels
LKS_MENU_NAME: str = "Scripts"

# Registered action IDs (for unregistration tracking)
_REGISTERED_ACTIONS: list[str] = []


# =============================================================================
# REGISTRATION FUNCTIONS (Using Dynamic Discovery)
# =============================================================================

def _register_action(action: ActionInfo) -> bool:
    """
    Register a single action script as a menu item in the Scripts menu.

    Args:
        action: ActionInfo from discovery system

    Returns:
        True if registered, False if already registered
    """
    script_path: str = resolve_script_path(action.path)

    # Add translation for localization (display name like "LKS: SculptObject_Decimate_Half_Selected.py")
    coat.ui.addTranslation(action.menu_id, action.display_name)

    # Only insert if not already in menu
    if not coat.ui.checkIfMenuItemInserted(action.menu_id):
        coat.ui.insertInMenu(LKS_MENU_NAME, action.menu_id, script_path)
        _REGISTERED_ACTIONS.append(action.menu_id)
        return True
    return False


def register_actions() -> int:
    """
    Register all LKS action scripts to the menu using dynamic discovery.

    Returns:
        Number of actions registered
    """
    actions: list[ActionInfo] = discover_actions(_ACTIONS_DIR)
    count: int = 0
    for action in actions:
        if _register_action(action):
            count += 1
    return count


def get_registered_actions() -> list[str]:
    """Get list of registered action IDs."""
    return list(_REGISTERED_ACTIONS)


# =============================================================================
# MODULE MANAGEMENT (uses dynamic discovery from hot_reload)
# =============================================================================

# Import dynamic discovery


def reload_modules(
    modules: list[str] | None = None,
    log_callback: Callable[[str], None] | None = None
) -> tuple[int, int]:
    """
    Reload LKS modules to pick up code changes.

    Uses dynamic discovery from hot_reload.discover_lks_modules().

    Args:
        modules: List of module names to reload (default: discovered LKS modules)
        log_callback: Optional callback for log messages

    Returns:
        Tuple of (reloaded_count, failed_count)
    """
    if modules is None:
        modules = discover_lks_modules()

    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    reloaded: int = 0
    failed: int = 0

    for module_name in modules:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                log(f"Reloaded: {module_name}")
                reloaded += 1
            except Exception as e:
                log(f"FAILED: {module_name} - {e}")
                failed += 1

    return reloaded, failed


def unload_modules(modules: list[str] | None = None) -> int:
    """
    Remove LKS modules from sys.modules.

    Uses dynamic discovery from hot_reload.discover_lks_modules().

    Args:
        modules: List of module names to unload (default: discovered LKS modules)

    Returns:
        Number of modules unloaded
    """
    if modules is None:
        modules = discover_lks_modules()

    count: int = 0
    for module_name in modules:
        if module_name in sys.modules:
            del sys.modules[module_name]
            count += 1

    return count


# =============================================================================
# ADDON LIFECYCLE
# =============================================================================

_extension_instance = None


def register_addon(
    show_panel: bool = True,
    log_callback: Callable[[str], None] | None = None
) -> bool:
    """
    Register the LKS addon with 3DCoat.

    This:
    1. Registers all action scripts to the menu
    2. Creates and registers the extension
    3. Optionally shows the panel

    Args:
        show_panel: Whether to show the panel after registration
        log_callback: Optional callback for log messages

    Returns:
        True if successful
    """
    global _extension_instance

    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    try:
        # Register actions
        action_count: int = register_actions()
        log(f"Registered {action_count} actions to SCRIPTS menu")

        # Register extension
        from LKS import LKSExtension, _ensure_extension
        _extension_instance = _ensure_extension()
        log("Extension registered")

        # Show panel if requested
        if show_panel and _extension_instance:
            _extension_instance.show_panel()
            log("Panel shown")

        log("Addon registration complete")
        return True

    except Exception as e:
        log(f"Registration failed: {e}")
        return False


def unregister_addon(
    log_callback: Callable[[str], None] | None = None
) -> bool:
    """
    Unregister the LKS addon from 3DCoat.

    This:
    1. Closes the panel if open
    2. Cleans up extension resources
    3. Optionally unloads modules

    Args:
        log_callback: Optional callback for log messages

    Returns:
        True if successful
    """
    global _extension_instance

    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    try:
        # Close panel and cleanup extension
        if _extension_instance:
            if hasattr(_extension_instance, '_panel') and _extension_instance._panel:
                _extension_instance._panel.close()
                log("Panel closed")
            _extension_instance = None
            log("Extension cleaned up")

        # Note: Cannot fully unregister menu items from 3DCoat
        # They will remain but become non-functional
        log("Addon unregistration complete")
        log("Note: Menu items remain until 3DCoat restart")
        return True

    except Exception as e:
        log(f"Unregistration failed: {e}")
        return False


def full_reload(
    log_callback: Callable[[str], None] | None = None,
    clear_cache: bool = True,
) -> bool:
    """
    Perform a full reload of the LKS addon.

    This:
    1. Clears __pycache__ and invalidates import caches (if clear_cache=True)
    2. Unregisters the addon
    3. Reloads all modules
    4. Re-registers the addon

    Args:
        log_callback: Optional callback for log messages
        clear_cache: If True (default), clear all caches before reload

    Returns:
        True if successful
    """
    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    log("Starting full reload...")

    # Clear caches first
    if clear_cache:
        pycache_count = clear_pycache(silent=True)
        invalidate_import_caches()
        log(f"Cleared {pycache_count} __pycache__ folders")

    # Unregister
    unregister_addon(log_callback)
    coat.io.step(2)

    # Reload modules
    reloaded, failed = reload_modules(log_callback=log_callback)
    log(f"Reloaded {reloaded} modules, {failed} failed")
    coat.io.step(2)

    # Re-register
    success: bool = register_addon(show_panel=True, log_callback=log_callback)
    log("Full reload complete" if success else "Full reload failed")

    return success
