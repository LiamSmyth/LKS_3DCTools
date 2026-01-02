"""
LKS Tools Panel - Configuration Dashboard

Opens a non-modal dialog for configuring LKS tool settings.
Close the panel before sculpting (dialogs block viewport input).

Uses coat.dialog().params() pattern (verified in coat.pyi).
The ui() method returns layout items dynamically.

Room: All
"""
import coat
from _utils.lks_settings import get_settings, save_settings


class LKSToolsConfig:
    """
    Configuration object for LKS Tools Panel.

    Properties become UI controls via coat.dialog().params().
    The ui() method defines the layout.
    """

    def __init__(self):
        """Initialize with cached settings."""
        settings = get_settings()

        # ==================== DYNAMIC SUBDIV ====================
        self.auto_subdivide = settings.auto_subdivide
        self.details_level = float(settings.details_level)
        self.remove_stretching = settings.remove_stretching

        # ==================== AUTOPO ====================
        self.autopo_density = settings.autopo_density

        # ==================== DECIMATE ====================
        self.decimate_percent = 50  # Reduction percentage

        # Track previous brush for sticky settings
        self._prev_brush = ""

    def ui(self):
        """
        Define UI layout. Returns list of control definitions.

        Syntax (from Autoexport.py example):
        - "property_name" - auto control based on type
        - "property,[min,max]" - slider with range
        - "property,[#opt1|#opt2]" - dropdown
        - "#Header Text" - section header
        - "---" - separator
        - "MethodName" - button that calls self.MethodName()
        - "[2 1]" - column layout (proportions)
        """
        items = []

        # ==================== DYNAMIC SUBDIV SECTION ====================
        items.append("#Dynamic Subdivision")
        items.append("auto_subdivide")
        items.append("details_level,[0,8]")
        items.append("remove_stretching")
        items.append("[1 1]")  # Two equal columns
        items.append("ApplyToBrushes")
        items.append("IncrementDetails")

        items.append("---")

        # ==================== AUTOPO SECTION ====================
        items.append("#Autopo")
        items.append("autopo_density")
        items.append("[1 1 1]")  # Three equal columns
        items.append("RunAutopo")
        items.append("AutopoToSculpt")
        items.append("AutopoToMultires")

        items.append("---")

        # ==================== DECIMATE SECTION ====================
        items.append("#Decimate")
        items.append("decimate_percent,[10,90]")
        items.append("[1 1]")
        items.append("DecimateCurrent")
        items.append("DecimateTree")

        items.append("---")

        # ==================== SAVE/CLOSE ====================
        items.append("SaveSettings")

        return items

    def process(self):
        """
        Called each frame while dialog is open.
        Used for polling/updating dynamic values.
        Returns False to keep dialog open.
        """
        # Could implement sticky brush polling here
        return False

    # ==================== BUTTON HANDLERS ====================

    def ApplyToBrushes(self):
        """Apply current dynamic subdiv settings to all brushes."""
        from _utils.brush_settings_utils import BrushSettingsUtils
        BrushSettingsUtils.apply_global_brush_settings(
            self.auto_subdivide,
            self.details_level,
            self.remove_stretching
        )
        coat.ui.showInfoMessage("Applied to all brushes", 2000)

    def IncrementDetails(self):
        """Increment details level by 1."""
        self.details_level = min(8.0, self.details_level + 1.0)
        self.ApplyToBrushes()

    def RunAutopo(self):
        """Run autopo with current settings."""
        from _utils.autopo_utils import run_autopo_with_settings
        # Update settings before running
        settings = get_settings()
        settings.autopo_density = self.autopo_density
        save_settings()
        run_autopo_with_settings()

    def AutopoToSculpt(self):
        """Run autopo and import result to sculpt."""
        from _utils.autopo_utils import autopo_to_sculpt
        settings = get_settings()
        settings.autopo_density = self.autopo_density
        save_settings()
        autopo_to_sculpt()

    def AutopoToMultires(self):
        """Run autopo and import as multiresolution."""
        from _utils.autopo_utils import autopo_to_multiresolution
        settings = get_settings()
        settings.autopo_density = self.autopo_density
        save_settings()
        autopo_to_multiresolution()

    def DecimateCurrent(self):
        """Decimate current selection."""
        coat.ui.showInfoMessage(
            f"Decimate {self.decimate_percent}% - TODO", 2000)

    def DecimateTree(self):
        """Decimate selection subtree."""
        coat.ui.showInfoMessage(
            f"Decimate Tree {self.decimate_percent}% - TODO", 2000)

    def SaveSettings(self):
        """Save current settings to disk."""
        settings = get_settings()
        settings.auto_subdivide = self.auto_subdivide
        settings.details_level = int(self.details_level)
        settings.remove_stretching = self.remove_stretching
        settings.autopo_density = self.autopo_density
        save_settings()
        coat.ui.showInfoMessage("Settings saved", 2000)


def show_lks_tools_panel():
    """
    Show the LKS Tools configuration panel.

    Uses noModal() so execution continues, but note:
    dialogs still block viewport input until closed.
    """
    config = LKSToolsConfig()

    # Load any persisted settings
    settings_path = "UserPrefs/Addons/LKS/lks_panel_state.json"
    if coat.io.fileExists(settings_path):
        coat.io.fromJsonFile(config, settings_path)

    # Show non-modal dialog at top-right
    result = coat.dialog() \
        .caption("LKS Tools") \
        .noModal() \
        .topRight() \
        .width(300) \
        .buttons("Close") \
        .params(config) \
        .process(config.process) \
        .show()

    # Save state when closed
    coat.io.toJson(config, settings_path)


# Run when script is executed directly
show_lks_tools_panel()
