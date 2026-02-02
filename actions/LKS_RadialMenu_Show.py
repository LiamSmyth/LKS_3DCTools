"""
Show radial tree menu at cursor position.

Room: All
Action: Display radial menu with configured actions
"""
from utils.action_base import action


@action
def main() -> None:
    """Show radial menu with items from config file."""
    print("[LKS_RadialMenu_Show] Starting...")

    from utils.ui.widgets import get_manager
    from utils.radial_menu_config import get_default_menu_items

    print("[LKS_RadialMenu_Show] Loading menu items from config...")
    # Load menu items from config
    items = get_default_menu_items()

    if not items:
        print("[RadialMenu] No menu items configured")
        return

    print(f"[LKS_RadialMenu_Show] Loaded {len(items)} items")

    # Show menu at cursor position
    print("[LKS_RadialMenu_Show] Getting manager...")
    manager = get_manager()

    print("[LKS_RadialMenu_Show] Calling show_menu...")
    manager.show_menu(items)

    print("[LKS_RadialMenu_Show] Complete")


main()
