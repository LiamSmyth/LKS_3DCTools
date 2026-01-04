"""
Unregister the LKS addon from 3DCoat.

This closes the LKS panel and cleans up extension resources.
Note: Menu items remain until 3DCoat restart.

Room: All
"""
from utils.registration_utils import unregister_addon
from utils.coat_ui_utils import show_message


def main() -> None:
    """Unregister LKS addon."""
    success: bool = unregister_addon()
    if success:
        show_message("LKS addon unregistered", 2000)
    else:
        show_message("LKS unregistration failed", 3000)


main()
