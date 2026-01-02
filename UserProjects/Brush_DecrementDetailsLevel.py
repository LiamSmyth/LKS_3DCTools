"""
Decrement Details Level

Decrements the brush details level by 1 and ensures dynamic subdiv is enabled.
5 -> 4 -> 3 -> 2 -> 1 -> 0 (floor)

Room: Sculpt
Action: Decrement details level, enable auto subdiv, apply to all brushes
"""
import coat
from _utils.brush_settings_utils import BrushSettingsUtils
from _utils.lks_settings import get_settings, save_settings
import importlib
from _utils import lks_settings
from _utils import brush_settings_utils
importlib.reload(lks_settings)
importlib.reload(brush_settings_utils)


def decrement_details_level():
    """Decrement the current details level by 1 and enable dynamic subdiv."""
    settings = get_settings()
    current = settings.details_level

    # Floor at 0
    new_value = max(0, current - 1)

    # Update cache - enable auto_subdivide, use cached remove_stretching
    settings.details_level = new_value
    settings.auto_subdivide = True
    save_settings()

    # Apply all settings to all brushes
    BrushSettingsUtils.apply_global_brush_settings(
        settings.auto_subdivide,
        settings.details_level,
        settings.remove_stretching
    )
    coat.ui.showInfoMessage(f"Details Level: {new_value} (DynSubdiv ON)", 2000)


# Execute
decrement_details_level()
