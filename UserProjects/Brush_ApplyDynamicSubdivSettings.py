"""
Apply Dynamic Subdiv Settings

Applies cached dynamic subdiv settings to all brush types.
Reads auto_subdivide, details_level, and remove_stretching from settings.

Room: Sculpt
Action: Apply dynamic subdiv settings to all brushes
"""
import coat
from _utils.brush_settings_utils import BrushSettingsUtils
from _utils.lks_settings import get_settings
import importlib
from _utils import lks_settings
from _utils import brush_settings_utils
importlib.reload(lks_settings)
importlib.reload(brush_settings_utils)


def apply_dynamic_subdiv_settings():
    """Apply cached dynamic subdiv settings to all brush types."""
    settings = get_settings()

    BrushSettingsUtils.apply_global_brush_settings(
        settings.auto_subdivide,
        settings.details_level,
        settings.remove_stretching
    )

    sub_status = "ON" if settings.auto_subdivide else "OFF"
    stretch_status = "ON" if settings.remove_stretching else "OFF"
    coat.ui.showInfoMessage(
        f"DynSubdiv: {sub_status}, Detail={settings.details_level}, Stretch={stretch_status}",
        3000
    )


# Execute
apply_dynamic_subdiv_settings()
