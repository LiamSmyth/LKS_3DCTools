"""
Radial Menu Cleanup Utilities - Clean up stale menu registrations.

Provides utilities to clean up:
- Orphaned action scripts (no corresponding library file)
- Stale menu XML files (3DCoat persistence)
- Registry state mismatches

Usage:
    python -c "from utils.radial_menu_cleanup import cleanup_all; cleanup_all()"
"""
from __future__ import annotations

from pathlib import Path
import shutil


def get_lks_root() -> Path:
    """Get root of LKS cModule."""
    return Path(__file__).parent.parent.resolve()


def cleanup_orphaned_action_scripts() -> int:
    """
    Delete action scripts in actions/radial/ that aren't in registry.

    Returns:
        Number of scripts deleted
    """
    from utils.radial_menu_registry import cleanup_orphaned_scripts
    return cleanup_orphaned_scripts()


def cleanup_menu_xml_files() -> int:
    """
    Delete stale LKS_Radial_*.xml menu item files.

    These are persisted by 3DCoat and must be manually deleted.
    Location: Documents/3DCoat/UserPrefs/Scripts/ExtraMenuItems/

    Returns:
        Number of XML files deleted
    """
    try:
        import coat
        documents_path = coat.io.documents("")
        extra_menu_items_dir = Path(
            documents_path) / "UserPrefs" / "Scripts" / "ExtraMenuItems"

        if not extra_menu_items_dir.exists():
            print(
                f"[RadialCleanup] ExtraMenuItems directory not found: {extra_menu_items_dir}")
            return 0

        deleted_count = 0
        for xml_file in extra_menu_items_dir.glob("LKS_Radial_*.xml"):
            xml_file.unlink()
            print(f"[RadialCleanup] Deleted menu XML: {xml_file.name}")
            deleted_count += 1

        return deleted_count

    except Exception as e:
        print(f"[RadialCleanup] Failed to cleanup menu XMLs: {e}")
        return 0


def cleanup_all(verbose: bool = True) -> dict[str, int]:
    """
    Run all cleanup operations.

    Args:
        verbose: Print detailed output

    Returns:
        Dictionary with counts: {
            "orphaned_scripts": <count>,
            "menu_xmls": <count>,
        }
    """
    results = {}

    if verbose:
        print("[RadialCleanup] Starting cleanup...")

    # Cleanup orphaned action scripts
    scripts_deleted = cleanup_orphaned_action_scripts()
    results["orphaned_scripts"] = scripts_deleted
    if verbose:
        print(
            f"[RadialCleanup] Deleted {scripts_deleted} orphaned action script(s)")

    # Cleanup menu XML files
    xmls_deleted = cleanup_menu_xml_files()
    results["menu_xmls"] = xmls_deleted
    if verbose:
        print(f"[RadialCleanup] Deleted {xmls_deleted} menu XML file(s)")

    if verbose:
        print("[RadialCleanup] Cleanup complete")

    return results


def reset_all_menus(confirm: bool = False) -> dict[str, int]:
    """
    DESTRUCTIVE: Unregister all menus and delete all generated files.

    This will:
    - Delete all action scripts in actions/radial/
    - Clear registry state
    - Delete menu XML files

    Library menu configs are NOT deleted.

    Args:
        confirm: Must be True to execute (safety check)

    Returns:
        Dictionary with counts
    """
    if not confirm:
        print("[RadialCleanup] reset_all_menus() requires confirm=True")
        return {}

    from utils.radial_menu_registry import (
        RADIAL_ACTIONS_DIR, REGISTRY_STATE_FILE, save_registry_state
    )

    results = {}

    # Delete all action scripts
    if RADIAL_ACTIONS_DIR.exists():
        script_count = len(list(RADIAL_ACTIONS_DIR.glob("*.py")))
        shutil.rmtree(RADIAL_ACTIONS_DIR)
        RADIAL_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
        results["action_scripts"] = script_count
        print(f"[RadialCleanup] Deleted {script_count} action script(s)")
    else:
        results["action_scripts"] = 0

    # Clear registry state
    if REGISTRY_STATE_FILE.exists():
        REGISTRY_STATE_FILE.unlink()
        print("[RadialCleanup] Cleared registry state")
    save_registry_state({})

    # Cleanup menu XMLs
    xmls_deleted = cleanup_menu_xml_files()
    results["menu_xmls"] = xmls_deleted

    print("[RadialCleanup] Reset complete - restart 3DCoat to refresh menus")

    return results
