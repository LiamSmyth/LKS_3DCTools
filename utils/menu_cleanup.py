"""
Menu cleanup utilities for removing stale LKS menu entries.

3DCoat persists menu registrations as XML files in:
  Documents/3DCoat/UserPrefs/Scripts/ExtraMenuItems/LKS_*.xml

This module provides functions to remove these files, allowing
fresh re-registration on next startup.

IMPORTANT: 3DCoat should be RESTARTED after cleanup for changes to take effect.
"""
from __future__ import annotations

from pathlib import Path

# =============================================================================
# CONSTANTS
# =============================================================================

# Path to ExtraMenuItems folder (relative to 3DCoat documents)
EXTRA_MENU_ITEMS_REL: str = "UserPrefs/Scripts/ExtraMenuItems"
LKS_PREFIX: str = "LKS_"


# =============================================================================
# FUNCTIONS
# =============================================================================

def get_extra_menu_items_path() -> Path | None:
    """Get the ExtraMenuItems folder path.

    Returns None if coat module is not available or path doesn't exist.
    """
    try:
        import coat
        docs_path: str = coat.io.documents("")
        extra_menu_path: Path = Path(docs_path) / EXTRA_MENU_ITEMS_REL
        if extra_menu_path.exists():
            return extra_menu_path
        return None
    except ImportError:
        return None


def find_lks_menu_files(extra_menu_path: Path | None = None) -> list[Path]:
    """Find all LKS_*.xml files in ExtraMenuItems folder.

    Args:
        extra_menu_path: Path to ExtraMenuItems folder. If None, auto-detects.

    Returns:
        List of Path objects for LKS_*.xml files.
    """
    if extra_menu_path is None:
        extra_menu_path = get_extra_menu_items_path()

    if extra_menu_path is None or not extra_menu_path.exists():
        return []

    files: list[Path] = list(extra_menu_path.glob(f"{LKS_PREFIX}*.xml"))
    return sorted(files, key=lambda p: p.name)


def delete_lks_menu_files(extra_menu_path: Path | None = None) -> tuple[int, list[str]]:
    """Delete all LKS_*.xml files from ExtraMenuItems folder.

    Args:
        extra_menu_path: Path to ExtraMenuItems folder. If None, auto-detects.

    Returns:
        Tuple of (deleted_count, list of deleted filenames)
    """
    files: list[Path] = find_lks_menu_files(extra_menu_path)
    deleted: list[str] = []

    for file_path in files:
        try:
            file_path.unlink()
            deleted.append(file_path.name)
        except OSError as e:
            # Log but continue - file might be locked
            print(f"Warning: Could not delete {file_path.name}: {e}")

    return len(deleted), deleted


def cleanup_lks_menu() -> tuple[int, list[str]]:
    """Clean up all LKS menu entries from 3DCoat.

    Call this to remove all stale LKS menu entries. After cleanup,
    restart 3DCoat to re-register with fresh names from __onstartup.py.

    Returns:
        Tuple of (deleted_count, list of deleted filenames)
    """
    return delete_lks_menu_files()


def get_menu_cleanup_status() -> dict[str, int | list[str]]:
    """Get status of LKS menu files for reporting.

    Returns:
        Dict with 'count' and 'files' keys.
    """
    files: list[Path] = find_lks_menu_files()
    return {
        "count": len(files),
        "files": [f.name for f in files],
    }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> None:
    """CLI entry point for menu cleanup."""
    import sys

    # Get path from coat module
    extra_menu_path: Path | None = get_extra_menu_items_path()

    if extra_menu_path is None:
        print("Error: Cannot locate ExtraMenuItems folder.")
        print("This script must be run from within 3DCoat or with coat module available.")
        sys.exit(1)

    files: list[Path] = find_lks_menu_files(extra_menu_path)

    if not files:
        print("No LKS_*.xml files found.")
        return

    print(f"Found {len(files)} LKS_*.xml files:")
    for f in files:
        print(f"  - {f.name}")

    print()
    response: str = input(
        "Delete all LKS_*.xml files? [y/N]: ").strip().lower()

    if response == "y":
        deleted_count, deleted_names = delete_lks_menu_files(extra_menu_path)
        print(f"\nDeleted {deleted_count} files.")
        print("Restart 3DCoat to re-register menu items with fresh names.")
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()
