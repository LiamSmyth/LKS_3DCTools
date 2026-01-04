"""
LKS Tools Panel - Comprehensive Configuration Dashboard

Opens a non-modal dialog for configuring LKS tool settings.
Close the panel before sculpting (dialogs block viewport input).

Uses coat.dialog().params() pattern (verified in coat.pyi).
The ui() method returns layout items dynamically.

Room: All
"""
import coat
from utils.lks_settings import (
    get_settings, save_settings,
    get_brush_settings, save_brush_settings,
    get_autopo_settings, save_autopo_settings,
)
from utils.coat_ui_utils import show_message


class LKSToolsConfig:
    """
    Configuration object for LKS Tools Panel.

    Properties become UI controls via coat.dialog().params().
    The ui() method defines the layout.
    """

    def __init__(self):
        """Initialize with cached settings."""
        settings = get_settings()
        brush_settings = get_brush_settings()
        autopo_settings = get_autopo_settings()

        # ==================== DYNAMIC SUBDIV (from brush settings) ====================
        self.auto_subdivide: bool = brush_settings.auto_subdivide
        self.details_level: float = float(brush_settings.details_level)
        self.remove_stretching: bool = brush_settings.remove_stretching

        # ==================== AUTOPO (from autopo settings) ====================
        self.autopo_polycount: int = autopo_settings.autopo_polycount
        self.autopo_capture_details: float = autopo_settings.autopo_capture_details
        self.autopo_auto_density: float = autopo_settings.autopo_auto_density
        self.autopo_hardsurface: bool = autopo_settings.autopo_hardsurface
        self.autopo_voxelize: bool = autopo_settings.autopo_voxelize
        self.autopo_voxelize_polycount: int = autopo_settings.autopo_voxelize_polycount
        self.autopo_decimate_if_above: bool = autopo_settings.autopo_decimate_if_above
        self.autopo_decimation_limit: int = autopo_settings.autopo_decimation_limit
        self.autopo_tangent_smooth: bool = autopo_settings.autopo_tangent_smooth
        self.autopo_bypass_modal: bool = autopo_settings.autopo_bypass_density_modal

        # ==================== DECIMATE (from general settings) ====================
        self.decimate_percent: int = settings.decimate_reduction

        # ==================== PREVIOUS STATE (for change detection) ====================
        self._prev_brush: dict = brush_settings.to_dict()
        self._prev_autopo: dict = autopo_settings.to_dict()
        self._prev_general: dict = {
            "decimate_reduction": self.decimate_percent}

    def ui(self) -> list:
        """Define UI layout."""
        items: list = []

        # ==================== DYNAMIC SUBDIV SECTION ====================
        items.append("#Dynamic Subdivision")
        items.append("auto_subdivide")
        items.append("details_level,[0,8]")
        items.append("remove_stretching")
        items.append("[1 1 1]")
        items.append("ApplyToBrushes")
        items.append("IncrementLevel")
        items.append("DecrementLevel")

        items.append("---")

        # ==================== MESH OPERATIONS SECTION ====================
        items.append("#Mesh Operations")

        # --- Decimate subsection ---
        items.append("##Decimate")
        items.append("decimate_percent,[10,90]")
        items.append("[1 1 1]")
        items.append("DecCurrent")
        items.append("DecTree")
        items.append("DecAll")
        items.append("[1 1]")
        items.append("Dec50")
        items.append("Dec80")

        # --- Resample subsection ---
        items.append("##Resample")
        items.append("[1 1 1]")
        items.append("ResHalfCur")
        items.append("ResHalfTree")
        items.append("ResHalfAll")
        items.append("[1 1]")
        items.append("ResDouble")
        items.append("Subdivide")

        # --- Mode Conversion subsection ---
        items.append("##Mode Conversion")
        items.append("[1 1 1]")
        items.append("ToSurfCur")
        items.append("ToSurfTree")
        items.append("ToSurfAll")
        items.append("[1 1 1]")
        items.append("ToVoxCur")
        items.append("ToVoxTree")
        items.append("ToVoxAll")

        items.append("---")

        # ==================== SCALE SECTION ====================
        items.append("#Scale")
        items.append("[1 1 1]")
        items.append("ScaleDownCur")
        items.append("ScaleDownTree")
        items.append("ScaleDownAll")
        items.append("[1 1 1]")
        items.append("ScaleUpCur")
        items.append("ScaleUpTree")
        items.append("ScaleUpAll")

        items.append("---")

        # ==================== VISIBILITY SECTION ====================
        items.append("#Visibility")

        # --- Hide subsection ---
        items.append("##Hide")
        items.append("[1 1 1 1]")
        items.append("HideCur")
        items.append("HideTree")
        items.append("HideOther")
        items.append("HideAll")
        items.append("[1 1 1 1]")
        items.append("ShowCur")
        items.append("ShowTree")
        items.append("ShowOther")
        items.append("ShowAll")
        items.append("InvertHide")

        # --- Ghost subsection ---
        items.append("##Ghost")
        items.append("[1 1 1 1]")
        items.append("GhostCur")
        items.append("GhostTree")
        items.append("GhostOther")
        items.append("GhostAll")
        items.append("[1 1 1 1]")
        items.append("UnghostCur")
        items.append("UnghostTree")
        items.append("UnghostOther")
        items.append("UnghostAll")
        items.append("InvertGhost")

        items.append("---")

        # ==================== SMART ACTIONS SECTION ====================
        items.append("#Smart Actions")

        # --- Uniform Density subsection ---
        items.append("##Uniform Density")
        items.append("[1 1]")
        items.append("UniformResampleTree")
        items.append("UniformResampleAll")
        items.append("[1 1]")
        items.append("UniformSmartTree")
        items.append("UniformSmartAll")

        # --- Other Smart Actions ---
        items.append("##Other")
        items.append("[1 1]")
        items.append("IdColorsTree")
        items.append("SplitMasked")
        items.append("MergePreserve")

        items.append("---")

        # ==================== SYMMETRY SECTION ====================
        items.append("#Symmetry")
        items.append("[1 1]")
        items.append("RemeshResymmCur")
        items.append("RemeshResymmTree")

        items.append("---")

        # ==================== AUTOPO SECTION ====================
        items.append("#Autopo")
        items.append("autopo_polycount")
        items.append("autopo_capture_details,[0,1]")
        items.append("autopo_auto_density,[0,2]")
        items.append("autopo_hardsurface")
        items.append("[1 1]")
        items.append("autopo_voxelize")
        items.append("autopo_voxelize_polycount")
        items.append("[1 1]")
        items.append("autopo_decimate_if_above")
        items.append("autopo_decimation_limit")
        items.append("[1 1]")
        items.append("autopo_tangent_smooth")
        items.append("autopo_bypass_modal")
        items.append("[1 1 1]")
        items.append("RunAutopo")
        items.append("AutopoToSculpt")
        items.append("AutopoToMultires")

        items.append("---")

        # ==================== LAYERS SECTION ====================
        items.append("#Layers")
        items.append("SetupLayers")

        items.append("---")

        # ==================== SAVE/CLOSE ====================
        items.append("SaveSettings")

        items.append("---")

        # ==================== DEV TOOLS ====================
        items.append("#Dev Tools")
        items.append("ReloadScripts")

        return items

    def process(self) -> bool:
        """
        Called each frame while dialog is open.

        Syncs panel state with disk to reflect external changes (e.g., from action scripts).
        Saves panel changes to disk when user modifies values via the panel UI.
        """
        self._sync_from_disk_and_save_ui_changes()
        return False

    def _sync_from_disk_and_save_ui_changes(self) -> None:
        """
        Smart sync: Detect if disk changed (external script) vs UI changed (user edit).

        Logic:
        1. Read current disk state
        2. If disk differs from _prev_disk, update panel UI from disk (external change)
        3. If panel UI differs from _prev_ui, save panel to disk (user change)
        """
        from utils.lks_settings import reload_brush_settings, reload_autopo_settings

        # --- BRUSH SETTINGS ---
        # Get fresh disk state
        reload_brush_settings()
        brush_disk = get_brush_settings()
        disk_brush: dict = {
            "auto_subdivide": brush_disk.auto_subdivide,
            "details_level": int(brush_disk.details_level),
            "remove_stretching": brush_disk.remove_stretching,
        }

        # Get current panel UI state
        ui_brush: dict = {
            "auto_subdivide": self.auto_subdivide,
            "details_level": int(self.details_level),
            "remove_stretching": self.remove_stretching,
        }

        # If disk changed from our last known disk state, sync UI from disk
        if disk_brush != self._prev_brush:
            self.auto_subdivide = disk_brush["auto_subdivide"]
            self.details_level = float(disk_brush["details_level"])
            self.remove_stretching = disk_brush["remove_stretching"]
            self._prev_brush = disk_brush
        # Else if UI changed from disk, save UI to disk
        elif ui_brush != disk_brush:
            self._save_brush_settings_to_cache()
            self._prev_brush = ui_brush

        # --- AUTOPO SETTINGS ---
        reload_autopo_settings()
        autopo_disk = get_autopo_settings()
        disk_autopo: dict = {
            "autopo_polycount": autopo_disk.autopo_polycount,
            "autopo_capture_details": autopo_disk.autopo_capture_details,
            "autopo_auto_density": autopo_disk.autopo_auto_density,
            "autopo_hardsurface": autopo_disk.autopo_hardsurface,
            "autopo_voxelize": autopo_disk.autopo_voxelize,
            "autopo_voxelize_polycount": autopo_disk.autopo_voxelize_polycount,
            "autopo_decimate_if_above": autopo_disk.autopo_decimate_if_above,
            "autopo_decimation_limit": autopo_disk.autopo_decimation_limit,
            "autopo_tangent_smooth": autopo_disk.autopo_tangent_smooth,
            "autopo_bypass_density_modal": autopo_disk.autopo_bypass_density_modal,
        }

        ui_autopo: dict = {
            "autopo_polycount": self.autopo_polycount,
            "autopo_capture_details": self.autopo_capture_details,
            "autopo_auto_density": self.autopo_auto_density,
            "autopo_hardsurface": self.autopo_hardsurface,
            "autopo_voxelize": self.autopo_voxelize,
            "autopo_voxelize_polycount": self.autopo_voxelize_polycount,
            "autopo_decimate_if_above": self.autopo_decimate_if_above,
            "autopo_decimation_limit": self.autopo_decimation_limit,
            "autopo_tangent_smooth": self.autopo_tangent_smooth,
            "autopo_bypass_density_modal": self.autopo_bypass_modal,
        }

        if disk_autopo != self._prev_autopo:
            self.autopo_polycount = disk_autopo["autopo_polycount"]
            self.autopo_capture_details = disk_autopo["autopo_capture_details"]
            self.autopo_auto_density = disk_autopo["autopo_auto_density"]
            self.autopo_hardsurface = disk_autopo["autopo_hardsurface"]
            self.autopo_voxelize = disk_autopo["autopo_voxelize"]
            self.autopo_voxelize_polycount = disk_autopo["autopo_voxelize_polycount"]
            self.autopo_decimate_if_above = disk_autopo["autopo_decimate_if_above"]
            self.autopo_decimation_limit = disk_autopo["autopo_decimation_limit"]
            self.autopo_tangent_smooth = disk_autopo["autopo_tangent_smooth"]
            self.autopo_bypass_modal = disk_autopo["autopo_bypass_density_modal"]
            self._prev_autopo = disk_autopo
        elif ui_autopo != disk_autopo:
            self._save_autopo_settings_to_cache()
            self._prev_autopo = ui_autopo

        # --- GENERAL SETTINGS (no external scripts modify these currently) ---
        # Just save UI changes to disk
        current_general: dict = {
            "decimate_reduction": self.decimate_percent,
        }
        if current_general != self._prev_general:
            self._save_general_settings_to_cache()
            self._prev_general = current_general

    # ==================== DYNAMIC SUBDIV HANDLERS ====================

    def _save_brush_settings_to_cache(self) -> None:
        """Save current brush settings to the brush settings cache."""
        brush_settings = get_brush_settings()
        brush_settings.auto_subdivide = self.auto_subdivide
        brush_settings.details_level = int(self.details_level)
        brush_settings.remove_stretching = self.remove_stretching
        save_brush_settings()

    def ApplyToBrushes(self) -> None:
        """Apply current dynamic subdiv settings to all brushes."""
        from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all, apply_remove_stretching_all
        apply_auto_subdivide_all(self.auto_subdivide)
        apply_details_level_all(self.details_level)
        apply_remove_stretching_all(self.remove_stretching)
        self._save_brush_settings_to_cache()
        show_message("Applied to all brushes", 2000)

    def IncrementLevel(self) -> None:
        """Increment details level by 1 (always enables auto_subdivide)."""
        from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
        self.details_level = min(8.0, self.details_level + 1.0)
        self.auto_subdivide = True
        apply_auto_subdivide_all(True)
        apply_details_level_all(self.details_level)
        self._save_brush_settings_to_cache()
        show_message(f"Details: {self.details_level}", 1500)

    def DecrementLevel(self) -> None:
        """Decrement details level by 1 (always enables auto_subdivide)."""
        from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
        self.details_level = max(0.0, self.details_level - 1.0)
        self.auto_subdivide = True
        apply_auto_subdivide_all(True)
        apply_details_level_all(self.details_level)
        self._save_brush_settings_to_cache()
        show_message(f"Details: {self.details_level}", 1500)

    # ==================== DECIMATE HANDLERS ====================

    def DecCurrent(self) -> None:
        """Decimate current selection."""
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.CURRENT, reduction_percent=float(
            self.decimate_percent))

    def DecTree(self) -> None:
        """Decimate current subtree."""
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.TREE, reduction_percent=float(self.decimate_percent))

    def DecAll(self) -> None:
        """Decimate all sculpt objects."""
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.ALL, reduction_percent=float(self.decimate_percent))

    def Dec50(self) -> None:
        """Quick decimate 50%."""
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        self.decimate_percent = 50
        op_main(scope=Scope.CURRENT, reduction_percent=50.0)

    def Dec80(self) -> None:
        """Quick decimate 80%."""
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        self.decimate_percent = 80
        op_main(scope=Scope.CURRENT, reduction_percent=80.0)

    # ==================== RESAMPLE HANDLERS ====================

    def _resample_elements(self, elements: list, scale: float) -> int:
        """Helper to resample a list of elements."""
        from utils.Volume_resample_utils import execute_resample
        from utils.Volume_mode_utils import ensure_surface_mode
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                target = int(vol.getPolycount() * scale)
                execute_resample(
                    target_polycount=target, scale=scale)
                count += 1
        return count

    def ResHalfCur(self) -> None:
        """Resample current to half."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count = self._resample_elements(elements, 0.5)
        show_message(f"Resampled {count} obj", 2000)

    def ResHalfTree(self) -> None:
        """Resample subtree to half."""
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            show_message("No selection", 2000)
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._resample_elements(elements, 0.5)
        current.selectOne()
        show_message(f"Resampled {count} obj", 2000)

    def ResHalfAll(self) -> None:
        """Resample all to half."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._resample_elements(elements, 0.5)
        show_message(f"Resampled {count} obj", 2000)

    def ResDouble(self) -> None:
        """Resample current to double."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count = self._resample_elements(elements, 2.0)
        show_message(f"Resampled {count} obj", 2000)

    def Subdivide(self) -> None:
        """Subdivide current (double polys)."""
        from utils.Volume_subdivide_utils import subdivide_once
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            show_message("No selection", 2000)
            return
        current.selectOne()
        subdivide_once()
        show_message("Subdivided", 2000)

    # ==================== MODE CONVERSION HANDLERS ====================

    def _convert_to_surface(self, elements: list) -> int:
        """Helper to convert elements to surface."""
        from utils.Volume_mode_utils import convert_to_surface
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                if vol.isVoxelized():
                    convert_to_surface(vol)
                    count += 1
        return count

    def _convert_to_voxels(self, elements: list) -> int:
        """Helper to convert elements to voxels."""
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                if vol.isSurface():
                    vol.toVoxels()
                    count += 1
        return count

    def ToSurfCur(self) -> None:
        """Convert current to surface."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._convert_to_surface(elements)
        show_message(f"Converted {count}", 2000)

    def ToSurfTree(self) -> None:
        """Convert subtree to surface."""
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._convert_to_surface(elements)
        current.selectOne()
        show_message(f"Converted {count}", 2000)

    def ToSurfAll(self) -> None:
        """Convert all to surface."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._convert_to_surface(elements)
        show_message(f"Converted {count}", 2000)

    def ToVoxCur(self) -> None:
        """Convert current to voxels."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._convert_to_voxels(elements)
        show_message(f"Converted {count}", 2000)

    def ToVoxTree(self) -> None:
        """Convert subtree to voxels."""
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._convert_to_voxels(elements)
        current.selectOne()
        show_message(f"Converted {count}", 2000)

    def ToVoxAll(self) -> None:
        """Convert all to voxels."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._convert_to_voxels(elements)
        show_message(f"Converted {count}", 2000)

    # ==================== SCALE HANDLERS ====================

    def _scale_elements(self, elements: list, factor: float) -> int:
        """Helper to scale elements."""
        from utils.object_utils import scale_element
        count: int = 0
        for el in elements:
            scale_element(el, factor)
            count += 1
        return count

    def ScaleDownCur(self) -> None:
        """Scale current down 100x."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._scale_elements(elements, 0.01)
        show_message(f"Scaled {count}", 2000)

    def ScaleDownTree(self) -> None:
        """Scale subtree down 100x."""
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._scale_elements(elements, 0.01)
        current.selectOne()
        show_message(f"Scaled {count}", 2000)

    def ScaleDownAll(self) -> None:
        """Scale all down 100x."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._scale_elements(elements, 0.01)
        show_message(f"Scaled {count}", 2000)

    def ScaleUpCur(self) -> None:
        """Scale current up 100x."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._scale_elements(elements, 100.0)
        show_message(f"Scaled {count}", 2000)

    def ScaleUpTree(self) -> None:
        """Scale subtree up 100x."""
        from utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._scale_elements(elements, 100.0)
        current.selectOne()
        show_message(f"Scaled {count}", 2000)

    def ScaleUpAll(self) -> None:
        """Scale all up 100x."""
        from utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._scale_elements(elements, 100.0)
        show_message(f"Scaled {count}", 2000)

    # ==================== HIDE/SHOW HANDLERS ====================

    def _get_other_elements(self, selected: list, all_elements: list) -> list:
        """Get elements NOT in the selected subtrees."""
        # Build set of all elements in selected subtrees
        from utils.scene_api import SceneAPI
        excluded: set = set()
        for sel in selected:
            subtree = SceneAPI.collect_subtree(sel)
            excluded.update(subtree)
        return [el for el in all_elements if el not in excluded]

    def HideCur(self) -> None:
        """Hide current selection."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.get_selected_elements()
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def HideTree(self) -> None:
        """Hide current subtree."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def HideOther(self) -> None:
        """Hide all except selection subtree."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        others = self._get_other_elements(selected, all_elements)
        count = set_visibility(others, False)
        show_message(f"Hid {count}", 2000)

    def HideAll(self) -> None:
        """Hide all."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.collect_all_sculpt_objects()
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def ShowCur(self) -> None:
        """Show current selection."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.get_selected_elements()
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def ShowTree(self) -> None:
        """Show current subtree."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def ShowOther(self) -> None:
        """Show all except selection subtree."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        others = self._get_other_elements(selected, all_elements)
        count = set_visibility(others, True)
        show_message(f"Shown {count}", 2000)

    def ShowAll(self) -> None:
        """Show all."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.collect_all_sculpt_objects()
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def InvertHide(self) -> None:
        """Invert visibility on all."""
        from utils.scene_api import SceneAPI
        from utils.SceneElement_visibility_utils import invert_visibility_on_elements
        elements = SceneAPI.collect_all_sculpt_objects()
        count = invert_visibility_on_elements(elements)
        show_message(f"Inverted {count}", 2000)

    # ==================== GHOST HANDLERS ====================

    def GhostCur(self) -> None:
        """Ghost current selection."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.CURRENT, ghost=True)

    def GhostTree(self) -> None:
        """Ghost current subtree."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.TREE, ghost=True)

    def GhostOther(self) -> None:
        """Ghost all except selection subtree."""
        from ops.SculptObject_SetGhost import main as op_main, GhostMode
        from utils.scope_utils import Scope
        op_main(scope=Scope.CURRENT, mode=GhostMode.ISOLATE)

    def GhostAll(self) -> None:
        """Ghost all."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.ALL, ghost=True)

    def UnghostCur(self) -> None:
        """Unghost current selection."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.CURRENT, ghost=False)

    def UnghostTree(self) -> None:
        """Unghost current subtree."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.TREE, ghost=False)

    def UnghostOther(self) -> None:
        """Unghost all except selection subtree."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.OTHER, ghost=False)

    def UnghostAll(self) -> None:
        """Unghost all."""
        from ops.SculptObject_SetGhost import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.ALL, ghost=False)

    def InvertGhost(self) -> None:
        """Invert ghost on all."""
        from ops.SculptObject_SetGhost import main as op_main, GhostMode
        from utils.scope_utils import Scope
        op_main(scope=Scope.ALL, mode=GhostMode.INVERT)

    # ==================== SMART ACTIONS HANDLERS ====================

    def _uniform_resample_elements(self, reference: 'coat.SceneElement', elements: list) -> int:
        """Helper: Resample elements to match reference density."""
        from utils.Volume_density_utils import resample_to_match_density
        ref_vol = reference.Volume()
        count: int = 0
        for el in elements:
            if el != reference and el.isSculptObject():
                resample_to_match_density(el, ref_vol)
                count += 1
        return count

    def _uniform_smart_elements(self, reference: 'coat.SceneElement', elements: list) -> tuple:
        """Helper: Smart density match elements to reference."""
        from utils.Volume_density_utils import smart_match_density
        ref_vol = reference.Volume()
        subdivided: int = 0
        decimated: int = 0
        resampled: int = 0
        for el in elements:
            if el != reference and el.isSculptObject():
                result = smart_match_density(el, ref_vol)
                if result == "subdivided":
                    subdivided += 1
                elif result == "decimated":
                    decimated += 1
                elif result == "resampled":
                    resampled += 1
        return subdivided, decimated, resampled

    def UniformResampleTree(self) -> None:
        """Resample subtree children to match selected object's density."""
        from utils.scene_api import SceneAPI
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a sculpt object", 2000)
            return
        subtree = SceneAPI.collect_subtree(reference)
        children = [el for el in subtree if el != reference]
        if not children:
            show_message("No children to process", 2000)
            return
        count = self._uniform_resample_elements(reference, children)
        reference.selectOne()
        show_message(f"Resampled {count} to uniform", 2000)

    def UniformResampleAll(self) -> None:
        """Resample ALL sculpt objects to match selected object's density."""
        from utils.scene_api import SceneAPI
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a reference object", 2000)
            return
        all_elements = SceneAPI.collect_all_sculpt_objects()
        if len(all_elements) <= 1:
            show_message("No other objects to process", 2000)
            return
        count = self._uniform_resample_elements(reference, all_elements)
        reference.selectOne()
        show_message(f"Resampled {count} to uniform", 2000)

    def UniformSmartTree(self) -> None:
        """Smart density match subtree (subdivide/decimate/resample)."""
        from utils.scene_api import SceneAPI
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a sculpt object", 2000)
            return
        subtree = SceneAPI.collect_subtree(reference)
        children = [el for el in subtree if el != reference]
        if not children:
            show_message("No children to process", 2000)
            return
        sub, dec, res = self._uniform_smart_elements(reference, children)
        reference.selectOne()
        show_message(f"Sub:{sub} Dec:{dec} Res:{res}", 2000)

    def UniformSmartAll(self) -> None:
        """Smart density match ALL objects to selected reference."""
        from utils.scene_api import SceneAPI
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a reference object", 2000)
            return
        all_elements = SceneAPI.collect_all_sculpt_objects()
        if len(all_elements) <= 1:
            show_message("No other objects to process", 2000)
            return
        sub, dec, res = self._uniform_smart_elements(reference, all_elements)
        reference.selectOne()
        show_message(f"Sub:{sub} Dec:{dec} Res:{res}", 2000)

    def RemeshResymmCur(self) -> None:
        """Remesh and symmetrize current selection."""
        from utils.scene_api import SceneAPI
        from utils.Volume_subdivide_utils import make_symmetrical
        from utils.Volume_mode_utils import ensure_surface_mode
        from utils.Scene_cleanup_utils import cleanup_after_mesh_operation
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                make_symmetrical()
                count += 1
        cleanup_after_mesh_operation()
        show_message(f"Resymmed {count}", 2000)

    def RemeshResymmTree(self) -> None:
        """Remesh and symmetrize subtree."""
        from utils.scene_api import SceneAPI
        from utils.Volume_subdivide_utils import make_symmetrical
        from utils.Volume_mode_utils import ensure_surface_mode
        from utils.Scene_cleanup_utils import cleanup_after_mesh_operation
        current = SceneAPI.get_current_element()
        if not current:
            show_message("No selection", 2000)
            return
        elements = SceneAPI.collect_subtree(current)
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                make_symmetrical()
                count += 1
        current.selectOne()
        cleanup_after_mesh_operation()
        show_message(f"Resymmed {count}", 2000)

    def IdColorsTree(self) -> None:
        """Fill subtree with random ID colors."""
        from ops.SculptObject_IdColors import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.TREE)

    def SplitMasked(self) -> None:
        """Split frozen/masked area to new object."""
        from utils.scene_api import SceneAPI
        from utils.Volume_mode_utils import ensure_surface_mode
        from utils.coat_ui_utils import (
            CMD_HIDE_FROZEN_AREA,
            CMD_SEPARATE_HIDDEN,
            CMD_DIALOG_OK,
            wait_frames,
        )
        current = SceneAPI.get_current_element()
        if not current or not current.isSculptObject():
            show_message("Select a sculpt object", 2000)
            return
        vol = current.Volume()
        ensure_surface_mode(vol)
        current.selectOne()
        # Hide frozen area
        coat.ui.cmd(CMD_HIDE_FROZEN_AREA)
        wait_frames(2)
        # Separate hidden
        coat.ui.cmd(CMD_SEPARATE_HIDDEN, lambda: coat.ui.cmd(CMD_DIALOG_OK))
        wait_frames(4)
        show_message("Split masked area", 2000)

    def MergePreserve(self) -> None:
        """Merge subtree preserving separate parts."""
        from utils.scene_api import SceneAPI
        from utils.coat_ui_utils import wait_frames
        current = SceneAPI.get_current_element()
        if not current:
            show_message("No selection", 2000)
            return
        current.selectOne()
        current.mergeSubtree()
        wait_frames(4)
        show_message("Merged subtree", 2000)

    # ==================== AUTOPO HANDLERS ====================

    def _get_autopo_params(self):
        """Build AutopoParams from current settings."""
        from utils.autopo_utils import AutopoParams
        # Debug: print all panel values being used
        print(f"[LKS Panel] _get_autopo_params:")
        print(f"  autopo_polycount = {self.autopo_polycount}")
        print(f"  autopo_voxelize = {self.autopo_voxelize}")
        print(f"  autopo_decimate_if_above = {self.autopo_decimate_if_above}")
        return AutopoParams(
            target_polycount=self.autopo_polycount,
            capture_details=self.autopo_capture_details,
            auto_density=self.autopo_auto_density,
            hardsurface=self.autopo_hardsurface,
            voxelize=self.autopo_voxelize,
            voxelize_polycount=self.autopo_voxelize_polycount,
            decimate_if_above=self.autopo_decimate_if_above,
            decimation_limit=self.autopo_decimation_limit,
            tangent_smooth=self.autopo_tangent_smooth,
            bypass_density_modal=self.autopo_bypass_modal,
        )

    def _save_autopo_settings_to_cache(self) -> None:
        """Save autopo settings to autopo settings cache."""
        autopo_settings = get_autopo_settings()
        autopo_settings.autopo_polycount = self.autopo_polycount
        autopo_settings.autopo_capture_details = self.autopo_capture_details
        autopo_settings.autopo_auto_density = self.autopo_auto_density
        autopo_settings.autopo_hardsurface = self.autopo_hardsurface
        autopo_settings.autopo_voxelize = self.autopo_voxelize
        autopo_settings.autopo_voxelize_polycount = self.autopo_voxelize_polycount
        autopo_settings.autopo_decimate_if_above = self.autopo_decimate_if_above
        autopo_settings.autopo_decimation_limit = self.autopo_decimation_limit
        autopo_settings.autopo_tangent_smooth = self.autopo_tangent_smooth
        autopo_settings.autopo_bypass_density_modal = self.autopo_bypass_modal
        save_autopo_settings()

    def _save_general_settings_to_cache(self) -> None:
        """Save general settings to general settings cache."""
        settings = get_settings()
        settings.decimate_reduction = self.decimate_percent
        save_settings()

    def _save_autopo_settings(self) -> None:
        """Save autopo settings to cache. (Legacy - calls new method)"""
        self._save_autopo_settings_to_cache()

    def RunAutopo(self) -> None:
        """Run autopo with current settings."""
        from utils.autopo_utils import execute_autopo
        self._save_autopo_settings_to_cache()
        params = self._get_autopo_params()
        print(
            f"[LKS Panel] RunAutopo with params: target_polycount={params.target_polycount}")
        print(
            f"[LKS Panel] Panel value: self.autopo_polycount={self.autopo_polycount}")
        execute_autopo(params)

    def AutopoToSculpt(self) -> None:
        """Run autopo and import to sculpt."""
        from utils.autopo_utils import autopo_to_sculpt
        self._save_autopo_settings_to_cache()
        params = self._get_autopo_params()
        print(
            f"[LKS Panel] AutopoToSculpt with params: target_polycount={params.target_polycount}")
        autopo_to_sculpt(params)

    def AutopoToMultires(self) -> None:
        """Run autopo and import as multiresolution."""
        from utils.autopo_utils import autopo_to_multiresolution
        self._save_autopo_settings_to_cache()
        params = self._get_autopo_params()
        print(
            f"[LKS Panel] AutopoToMultires with params: target_polycount={params.target_polycount}")
        autopo_to_multiresolution(params)

    # ==================== LAYERS HANDLER ====================

    def SetupLayers(self) -> None:
        """Setup standard two-layer configuration."""
        from utils.Scene_layer_utils import ensure_standard_layers
        ensure_standard_layers()
        show_message("Layers configured", 2000)

    # ==================== SAVE HANDLER ====================

    def SaveSettings(self) -> None:
        """Save all settings to disk (brush, autopo, and general)."""
        # Save brush settings
        self._save_brush_settings_to_cache()
        # Save autopo settings
        self._save_autopo_settings_to_cache()
        # Save general settings
        self._save_general_settings_to_cache()
        show_message("All settings saved", 2000)

    # ==================== DEV TOOLS HANDLER ====================

    def ReloadScripts(self) -> None:
        """Reload all _utils modules to pick up code changes."""
        import importlib
        import sys

        # List of modules to reload (in dependency order)
        modules_to_reload: list[str] = [
            '_utils.lks_settings',
            '_utils.coat_ui_utils',
            '_utils.scene_api',
            '_utils.scope_utils',
            '_utils.object_utils',
            '_utils.Volume_decimate_utils',
            '_utils.Volume_resample_utils',
            '_utils.Volume_subdivide_utils',
            '_utils.Volume_mode_utils',
            '_utils.Volume_density_utils',
            '_utils.Scene_cleanup_utils',
            '_utils.Scene_layer_utils',
            '_utils.Scene_tiling_utils',
            '_utils.SceneElement_visibility_utils',
            '_utils.SceneElement_boolean_utils',
            '_utils.brush_settings_utils',
            '_utils.autopo_utils',
            '_utils.scene_iteration_utils',
        ]

        reloaded_count: int = 0
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    print(f"[LKS] Reloaded: {module_name}")
                    reloaded_count += 1
                except Exception as e:
                    print(f"[LKS] Failed to reload {module_name}: {e}")
            else:
                print(f"[LKS] Not loaded: {module_name}")

        show_message(f"Reloaded {reloaded_count} modules", 2000)


def show_lks_tools_panel() -> None:
    """Show the LKS Tools configuration panel."""
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
        .width(320) \
        .buttons("Close") \
        .params(config) \
        .process(config.process) \
        .show()

    # Save state when closed
    coat.io.toJson(config, settings_path)


# Run when script is executed directly
show_lks_tools_panel()
