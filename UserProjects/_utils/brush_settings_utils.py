"""
Brush Settings Utilities - Dynamic subdivision settings for all brush types.

Provides functions to apply auto_subdivide, details_level, and remove_stretching
settings across all 3DCoat brush types.
"""
import coat

# =============================================================================
# BRUSH TYPE LIST
# =============================================================================

BRUSH_TYPES = [
    "carve", "flatten", "clay", "build", "draw", "smooth",
    "pinch", "inflate", "layer", "shift", "scrape", "fill",
    "growclay", "claytubes", "dam", "crease", "cut", "cutoff",
    "voxhide", "pose", "snake", "muscules", "twist", "move",
    "rapid", "polish", "brush3d", "chisel", "planar", "hpolish",
    "sweep", "caps", "reconstruct", "measure"
]

# =============================================================================
# SETTING PATH TEMPLATES
# =============================================================================

# Per-brush-type settings use format: $BrushConstructor::SETTING[BRUSH_TYPE]
SETTING_AUTO_SUBDIVIDE = "$BrushConstructor::AutoSubdivide[{brush}]"
SETTING_DETAILS_LEVEL = "$BrushConstructor::DetailsLevel[{brush}]"
SETTING_REMOVE_STRETCHING = "$BrushConstructor::RemoveStretching[{brush}]"

# Global settings
SETTING_GLOBAL_REMOVE_STRETCHING = "$RemoveStretching"


# =============================================================================
# BRUSH SETTINGS CLASS
# =============================================================================

class BrushSettingsUtils:
    """Static utility functions for brush settings configuration."""

    @staticmethod
    def apply_global_brush_settings(
        auto_subdivide: bool,
        details_level: float,
        remove_stretching: bool
    ) -> None:
        """
        Apply dynamic subdiv settings to ALL brush types.

        Args:
            auto_subdivide: Enable auto subdivision
            details_level: Detail level (0 = neutral, 1-16+ = finer)
            remove_stretching: Enable remove stretching
        """
        BrushSettingsUtils.set_auto_subdivide_all(auto_subdivide)
        BrushSettingsUtils.set_details_level_all(details_level)
        BrushSettingsUtils.set_remove_stretching_all(remove_stretching)

    @staticmethod
    def set_auto_subdivide_all(enabled: bool) -> None:
        """
        Set auto subdivide on all brush types.

        Args:
            enabled: Whether to enable auto subdivide
        """
        for brush_type in BRUSH_TYPES:
            setting = SETTING_AUTO_SUBDIVIDE.format(brush=brush_type)
            coat.ui.setBoolValue(setting, enabled)

    @staticmethod
    def set_details_level_all(level: float) -> None:
        """
        Set details level on all brush types.

        Args:
            level: Detail level (0 = neutral, higher = finer)
        """
        for brush_type in BRUSH_TYPES:
            setting = SETTING_DETAILS_LEVEL.format(brush=brush_type)
            # Note: Use setSliderValue for slider controls, setEditBoxValue for edit boxes
            coat.ui.setSliderValue(setting, float(level))

    @staticmethod
    def set_remove_stretching_all(enabled: bool) -> None:
        """
        Set remove stretching globally and on all brush types.

        Note: The global $RemoveStretching must be enabled for
        per-brush-type settings to take effect.

        Args:
            enabled: Whether to enable remove stretching
        """
        # Set the global setting (required for it to work)
        coat.ui.setBoolValue(SETTING_GLOBAL_REMOVE_STRETCHING, enabled)

        # Also set per-brush-type
        for brush_type in BRUSH_TYPES:
            setting = SETTING_REMOVE_STRETCHING.format(brush=brush_type)
            coat.ui.setBoolValue(setting, enabled)

    @staticmethod
    def set_auto_subdivide(brush_type: str, enabled: bool) -> None:
        """Set auto subdivide for a specific brush type."""
        setting = SETTING_AUTO_SUBDIVIDE.format(brush=brush_type)
        coat.ui.setBoolValue(setting, enabled)

    @staticmethod
    def set_details_level(brush_type: str, level: float) -> None:
        """Set details level for a specific brush type."""
        setting = SETTING_DETAILS_LEVEL.format(brush=brush_type)
        coat.ui.setSliderValue(setting, float(level))

    @staticmethod
    def set_remove_stretching(brush_type: str, enabled: bool) -> None:
        """Set remove stretching for a specific brush type."""
        setting = SETTING_REMOVE_STRETCHING.format(brush=brush_type)
        coat.ui.setBoolValue(setting, enabled)
