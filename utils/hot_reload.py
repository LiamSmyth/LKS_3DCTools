"""
Hot reload utilities for LKS cModule development.

Provides automatic module reloading for action scripts and panel development.
This ensures code changes are picked up without restarting 3DCoat.

Usage in action scripts:
    from utils.hot_reload import reload_all
    reload_all()  # Call at top of main() before any other imports

Usage for specific modules:
    from utils.hot_reload import reload_module
    reload_module("utils.scope_utils")

Note: cExtensions CANNOT be unregistered once created. Menu items persist
until 3DCoat restart. This module handles what CAN be reloaded.
"""
from __future__ import annotations

import sys
import importlib
import shutil
from pathlib import Path
from typing import Callable


# =============================================================================
# CACHE CLEARING
# =============================================================================

def get_lks_root() -> Path:
    """Get the LKS module root directory."""
    return Path(__file__).parent.parent


def clear_pycache(root: Path | None = None, silent: bool = True) -> int:
    """
    Recursively delete all __pycache__ folders under the LKS root.

    Args:
        root: Root directory (default: LKS module root)
        silent: If True, suppress console output

    Returns:
        Number of __pycache__ folders deleted
    """
    if root is None:
        root = get_lks_root()

    deleted: int = 0
    for pycache in root.rglob("__pycache__"):
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache)
                deleted += 1
            except Exception as e:
                if not silent:
                    print(f"[LKS] Failed to delete {pycache}: {e}")

    if not silent and deleted > 0:
        print(f"[LKS] Cleared {deleted} __pycache__ folders")

    return deleted


def invalidate_import_caches() -> None:
    """
    Invalidate Python's import caches.

    This tells Python to re-check the filesystem for module changes.
    Call before reload_modules() for maximum freshness.
    """
    importlib.invalidate_caches()


def clear_lks_from_sys_modules(preserve_hot_reload: bool = True) -> int:
    """
    Remove all LKS modules from sys.modules.

    This forces Python to re-import modules from disk on next import.
    More aggressive than reload - useful when module structure changed.

    Args:
        preserve_hot_reload: If True, keep utils.hot_reload loaded

    Returns:
        Number of modules removed
    """
    to_remove: list[str] = []

    for name in list(sys.modules.keys()):
        is_lks = any(name.startswith(prefix) for prefix in _PACKAGE_PRIORITY)
        if is_lks:
            if preserve_hot_reload and name == "utils.hot_reload":
                continue
            to_remove.append(name)

    for name in to_remove:
        del sys.modules[name]

    return len(to_remove)


# =============================================================================
# MODULE DISCOVERY (dynamic - no manual lists to maintain!)
# =============================================================================

# Package prefixes that belong to LKS (in reload order priority)
# Lower index = reload first (dependencies before dependents)
_PACKAGE_PRIORITY: dict[str, int] = {
    "utils.": 0,  # Utilities first (no LKS dependencies)
    "ops.": 1,    # Operators depend on utils
    "ui.": 2,     # UI depends on utils and ops
}

# Modules to skip during reload (would cause issues)
_SKIP_MODULES: set[str] = {
    "utils.hot_reload",  # Don't reload ourselves mid-reload!
}


def _get_module_priority(module_name: str) -> int:
    """Get reload priority for a module (lower = reload first)."""
    for prefix, priority in _PACKAGE_PRIORITY.items():
        if module_name.startswith(prefix):
            return priority
    return 99  # Unknown modules reload last


def discover_lks_modules() -> list[str]:
    """
    Discover all loaded LKS modules from sys.modules.

    Returns modules sorted in dependency order (utils → ops → ui).
    No manual list maintenance required!

    Returns:
        List of module names in reload order
    """
    lks_modules: list[str] = []

    for name in sys.modules:
        # Check if it's an LKS module
        is_lks = any(name.startswith(prefix) for prefix in _PACKAGE_PRIORITY)
        if is_lks and name not in _SKIP_MODULES:
            lks_modules.append(name)

    # Sort by priority (dependencies first), then alphabetically
    lks_modules.sort(key=lambda m: (_get_module_priority(m), m))

    return lks_modules


# =============================================================================
# RELOAD FUNCTIONS
# =============================================================================

def reload_module(module_name: str) -> bool:
    """
    Reload a single module if it's loaded.

    Args:
        module_name: Module name (e.g., "utils.scope_utils")

    Returns:
        True if reloaded, False if not loaded or failed
    """
    if module_name not in sys.modules:
        return False

    try:
        importlib.reload(sys.modules[module_name])
        return True
    except Exception as e:
        print(f"[LKS] Failed to reload {module_name}: {e}")
        return False


