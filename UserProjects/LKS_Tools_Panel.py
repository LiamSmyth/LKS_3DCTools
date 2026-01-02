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
from _utils.coat_ui_utils import show_message


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
        self.auto_subdivide: bool = settings.auto_subdivide
        self.details_level: float = float(settings.details_level)
        self.remove_stretching: bool = settings.remove_stretching

        # ==================== AUTOPO ====================
        self.autopo_density: int = settings.autopo_density

        # ==================== DECIMATE ====================
        self.decimate_percent: int = 50  # Reduction percentage

        # Track previous brush for sticky settings
        self._prev_brush: str = ""

    def ui(self) -> list:
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
        items: list = []

        # ==================== DYNAMIC SUBDIV SECTION ====================
        items.append("#Dynamic Subdivision")
        items.append("auto_subdivide")
        items.append("details_level,[0,8]")
        items.append("remove_stretching")
        items.append("[1 1]")  # Two equal columns
        items.append("ApplyToBrushes")
        items.append("IncrementDetails")

        items.append("---")

        # ==================== OBJECT OPERATIONS SECTION ====================
        items.append("#Object Operations")
        items.append("[1 1]")
        items.append("ScaleDown100x")
        items.append("ScaleUp100x")
        items.append("[1 1]")
        items.append("ToSurfaceAll")
        items.append("ToVoxelAll")

        items.append("---")

        # ==================== GHOST/VISIBILITY SECTION ====================
        items.append("#Visibility")
        items.append("[1 1]")
        items.append("GhostToggleTree")
        items.append("UnghostAll")
        items.append("[1 1]")
        items.append("GhostIsolate")
        items.append("GhostInvert")

        items.append("---")

        # ==================== DECIMATE SECTION ====================
        items.append("#Decimate")
        items.append("decimate_percent,[10,90]")
        items.append("[1 1]")
        items.append("DecimateCurrent")
        items.append("DecimateTree")

        items.append("---")

        # ==================== AUTOPO SECTION ====================
        items.append("#Autopo")
        items.append("autopo_density")
        items.append("[1 1 1]")  # Three equal columns
        items.append("RunAutopo")
        items.append("AutopoToSculpt")
        items.append("AutopoToMultires")

        items.append("---")

        # ==================== SAVE/CLOSE ====================
        items.append("SaveSettings")

        return items

    def process(self) -> bool:
        """
        Called each frame while dialog is open.
        Used for polling/updating dynamic values.
        Returns False to keep dialog open.
        """
        return False

    # ==================== DYNAMIC SUBDIV HANDLERS ====================

    def ApplyToBrushes(self) -> None:
        """Apply current dynamic subdiv settings to all brushes."""
        from _utils.brush_settings_utils import BrushSettingsUtils
        BrushSettingsUtils.apply_global_brush_settings(
            self.auto_subdivide,
            self.details_level,
            self.remove_stretching
        )
        show_message("Applied to all brushes", 2000)

    def IncrementDetails(self) -> None:
        """Increment details level by 1."""
        self.details_level = min(8.0, self.details_level + 1.0)
        self.ApplyToBrushes()

    # ==================== OBJECT OPERATION HANDLERS ====================

    def ScaleDown100x(self) -> None:
        """Scale current object down by 100x."""
        from _utils.object_utils import ObjectUtils
        el: coat.SceneElement | None = coat.Scene.current()
        if not el:
            show_message("No object selected", 2000)
            return
        ObjectUtils.scale_selected_element(el, 0.01)
        show_message("Scaled down 100x", 2000)

    def ScaleUp100x(self) -> None:
        """Scale current object up by 100x."""
        from _utils.object_utils import ObjectUtils
        el: coat.SceneElement | None = coat.Scene.current()
        if not el:
            show_message("No object selected", 2000)
            return
        ObjectUtils.scale_selected_element(el, 100.0)
        show_message("Scaled up 100x", 2000)

    def ToSurfaceAll(self) -> None:
        """Convert all objects to surface mode."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import convert_to_surface

        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        count: int = 0
        for el in all_elements:
            if el.isSculptObject():
                vol: coat.Volume = el.Volume()
                if vol.isVoxelized():
                    convert_to_surface(vol)
                    count += 1
        show_message(f"Converted {count} to surface", 2000)

    def ToVoxelAll(self) -> None:
        """Convert all objects to voxel mode."""
        from _utils.scene_api import SceneAPI

        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        count: int = 0
        for el in all_elements:
            if el.isSculptObject():
                vol: coat.Volume = el.Volume()
                if vol.isSurface():
                    vol.toVoxels()
                    count += 1
        show_message(f"Converted {count} to voxels", 2000)

    # ==================== GHOST/VISIBILITY HANDLERS ====================

    def GhostToggleTree(self) -> None:
        """Toggle ghost on current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.visibility_utils import set_ghost

        current: coat.SceneElement | None = SceneAPI.get_current_element()
        if not current:
            show_message("No object selected", 2000)
            return

        new_ghost: bool = not current.ghost()
        elements: list[coat.SceneElement] = SceneAPI.collect_subtree(current)
        count: int = set_ghost(elements, new_ghost)
        current.selectOne()

        status: str = "ghosted" if new_ghost else "unghosted"
        show_message(f"{count} objects {status}", 2000)

    def UnghostAll(self) -> None:
        """Unghost all objects."""
        from _utils.scene_api import SceneAPI
        from _utils.visibility_utils import unghost_elements

        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        count: int = unghost_elements(all_elements)
        show_message(f"Unghosted {count} objects", 2000)

    def GhostIsolate(self) -> None:
        """Ghost all except current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.visibility_utils import ghost_except

        current: coat.SceneElement | None = SceneAPI.get_current_element()
        if not current:
            show_message("No object selected", 2000)
            return

        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        selected: list[coat.SceneElement] = SceneAPI.get_selected_elements()
        count: int = ghost_except(all_elements, selected)
        show_message(f"Isolated - ghosted {count}", 2000)

    def GhostInvert(self) -> None:
        """Invert ghost state on all objects."""
        from _utils.scene_api import SceneAPI
        from _utils.visibility_utils import invert_ghost_on_elements

        all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects(
        )
        count: int = invert_ghost_on_elements(all_elements)
        show_message(f"Inverted {count} objects", 2000)

    # ==================== DECIMATE HANDLERS ====================

    def DecimateCurrent(self) -> None:
        """Decimate current selection by percent."""
        from _utils.mesh_utils import DecimateParams, execute_decimate, cleanup_after_mesh_operation
        from _utils.object_utils import ObjectUtils

        result = ObjectUtils.get_current_sculpt_volume()
        if not result:
            return

        current_object, vol = result
        ObjectUtils.ensure_surface_mode(vol)

        execute_decimate(DecimateParams(
            reduction_percent=float(self.decimate_percent)))
        cleanup_after_mesh_operation()
        show_message(f"Decimated {self.decimate_percent}%", 2000)

    def DecimateTree(self) -> None:
        """Decimate subtree by percent."""
        from _utils.mesh_utils import DecimateParams, execute_decimate, cleanup_after_mesh_operation, ensure_surface_mode
        from _utils.scene_api import SceneAPI

        current: coat.SceneElement | None = SceneAPI.get_current_element()
        if not current:
            show_message("No object selected", 2000)
            return

        elements: list[coat.SceneElement] = SceneAPI.collect_subtree(current)
        count: int = 0

        for el in elements:
            if el.isSculptObject():
                vol: coat.Volume = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                execute_decimate(DecimateParams(
                    reduction_percent=float(self.decimate_percent)))
                count += 1

        current.selectOne()
        cleanup_after_mesh_operation()
        show_message(
            f"Decimated {count} objects by {self.decimate_percent}%", 2000)

    # ==================== AUTOPO HANDLERS ====================

    def RunAutopo(self) -> None:
        """Run autopo with current settings."""
        from _utils.autopo_utils import AutopoParams, execute_autopo
        self._save_autopo_settings()
        params = AutopoParams(target_polycount=self.autopo_density)
        execute_autopo(params)

    def AutopoToSculpt(self) -> None:
        """Run autopo and import result to sculpt."""
        from _utils.autopo_utils import autopo_to_sculpt, AutopoParams
        self._save_autopo_settings()
        params = AutopoParams(target_polycount=self.autopo_density)
        autopo_to_sculpt(params)

    def AutopoToMultires(self) -> None:
        """Run autopo and import as multiresolution."""
        from _utils.autopo_utils import autopo_to_multiresolution, AutopoParams
        self._save_autopo_settings()
        params = AutopoParams(target_polycount=self.autopo_density)
        autopo_to_multiresolution(params)

    def _save_autopo_settings(self) -> None:
        """Helper to save autopo settings."""
        settings = get_settings()
        settings.autopo_density = self.autopo_density
        save_settings()

    # ==================== SAVE HANDLER ====================

    def SaveSettings(self) -> None:
        """Save current settings to disk."""
        settings = get_settings()
        settings.auto_subdivide = self.auto_subdivide
        settings.details_level = int(self.details_level)
        settings.remove_stretching = self.remove_stretching
        settings.autopo_density = self.autopo_density
        save_settings()
        show_message("Settings saved", 2000)


def show_lks_tools_panel() -> None:
    """
    Show the LKS Tools configuration panel.

    Uses noModal() so execution continues, but note:
    dialogs still block viewport input until closed.
    """
    config = LKSToolsConfig()

    # Load any persisted settings
    settings_path: str = "UserPrefs/Addons/LKS/lks_panel_state.json"
    if coat.io.fileExists(settings_path):
        coat.io.fromJsonFile(config, settings_path)

    # Show non-modal dialog at top-right
    coat.dialog() \
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
