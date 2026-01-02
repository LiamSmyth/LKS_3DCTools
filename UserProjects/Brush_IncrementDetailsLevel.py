"""
Increment Details Level

Increments the brush details level by 1 and ensures dynamic subdiv is enabled.
0 -> 1 -> 2 -> 3 -> 4 -> 5 ...

Room: Sculpt
Action: Increment details level, enable auto subdiv, apply to all brushes
"""
import coat
from _utils.brush_settings_utils import BrushSettingsUtils
from _utils.lks_settings import get_settings, save_settings
import importlib
from _utils import lks_settings
from _utils import brush_settings_utils
importlib.reload(lks_settings)
importlib.reload(brush_settings_utils)


def increment_details_level():
    """Increment the current details level by 1 and enable dynamic subdiv."""
    settings = get_settings()
    current = settings.details_level

    new_value = current + 1

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
increment_details_level()
