"""
Apply Dynamic Subdiv Settings

Applies cached dynamic subdiv settings to all brush types.
Reads auto_subdivide, details_level, and remove_stretching from brush settings.

Room: Sculpt
Action: Apply dynamic subdiv settings to all brushes
"""
import coat
from utils.brush_settings_utils import BrushSettingsUtils
from utils.lks_settings import get_brush_settings


def apply_dynamic_subdiv_settings():
    """Apply cached dynamic subdiv settings to all brush types."""
    settings = get_brush_settings()

    BrushSettingsUtils.apply_global_brush_settings(
        settings.auto_subdivide,
        settings.details_level,
        settings.remove_stretching
    )

    sub_status: str = "ON" if settings.auto_subdivide else "OFF"
    stretch_status: str = "ON" if settings.remove_stretching else "OFF"
    coat.ui.showInfoMessage(
        f"DynSubdiv: {sub_status}, Detail={settings.details_level}, Stretch={stretch_status}",
        3000
    )


# Execute
apply_dynamic_subdiv_settings()
