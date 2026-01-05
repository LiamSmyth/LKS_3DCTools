"""
LKS Unregister Main - Core unregistration entry point.

This script unregisters the LKS addon from 3DCoat:
1. Closes the panel if open
2. Cleans up extension resources
3. Optionally clears menu entries (requires restart)

Note: 3DCoat has no API to remove menu items. Use menu_cleanup.py
to delete the XML files, then restart 3DCoat.

Usage:
    from unregister_main import unregister
    unregister()  # Clean shutdown
"""
from __future__ import annotations

import coat


def unregister(clear_menu_files: bool = False) -> bool:
    """
    Unregister the LKS addon from 3DCoat.

    Args:
        clear_menu_files: Whether to delete menu XML files (requires restart)

    Returns:
        True if successful
    """
    try:
        # Close panel and cleanup extension
        from LKS import LKSExtension
        ext = LKSExtension.get_instance()

        if ext:
            if hasattr(ext, '_panel') and ext._panel:
                ext._panel.close()
                print("[LKS] Panel closed")
            print("[LKS] Extension cleaned up")

        # Optionally clear menu files
        if clear_menu_files:
            from utils.menu_cleanup import cleanup_lks_menu
            deleted, names = cleanup_lks_menu()
            if deleted > 0:
                print(f"[LKS] Deleted {deleted} menu files (restart required)")
                coat.ui.showInfoMessage(
                    f"LKS: Deleted {deleted} menu files. Restart 3DCoat to apply.", 3000)
            else:
                print("[LKS] No menu files to delete")

        print("[LKS] Unregistration complete")
        coat.ui.showInfoMessage("LKS: Unregistered", 2000)
        return True

    except Exception as e:
        print(f"[LKS] Unregistration failed: {e}")
        coat.ui.showInfoMessage(f"LKS: Unregistration failed - {e}", 3000)
        return False


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":
    unregister()
