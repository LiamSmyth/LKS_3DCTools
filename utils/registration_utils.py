"""
LKS addon registration utilities.

This module handles registering and unregistering the LKS addon with 3DCoat.
It provides:
- Menu action registration for hotkey assignment
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

# =============================================================================
# CONSTANTS
# =============================================================================

# LKS module root
_LKS_ROOT: Path = Path(__file__).parent.parent.resolve()
_ACTIONS_PATH: str = str(_LKS_ROOT / "actions").replace("\\", "/")

# Registered action IDs (for unregistration tracking)
_REGISTERED_ACTIONS: list[str] = []


# =============================================================================
# ACTION DEFINITIONS
# =============================================================================

# Format: (action_id, script_name, translation)
ACTION_DEFINITIONS: list[tuple[str, str, str]] = [
    # Decimate
    ("LKS_Decimate_Half_Selected", "SculptObject_Decimate_Half_Selected.py",
     "LKS: Decimate Selected 50%"),
    ("LKS_Decimate_Half_Subtree", "SculptObject_Decimate_Half_Subtree.py",
     "LKS: Decimate Subtree 50%"),
    ("LKS_ProxyToggle_Decimate16X", "SculptObject_ProxyToggle_Decimate16X_Selected.py",
     "LKS: Proxy Toggle Decimate 16X"),

    # Ghost/Visibility
    ("LKS_Ghost_Toggle_Subtree", "SculptObject_Ghost_Toggle_Subtree.py",
     "LKS: Ghost Toggle Subtree"),
    ("LKS_Ghost_Invert_All", "SculptObject_Ghost_Invert_All.py",
     "LKS: Ghost Invert All"),
    ("LKS_Ghost_Isolate_Selected", "SculptObject_Ghost_Isolate_Selected.py",
     "LKS: Ghost Isolate Selected"),
    ("LKS_Unghost_All", "SculptObject_Unghost_All.py",
     "LKS: Unghost All"),
    ("LKS_Visibility_Toggle_Subtree", "SculptObject_Visibility_Toggle_Subtree.py",
     "LKS: Visibility Toggle Subtree"),

    # Scale
    ("LKS_Scale_Down100x", "SculptObject_Scale_Down100x_Selected.py",
     "LKS: Scale Down 100x"),
    ("LKS_Scale_Up100x", "SculptObject_Scale_Up100x_Selected.py",
     "LKS: Scale Up 100x"),

    # Mode
    ("LKS_ToSurface_All", "SculptObject_ToSurface_All.py",
     "LKS: Convert All to Surface"),
    ("LKS_ToVoxel_All", "SculptObject_ToVoxel_All.py",
     "LKS: Convert All to Voxel"),

    # Mesh Operations
    ("LKS_Subdivide_Double_Subtree", "SculptObject_Subdivide_Double_Subtree.py",
     "LKS: Subdivide Double Subtree"),
    ("LKS_Resample_Half_Subtree", "SculptObject_Resample_Half_Subtree.py",
     "LKS: Resample Half Subtree"),
    ("LKS_RemeshResymm_Selected", "SculptObject_RemeshResymm_Safe_Selected.py",
     "LKS: Remesh+Resymm Selected"),
    ("LKS_IdColors_FromParts", "SculptObject_IdColors_FromParts.py",
     "LKS: ID Colors from Parts"),

    # Autopo
    ("LKS_Autopo_Run", "Autopo_Run.py",
     "LKS: Autopo Run"),
    ("LKS_Autopo_ToSculpt", "Autopo_ToSculpt.py",
     "LKS: Autopo to Sculpt"),

    # Brush
    ("LKS_Brush_IncrementDetails", "Brush_IncrementDetailsLevel.py",
     "LKS: Brush Increment Details"),
    ("LKS_Brush_DecrementDetails", "Brush_DecrementDetailsLevel.py",
     "LKS: Brush Decrement Details"),
]


# =============================================================================
# REGISTRATION FUNCTIONS
# =============================================================================

def _register_action(action_id: str, script_name: str, translation: str) -> bool:
    """
    Register a single action script as a menu item.

    Args:
        action_id: Unique identifier for the action
        script_name: Filename of the action script
        translation: User-facing name for hotkey assignment

    Returns:
        True if registered, False if already registered
    """
    script_path: str = f"{_ACTIONS_PATH}/{script_name}"

    # Add translation for localization
    coat.ui.addTranslation(action_id, translation)

    # Only insert if not already in menu
    if not coat.ui.checkIfMenuItemInserted(action_id):
        coat.ui.insertInMenu("SCRIPTS", action_id, script_path)
        _REGISTERED_ACTIONS.append(action_id)
        return True
    return False


def register_actions() -> int:
    """
    Register all LKS action scripts to the menu.

    Returns:
        Number of actions registered
    """
    count: int = 0
    for action_id, script_name, translation in ACTION_DEFINITIONS:
        if _register_action(action_id, script_name, translation):
            count += 1
    return count


def get_registered_actions() -> list[str]:
    """Get list of registered action IDs."""
    return list(_REGISTERED_ACTIONS)


# =============================================================================
# MODULE MANAGEMENT
# =============================================================================

# Modules to reload (in dependency order)
LKS_MODULES: list[str] = [
    # Core utilities
    'utils.lks_settings',
    'utils.coat_ui_utils',
    'utils.scene_api',
    'utils.scope_utils',
    'utils.object_utils',
    # Volume utilities
    'utils.Volume_decimate_utils',
    'utils.Volume_resample_utils',
    'utils.Volume_subdivide_utils',
    'utils.Volume_mode_utils',
    'utils.Volume_density_utils',
    'utils.Volume_proxy_utils',
    # Scene utilities
    'utils.Scene_cleanup_utils',
    'utils.Scene_layer_utils',
    'utils.Scene_tiling_utils',
    'utils.SceneElement_visibility_utils',
    'utils.SceneElement_boolean_utils',
    # Feature utilities
    'utils.brush_settings_utils',
    'utils.autopo_utils',
    'utils.scene_iteration_utils',
    'utils.registration_utils',
    # Operators
    'ops.SculptObject_Decimate',
    'ops.SculptObject_SetGhost',
    'ops.SculptObject_Scale',
    'ops.SculptObject_ModeConvert',
    'ops.SculptObject_Resample',
    'ops.SculptObject_IdColors',
    'ops.SculptObject_Proxy',
    # UI
    'ui.styles',
    'ui.widgets',
    'ui.activity_log',
]


def reload_modules(
    modules: list[str] | None = None,
    log_callback: Callable[[str], None] | None = None
) -> tuple[int, int]:
    """
    Reload LKS modules to pick up code changes.

    Args:
        modules: List of module names to reload (default: all LKS modules)
        log_callback: Optional callback for log messages

    Returns:
        Tuple of (reloaded_count, failed_count)
    """
    if modules is None:
        modules = LKS_MODULES

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

    Args:
        modules: List of module names to unload (default: all LKS modules)

    Returns:
        Number of modules unloaded
    """
    if modules is None:
        modules = LKS_MODULES

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
    log_callback: Callable[[str], None] | None = None
) -> bool:
    """
    Perform a full reload of the LKS addon.

    This:
    1. Unregisters the addon
    2. Reloads all modules
    3. Re-registers the addon

    Args:
        log_callback: Optional callback for log messages

    Returns:
        True if successful
    """
    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    log("Starting full reload...")

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
