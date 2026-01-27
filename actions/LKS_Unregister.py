"""
Unregister the LKS addon from 3DCoat.

This closes the LKS panel and cleans up extension resources.
Note: Menu items remain until 3DCoat restart.

Room: All
"""
from utils.registration_utils import unregister_addon
from utils.coat_ui_utils import show_message
import sys

# Clear cached utils/ops/ui modules to ensure fresh imports
_to_clear = [name for name in list(sys.modules.keys())
             if name.startswith(("utils.", "ops.", "ui."))]
for _name in _to_clear:
    del sys.modules[_name]


def main() -> None:
    """Unregister LKS addon."""
    success: bool = unregister_addon()
    if success:
        show_message("LKS addon unregistered", 2000)
    else:
        show_message("LKS unregistration failed", 3000)


main()

# Queue this script for cache clearing (deferred to next frame)
if not hasattr(sys, '_lks_modules_to_clear'):
    sys._lks_modules_to_clear = set()
sys._lks_modules_to_clear.add(__name__)
