"""
Show radial tree menu at cursor position.

Room: All
Action: Display radial menu with configured actions

NOTE: Uses dev_mode setting to conditionally reload modules.
When dev_mode=False, skips reload_all() for instant radial menu response.
"""
import sys
import time as _time

_MODULE_BODY_START: float = _time.monotonic()


def main() -> None:
    """Show radial menu with items from config file."""
    _t0: float = _time.monotonic()
    _dispatch_ms: float = (_t0 - _MODULE_BODY_START) * 1000
    print(f"[RadialMenu] Module body→main: {_dispatch_ms:.0f}ms")

    # Check dev mode for conditional reload
    from utils.lks_settings import get_settings
    _dev_mode: bool = get_settings().dev_mode
    _t1: float = _time.monotonic()

    if _dev_mode:
        from utils.hot_reload import reload_all
        reload_all()
    _t2: float = _time.monotonic()

    from utils.ui.widgets import get_manager
    from utils.radial_menu_config import get_default_menu_items
    _t3: float = _time.monotonic()

    # Load menu items from config
    items = get_default_menu_items()
    _t4: float = _time.monotonic()

    if not items:
        print("[RadialMenu] No menu items configured")
        return

    # Show menu at cursor position
    manager = get_manager()
    manager.show_menu(items, action_id="LKS_RadialMenu_Show")
    _t5: float = _time.monotonic()

    print(f"[RadialMenu] Timing: settings={(_t1-_t0)*1000:.0f}ms, "
          f"reload={(_t2-_t1)*1000:.0f}ms, imports={(_t3-_t2)*1000:.0f}ms, "
          f"config={(_t4-_t3)*1000:.0f}ms, show={(_t5-_t4)*1000:.0f}ms, "
          f"total={(_t5-_t0)*1000:.0f}ms")

    # Queue this module for cache clearing (so next press re-executes)
    if not hasattr(sys, '_lks_modules_to_clear'):
        sys._lks_modules_to_clear = set()
    sys._lks_modules_to_clear.add(__name__)


main()
