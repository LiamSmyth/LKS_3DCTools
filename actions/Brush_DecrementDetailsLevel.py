"""
Decrement Details Level

Decrements the brush details level by 1 and applies to current brush.
Use 'Apply to Brushes' in LKS panel to apply to all brush types.

Room: Sculpt
Action: Decrement details level, apply to current brush
"""
from utils.brush_settings_utils import apply_auto_subdivide_current, apply_details_level_current
from utils.lks_settings import get_brush_settings, save_brush_settings, reload_brush_settings
from utils.coat_ui_utils import show_message
from utils.object_utils import validate_and_ensure_surface_mode


def decrement_details_level():
    """Decrement the current details level by 1."""
    # Ensure we're in surface mode (required for dynamic subdiv to work)
    if not validate_and_ensure_surface_mode():
        show_message("Select a sculpt object in surface mode", 2000)
        return

    # Force reload from disk to get latest value (avoid stale singleton)
    reload_brush_settings()

    # Load current settings from cache
    settings = get_brush_settings()
    current: int = int(settings.details_level)

    # Floor at 0
    new_value: int = max(0, current - 1)

    # Update cache and save to disk
    settings.details_level = new_value
    settings.auto_subdivide = True
    save_brush_settings()

    # Apply to current brush only (fast - instant)
    apply_auto_subdivide_current(True)
    apply_details_level_current(float(new_value))

    show_message(f"Details Level: {new_value}", 1000)


decrement_details_level()
