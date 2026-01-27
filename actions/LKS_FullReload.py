"""
Full reload of the LKS addon.

This unregisters the addon, reloads all modules, and re-registers.
Useful during development to pick up code changes.

Room: All
"""
from utils.registration_utils import full_reload
from utils.coat_ui_utils import show_message
import sys

# CRITICAL: Clear cached LKS modules BEFORE importing anything else
# This ensures we get fresh code from disk, not stale cached modules.
_to_clear = [name for name in list(sys.modules.keys())
             if name.startswith(("utils.", "ops.", "ui.", "cExtensions.LKS."))]
for _name in _to_clear:
    del sys.modules[_name]


def main() -> None:
    """Full reload LKS addon."""
    success: bool = full_reload()
    if success:
        show_message("LKS full reload complete", 2000)
    else:
        show_message("LKS full reload failed", 3000)


main()

# Queue this script for cache clearing (deferred to next frame)
if not hasattr(sys, '_lks_modules_to_clear'):
    sys._lks_modules_to_clear = set()
sys._lks_modules_to_clear.add(__name__)
