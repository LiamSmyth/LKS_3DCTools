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


def clear_lks_from_sys_modules(
    preserve_hot_reload: bool = True,
    preserve_extension: bool = True,
) -> tuple[int, list[str]]:
    """
    Remove all LKS modules from sys.modules using filesystem-based discovery.

    This forces Python to re-import modules from disk on next import.
    More aggressive than reload — useful when module structure changed.
    Uses filesystem scanning so newly-added .py files are also cleared.

    Args:
        preserve_hot_reload: If True, keep utils.hot_reload loaded
        preserve_extension: If True, keep the LKS extension module (LKS.py)
            loaded so the cExtension C++ registration is not duplicated

    Returns:
        Tuple of (number_of_modules_removed, list_of_removed_names)
    """
    # Modules that must be preserved to avoid breaking the runtime
    _preserve: set[str] = set()
    if preserve_hot_reload:
        _preserve.add("utils.hot_reload")
    if preserve_extension:
        from utils.extension_identity import get_extension_folder_name

        folder: str = get_extension_folder_name()
        _preserve.add(folder)
        _preserve.add("LKS")  # source-tree / classic entry module name
        # Also preserve anything the extension module directly depends on
        # at module level (coat, cPy) — these are 3DCoat builtins, safe to skip

    # Discover ALL modules from filesystem (not just sys.modules)
    all_lks_modules: list[str] = discover_all_modules_from_filesystem()

    removed: list[str] = []
    for name in all_lks_modules:
        if name in sys.modules and name not in _preserve:
            del sys.modules[name]
            removed.append(name)

    # Also clear any modules that matched install prefixes but weren't
    # caught by filesystem scan (e.g., modules imported from outside root)
    from utils.extension_identity import cextension_module_prefixes

    extra_prefixes: tuple[str, ...] = cextension_module_prefixes()
    for name in list(sys.modules.keys()):
        if any(name.startswith(p) for p in extra_prefixes):
            if name not in _preserve:
                del sys.modules[name]
                removed.append(name)

    return len(removed), removed


# =============================================================================
# MODULE DISCOVERY (dynamic - no manual lists to maintain!)
# =============================================================================

# Package prefixes that belong to LKS (in reload order priority)
# Lower index = reload first (dependencies before dependents)
_PACKAGE_PRIORITY: dict[str, int] = {
    "lks_utils.": 0,   # Vendor lib — zero LKS dependencies
    "utils.": 1,        # Core utilities (may depend on lks_utils)
    "generators.": 2,   # Code generators depend on utils
    "ops.": 3,          # Operators depend on utils
    "ui.": 4,           # UI depends on utils and ops
    "actions.": 5,      # Action scripts depend on everything above
}

# Root-level modules (no dot prefix) that belong to this cExtension.
# Folder-named entry (e.g. LKS_Side.py) is included dynamically at reload time.
_ROOT_MODULES: set[str] = {
    "LKS", "__init__", "__onstartup",
}

# Modules to skip during reload (would cause issues)
_SKIP_MODULES: set[str] = {
    "utils.hot_reload",  # Don't reload ourselves mid-reload!
}

# Directories to exclude from filesystem scanning
_SKIP_DIRS: set[str] = {
    "__pycache__", ".git", ".cursor", ".github",
    "_docs", ".example_code", "agent-transcripts",
    "mcps", "terminals", "data",  # data/ is JSON, not Python
}

# File patterns to exclude
_SKIP_FILE_PREFIXES: tuple[str, ...] = ("test_", "_test_")
_SKIP_FILE_SUFFIXES: tuple[str, ...] = ()


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
        is_lks = any(name.startswith(prefix) for prefix in _PACKAGE_PRIORITY)
        if is_lks and name not in _SKIP_MODULES:
            lks_modules.append(name)

    # Sort by priority (dependencies first), then alphabetically
    lks_modules.sort(key=lambda m: (_get_module_priority(m), m))

    return lks_modules


def discover_all_modules_from_filesystem(
    root: Path | None = None,
) -> list[str]:
    """
    Discover ALL LKS Python modules by scanning the filesystem.

    Unlike discover_lks_modules() which only finds what's already in
    sys.modules, this scans every .py file under the LKS root directory.
    This catches newly-added files that haven't been imported yet.

    Args:
        root: LKS root directory (default: auto-detect)

    Returns:
        List of module names sorted in dependency order
    """
    if root is None:
        root = get_lks_root()

    modules: list[str] = []

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        parts: tuple[str, ...] = py_file.relative_to(root).parts
        if any(part in _SKIP_DIRS for part in parts):
            continue

        # Skip excluded file patterns
        filename: str = py_file.stem
        if filename.startswith(_SKIP_FILE_PREFIXES):
            continue
        if filename.endswith(_SKIP_FILE_SUFFIXES):
            continue

        # Convert filesystem path to module name
        module_name: str = _path_to_module_name(parts)

        # Skip internal Python artifacts
        if module_name in _SKIP_MODULES:
            continue

        # Skip root modules that aren't in the known set
        if "." not in module_name and module_name not in _ROOT_MODULES:
            # Only include root .py files that are part of the package
            if module_name in ("coat",):  # coat.pyi is type stubs, skip
                continue

        modules.append(module_name)

    # Remove duplicates and sort
    modules = sorted(set(modules), key=lambda m: (_get_module_priority(m), m))
    return modules