def reload_modules(
    modules: list[str] | None = None,
    log_callback: Callable[[str], None] | None = None,
    silent: bool = False,
) -> tuple[int, int]:
    """
    Reload multiple modules in order.

    Args:
        modules: List of module names (default: auto-discovered from sys.modules)
        log_callback: Optional callback for log messages
        silent: If True, suppress console output

    Returns:
        Tuple of (reloaded_count, failed_count)
    """
    if modules is None:
        modules = discover_lks_modules()

    def log(msg: str) -> None:
        if not silent:
            print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    reloaded: int = 0
    failed: int = 0

    for module_name in modules:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                reloaded += 1
            except Exception as e:
                log(f"FAILED: {module_name} - {e}")
                failed += 1

    if not silent and reloaded > 0:
        log(f"Reloaded {reloaded} modules" +
            (f" ({failed} failed)" if failed else ""))

    return reloaded, failed


def reload_all(
    silent: bool = True,
    clear_cache: bool = False,
) -> tuple[int, int]:
    """
    Reload all LKS modules. Call at start of action scripts.

    This is the main entry point for hot-reloading during development.
    Automatically discovers all loaded LKS modules from sys.modules
    and reloads them in dependency order (utils → ops → ui).

    Args:
        silent: If True (default), suppress console output
        clear_cache: If True, clear __pycache__ and invalidate import caches first

    Returns:
        Tuple of (reloaded_count, failed_count)

    Example:
        def main() -> None:
            from utils.hot_reload import reload_all
            reload_all()

            # Now import and use modules - they're fresh!
            from ops.SculptObject_Decimate import main as op_main
            op_main(...)
    """
    if clear_cache:
        clear_pycache(silent=silent)
        invalidate_import_caches()

    return reload_modules(silent=silent)


def reload_by_prefix(prefix: str, silent: bool = True) -> tuple[int, int]:
    """
    Reload modules matching a prefix (e.g., "utils.", "ops.").

    Args:
        prefix: Module prefix to match
        silent: If True, suppress console output

    Returns:
        Tuple of (reloaded_count, failed_count)
    """
    modules = [m for m in discover_lks_modules() if m.startswith(prefix)]
    return reload_modules(modules, silent=silent)


def fresh_reload(silent: bool = False) -> tuple[int, int]:
    """
    Perform a fresh reload by clearing all caches first.

    This is the most aggressive reload option:
    1. Clears all __pycache__ folders
    2. Invalidates Python import caches
    3. Removes all LKS modules from sys.modules
    4. Re-imports and returns count

    Use when module structure has changed (new files, moved files, etc.).

    Args:
        silent: If True, suppress console output

    Returns:
        Tuple of (modules_cleared, 0)  - always succeeds since we clear rather than reload
    """
    if not silent:
        print("[LKS] Fresh reload: clearing all caches...")

    # Step 1: Clear __pycache__
    pycache_count: int = clear_pycache(silent=silent)

    # Step 2: Invalidate import caches
    invalidate_import_caches()

    # Step 3: Remove LKS modules from sys.modules
    cleared: int = clear_lks_from_sys_modules(preserve_hot_reload=True)

    if not silent:
        print(f"[LKS] Fresh reload complete: cleared {cleared} modules, "
              f"{pycache_count} __pycache__ folders")

    return cleared, 0


# =============================================================================
# PANEL RELOAD (special handling to keep window alive)
# =============================================================================

def reload_for_panel(
    panel_instance,
    log_callback: Callable[[str], None] | None = None,
    clear_cache: bool = True,
) -> bool:
    """
    Reload all modules while keeping panel window alive.

    This reloads all LKS modules and refreshes the panel's UI
    without closing the window. The panel instance is preserved
    but its callbacks will use freshly reloaded code.

    Args:
        panel_instance: The LKSPanel instance to refresh
        log_callback: Optional callback for log messages
        clear_cache: If True (default), clear __pycache__ before reload

    Returns:
        True if reload succeeded
    """
    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    try:
        # Step 0: Clear caches for fresh import
        if clear_cache:
            pycache_count = clear_pycache(silent=True)
            invalidate_import_caches()
            if pycache_count > 0:
                log(f"Cleared {pycache_count} __pycache__ folders")

        # Step 1: Reload all modules
        reloaded, failed = reload_modules(
            log_callback=log_callback, silent=False)

        # Step 2: If panel has a rebuild method, call it
        if hasattr(panel_instance, "rebuild_ui"):
            log("Rebuilding panel UI...")
            panel_instance.rebuild_ui()
        elif hasattr(panel_instance, "refresh"):
            log("Refreshing panel...")
            panel_instance.refresh()

        log(f"Hot reload complete: {reloaded} modules reloaded")
        return failed == 0

    except Exception as e:
        log(f"Hot reload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# DIAGNOSTICS
# =============================================================================

def list_loaded_lks_modules() -> list[str]:
    """List all LKS modules currently in sys.modules (sorted by priority)."""
    return discover_lks_modules()


def print_module_status() -> None:
    """Print status of all loaded LKS modules."""
    modules = discover_lks_modules()
    print("[LKS] Loaded Modules:")
    print("-" * 50)
    for module in modules:
        print(f"  {module}")
    print("-" * 50)
    print(f"Total: {len(modules)} modules loaded")
