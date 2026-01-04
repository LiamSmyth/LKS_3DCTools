"""
Full reload of the LKS addon.

This unregisters the addon, reloads all modules, and re-registers.
Useful during development to pick up code changes.

Room: All
"""
from utils.registration_utils import full_reload
from utils.coat_ui_utils import show_message


def main() -> None:
    """Full reload LKS addon."""
    success: bool = full_reload()
    if success:
        show_message("LKS full reload complete", 2000)
    else:
        show_message("LKS full reload failed", 3000)


main()