def _path_to_module_name(parts: tuple[str, ...]) -> str:
    """Convert filesystem path parts to a Python module name.

    Example:
        ('utils', 'ui', 'widgets', 'markdown_display.py') → 'utils.ui.widgets.markdown_display'
        ('LKS.py',) → 'LKS'
    """
    # Strip .py extension from last part
    cleaned: list[str] = []
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            # Last part — strip .py
            if part.endswith(".py"):
                part = part[:-3]
        cleaned.append(part)
    return ".".join(cleaned)


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

    # DEBUG: Always print entry/exit to trace hangs
    print("[LKS-DEBUG] reload_all() entering, discovering modules...", flush=True)
    modules: list[str] = discover_lks_modules()
    print(f"[LKS-DEBUG] reload_all() found {len(modules)} modules to reload", flush=True)
    result = reload_modules(modules=modules, silent=silent)
    print(f"[LKS-DEBUG] reload_all() complete: {result}", flush=True)
    return result


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

    # Step 3: Remove LKS modules from sys.modules (filesystem-based)
    cleared, _ = clear_lks_from_sys_modules(
        preserve_hot_reload=True, preserve_extension=True)

    # Step 4: Clear FastReimport cache
    try:
        from utils.fast_reimport import FastReimportFinder
        finder = FastReimportFinder.get_instance()
        finder.clear_all()
    except Exception:
        pass

    if not silent:
        print(f"[LKS] Fresh reload complete: cleared {cleared} modules, "
              f"{pycache_count} __pycache__ folders")

    return cleared, 0


# =============================================================================
# FULL HOT-RESTART (close old panel, clear everything, re-register, open fresh)
# =============================================================================

def full_restart_panel(
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """
    Perform a full hot-reload of the LKS addon from the panel button.

    This is the most complete reload possible without restarting 3DCoat:
    1. Clears all __pycache__ and invalidates import caches
    2. Reinitializes the extension (closes the old panel)
    3. Deletes ALL LKS modules from sys.modules (filesystem-based discovery,
       so newly-added .py files are also caught)
    4. Re-registers action scripts to the 3DCoat menu
    5. Opens a fresh panel from the newly-reimported code

    The cExtension C++ registration is permanent, but its Python state
    is fully reset. Menu XML entries persist until 3DCoat restart but
    become functional again after re-registration.

    Args:
        log_callback: Optional callback for log messages

    Returns:
        True if the full restart succeeded
    """
    import gc

    def log(msg: str) -> None:
        print(f"[LKS] {msg}")
        if log_callback:
            log_callback(msg)

    try:
        # ── Step 1: Clear all caches ──
        log("Clearing caches...")
        pycache_count: int = clear_pycache(silent=True)
        invalidate_import_caches()
        if pycache_count > 0:
            log(f"  Cleared {pycache_count} __pycache__ folders")

        # ── Step 2: Reinitialize extension (closes old panel) ──
        log("Closing old panel...")
        try:
            from LKS import LKSExtension
            ext = LKSExtension.get_instance()
            if ext:
                ext.reinitialize()
                log("  Extension reinitialized")
            else:
                log("  No extension instance found")
        except Exception as e:
            log(f"  Extension reinit warning: {e}")

        # ── Step 3: Clear ALL LKS modules from sys.modules ──
        log("Clearing all LKS modules from sys.modules...")
        cleared_count, _ = clear_lks_from_sys_modules(
            preserve_hot_reload=True,
            preserve_extension=True,
        )
        log(f"  Cleared {cleared_count} modules")

        # Clear FastReimport cache
        try:
            from utils.fast_reimport import FastReimportFinder
            finder = FastReimportFinder.get_instance()
            finder.clear_all()
        except Exception:
            pass

        # Force garbage collection to clean up any dangling references
        gc.collect()

        # ── Step 4: Re-register action scripts ──
        log("Registering actions...")
        try:
            from utils.registration_utils import register_actions
            action_count: int = register_actions()
            log(f"  Registered {action_count} action scripts")
        except Exception as e:
            log(f"  Action registration warning: {e}")

        # ── Step 5: Open fresh panel ──
        log("Opening fresh panel...")
        try:
            from LKS import LKSExtension, _ensure_extension
            ext = _ensure_extension()
            ext.show_panel()
            log("  Panel opened with fresh code")
        except Exception as e:
            import traceback
            log(f"  Panel creation failed: {e}")
            traceback.print_exc()
            return False

        log(f"Full hot-restart complete ({cleared_count} modules cleared)")
        return True

    except Exception as e:
        log(f"Full hot-restart failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Backward compatibility — delegates to the new full_restart_panel
def reload_for_panel(
    panel_instance,
    log_callback: Callable[[str], None] | None = None,
    clear_cache: bool = True,
) -> bool:
    """
    Reload all modules while keeping panel window alive.

    DEPRECATED: This now delegates to full_restart_panel() which performs
    a complete unregister/reregister cycle. The panel_instance argument
    is ignored — the extension singleton is used instead.

    Args:
        panel_instance: (ignored, kept for backward compatibility)
        log_callback: Optional callback for log messages
        clear_cache: (ignored — always True)

    Returns:
        True if reload succeeded
    """
    return full_restart_panel(log_callback=log_callback)


# =============================================================================
# DEV-MODE CONDITIONAL RELOAD (for panel button callbacks)
# =============================================================================

def reload_if_dev() -> None:
    """
    Call reload_all() if dev_mode is enabled. No-op otherwise.

    Use at the top of panel button callbacks so they pick up code changes
    during development, matching the behavior of @action-decorated menu items.

    This is safe to call unconditionally — it checks dev_mode internally
    and is wrapped in try/except so a settings read failure won't block
    the operation.
    """
    try:
        from utils.lks_settings import get_settings
        if get_settings().dev_mode:
            from utils.hot_reload import reload_all
            reload_all()
    except Exception:
        pass  # Settings unavailable (not in 3DCoat) — no-op


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
