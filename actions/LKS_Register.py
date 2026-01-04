"""
Register the LKS addon with 3DCoat.

This registers all LKS action scripts to the SCRIPTS menu and creates
the extension for per-frame hooks.

Room: All
"""
from utils.registration_utils import register_addon
from utils.coat_ui_utils import show_message


def main() -> None:
    """Register LKS addon."""
    success: bool = register_addon(show_panel=True)
    if success:
        show_message("LKS addon registered", 2000)
    else:
        show_message("LKS registration failed", 3000)


main()
