"""
LKS Register Main - Core registration entry point.

This script registers the LKS addon with 3DCoat:
1. Registers all action scripts to the Scripts menu (dynamic discovery)
2. Creates and registers the extension
3. Shows the panel

Can be called from:
- Actions menu: LKS_Register.py
- Panel buttons
- __onstartup.py (if auto-registration enabled)

Usage:
    from register_main import register
    register()  # Full registration with panel
"""
from __future__ import annotations

import coat


def register(show_panel: bool = True) -> bool:
    """
    Register the LKS addon with 3DCoat.

    Args:
        show_panel: Whether to show the panel after registration

    Returns:
        True if successful
    """
    try:
        # Import here to allow hot-reload
        from utils.registration_utils import register_actions
        from LKS import _ensure_extension

        # Register actions to menu (uses dynamic discovery now)
        action_count: int = register_actions()
        print(f"[LKS] Registered {action_count} actions to Scripts menu")

        # Create/get extension
        ext = _ensure_extension()
        print("[LKS] Extension registered")

        # Show panel if requested
        if show_panel and ext:
            ext.show_panel()
            print("[LKS] Panel shown")

        coat.ui.showInfoMessage("LKS: Registration complete", 2000)
        return True

    except Exception as e:
        print(f"[LKS] Registration failed: {e}")
        coat.ui.showInfoMessage(f"LKS: Registration failed - {e}", 3000)
        return False


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":
    register()
