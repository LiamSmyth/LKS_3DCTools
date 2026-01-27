"""
Register the LKS addon with 3DCoat.

This registers all LKS action scripts to the SCRIPTS menu and creates
the extension for per-frame hooks.

Room: All
"""
from utils.registration_utils import register_addon
from utils.coat_ui_utils import show_message
import sys

# Clear cached utils/ops/ui modules to ensure fresh imports
_to_clear = [name for name in list(sys.modules.keys())
             if name.startswith(("utils.", "ops.", "ui."))]
for _name in _to_clear:
    del sys.modules[_name]


def main() -> None:
    """Register LKS addon."""
    success: bool = register_addon(show_panel=True)
    if success:
        show_message("LKS addon registered", 2000)
    else:
        show_message("LKS registration failed", 3000)


main()

# Queue this script for cache clearing (deferred to next frame)
if not hasattr(sys, '_lks_modules_to_clear'):
    sys._lks_modules_to_clear = set()
sys._lks_modules_to_clear.add(__name__)
