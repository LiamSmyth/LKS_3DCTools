"""
LKS Tools Panel - Comprehensive Configuration Dashboard

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

        # ==================== AUTOPO (all parameters) ====================
        self.autopo_polycount: int = settings.autopo_polycount
        self.autopo_capture_details: float = settings.autopo_capture_details
        self.autopo_auto_density: float = settings.autopo_auto_density
        self.autopo_hardsurface: bool = settings.autopo_hardsurface
        self.autopo_voxelize: bool = settings.autopo_voxelize
        self.autopo_voxelize_polycount: int = settings.autopo_voxelize_polycount
        self.autopo_decimate_if_above: bool = settings.autopo_decimate_if_above
        self.autopo_decimation_limit: int = settings.autopo_decimation_limit
        self.autopo_tangent_smooth: bool = settings.autopo_tangent_smooth
        self.autopo_bypass_modal: bool = settings.autopo_bypass_density_modal

        # ==================== DECIMATE ====================
        self.decimate_percent: int = 50  # Reduction percentage

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
        items.append("UniformResample")
        items.append("UniformSmart")

        # --- Remesh/Symmetry subsection ---
        items.append("##Remesh + Symmetry")
        items.append("[1 1]")
        items.append("RemeshResymmCur")
        items.append("RemeshResymmTree")

        # --- Other Smart Actions ---
        items.append("##Other")
        items.append("[1 1]")
        items.append("IdColorsTree")
        items.append("SplitMasked")
        items.append("MergePreserve")

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

        return items

    def process(self) -> bool:
        """Called each frame while dialog is open."""
        return False

    # ==================== DYNAMIC SUBDIV HANDLERS ====================

    def ApplyToBrushes(self) -> None:
        """Apply current dynamic subdiv settings to all brushes."""
        from _utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all, apply_remove_stretching_all
        apply_auto_subdivide_all(self.auto_subdivide)
        apply_details_level_all(self.details_level)
        apply_remove_stretching_all(self.remove_stretching)
        show_message("Applied to all brushes", 2000)

    def IncrementLevel(self) -> None:
        """Increment details level by 1 (always enables auto_subdivide)."""
        from _utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
        self.details_level = min(8.0, self.details_level + 1.0)
        self.auto_subdivide = True
        apply_auto_subdivide_all(True)
        apply_details_level_all(self.details_level)
        show_message(f"Details: {self.details_level}", 1500)

    def DecrementLevel(self) -> None:
        """Decrement details level by 1 (always enables auto_subdivide)."""
        from _utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
        self.details_level = max(0.0, self.details_level - 1.0)
        self.auto_subdivide = True
        apply_auto_subdivide_all(True)
        apply_details_level_all(self.details_level)
        show_message(f"Details: {self.details_level}", 1500)

    # ==================== DECIMATE HANDLERS ====================

    def _decimate_elements(self, elements: list) -> int:
        """Helper to decimate a list of elements."""
        from _utils.mesh_utils import DecimateParams, execute_decimate, ensure_surface_mode
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                execute_decimate(DecimateParams(
                    reduction_percent=float(self.decimate_percent)))
                count += 1
        return count

    def DecCurrent(self) -> None:
        """Decimate current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import cleanup_after_mesh_operation
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count = self._decimate_elements(elements)
        cleanup_after_mesh_operation()
        show_message(f"Decimated {count} obj", 2000)

    def DecTree(self) -> None:
        """Decimate current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import cleanup_after_mesh_operation
        current = SceneAPI.get_current_element()
        if not current:
            show_message("No selection", 2000)
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._decimate_elements(elements)
        current.selectOne()
        cleanup_after_mesh_operation()
        show_message(f"Decimated {count} obj", 2000)

    def DecAll(self) -> None:
        """Decimate all sculpt objects."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import cleanup_after_mesh_operation
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._decimate_elements(elements)
        cleanup_after_mesh_operation()
        show_message(f"Decimated {count} obj", 2000)

    def Dec50(self) -> None:
        """Quick decimate 50%."""
        self.decimate_percent = 50
        self.DecCurrent()

    def Dec80(self) -> None:
        """Quick decimate 80%."""
        self.decimate_percent = 80
        self.DecCurrent()

    # ==================== RESAMPLE HANDLERS ====================

    def _resample_elements(self, elements: list, scale: float) -> int:
        """Helper to resample a list of elements."""
        from _utils.mesh_utils import execute_resample, ResampleParams, ensure_surface_mode
        count: int = 0
        for el in elements:
            if el.isSculptObject():
                vol = el.Volume()
                ensure_surface_mode(vol)
                el.selectOne()
                target = int(vol.getPolycount() * scale)
                execute_resample(ResampleParams(
                    target_polycount=target, scale=scale))
                count += 1
        return count

    def ResHalfCur(self) -> None:
        """Resample current to half."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count = self._resample_elements(elements, 0.5)
        show_message(f"Resampled {count} obj", 2000)

    def ResHalfTree(self) -> None:
        """Resample subtree to half."""
        from _utils.scene_api import SceneAPI
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
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._resample_elements(elements, 0.5)
        show_message(f"Resampled {count} obj", 2000)

    def ResDouble(self) -> None:
        """Resample current to double."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        if not elements:
            show_message("No selection", 2000)
            return
        count = self._resample_elements(elements, 2.0)
        show_message(f"Resampled {count} obj", 2000)

    def Subdivide(self) -> None:
        """Subdivide current (double polys)."""
        from _utils.mesh_utils import subdivide_once
        from _utils.scene_api import SceneAPI
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
        from _utils.mesh_utils import convert_to_surface
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
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._convert_to_surface(elements)
        show_message(f"Converted {count}", 2000)

    def ToSurfTree(self) -> None:
        """Convert subtree to surface."""
        from _utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._convert_to_surface(elements)
        current.selectOne()
        show_message(f"Converted {count}", 2000)

    def ToSurfAll(self) -> None:
        """Convert all to surface."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._convert_to_surface(elements)
        show_message(f"Converted {count}", 2000)

    def ToVoxCur(self) -> None:
        """Convert current to voxels."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._convert_to_voxels(elements)
        show_message(f"Converted {count}", 2000)

    def ToVoxTree(self) -> None:
        """Convert subtree to voxels."""
        from _utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._convert_to_voxels(elements)
        current.selectOne()
        show_message(f"Converted {count}", 2000)

    def ToVoxAll(self) -> None:
        """Convert all to voxels."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._convert_to_voxels(elements)
        show_message(f"Converted {count}", 2000)

    # ==================== SCALE HANDLERS ====================

    def _scale_elements(self, elements: list, factor: float) -> int:
        """Helper to scale elements."""
        from _utils.object_utils import scale_element
        count: int = 0
        for el in elements:
            scale_element(el, factor)
            count += 1
        return count

    def ScaleDownCur(self) -> None:
        """Scale current down 100x."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._scale_elements(elements, 0.01)
        show_message(f"Scaled {count}", 2000)

    def ScaleDownTree(self) -> None:
        """Scale subtree down 100x."""
        from _utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._scale_elements(elements, 0.01)
        current.selectOne()
        show_message(f"Scaled {count}", 2000)

    def ScaleDownAll(self) -> None:
        """Scale all down 100x."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._scale_elements(elements, 0.01)
        show_message(f"Scaled {count}", 2000)

    def ScaleUpCur(self) -> None:
        """Scale current up 100x."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.get_selected_elements()
        count = self._scale_elements(elements, 100.0)
        show_message(f"Scaled {count}", 2000)

    def ScaleUpTree(self) -> None:
        """Scale subtree up 100x."""
        from _utils.scene_api import SceneAPI
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = self._scale_elements(elements, 100.0)
        current.selectOne()
        show_message(f"Scaled {count}", 2000)

    def ScaleUpAll(self) -> None:
        """Scale all up 100x."""
        from _utils.scene_api import SceneAPI
        elements = SceneAPI.collect_all_sculpt_objects()
        count = self._scale_elements(elements, 100.0)
        show_message(f"Scaled {count}", 2000)

    # ==================== HIDE/SHOW HANDLERS ====================

    def _get_other_elements(self, selected: list, all_elements: list) -> list:
        """Get elements NOT in the selected subtrees."""
        # Build set of all elements in selected subtrees
        from _utils.scene_api import SceneAPI
        excluded: set = set()
        for sel in selected:
            subtree = SceneAPI.collect_subtree(sel)
            excluded.update(subtree)
        return [el for el in all_elements if el not in excluded]

    def HideCur(self) -> None:
        """Hide current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.get_selected_elements()
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def HideTree(self) -> None:
        """Hide current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def HideOther(self) -> None:
        """Hide all except selection subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        others = self._get_other_elements(selected, all_elements)
        count = set_visibility(others, False)
        show_message(f"Hid {count}", 2000)

    def HideAll(self) -> None:
        """Hide all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.collect_all_sculpt_objects()
        count = set_visibility(elements, False)
        show_message(f"Hid {count}", 2000)

    def ShowCur(self) -> None:
        """Show current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.get_selected_elements()
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def ShowTree(self) -> None:
        """Show current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def ShowOther(self) -> None:
        """Show all except selection subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        others = self._get_other_elements(selected, all_elements)
        count = set_visibility(others, True)
        show_message(f"Shown {count}", 2000)

    def ShowAll(self) -> None:
        """Show all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_visibility
        elements = SceneAPI.collect_all_sculpt_objects()
        count = set_visibility(elements, True)
        show_message(f"Shown {count}", 2000)

    def InvertHide(self) -> None:
        """Invert visibility on all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import invert_visibility_on_elements
        elements = SceneAPI.collect_all_sculpt_objects()
        count = invert_visibility_on_elements(elements)
        show_message(f"Inverted {count}", 2000)

    # ==================== GHOST HANDLERS ====================

    def GhostCur(self) -> None:
        """Ghost current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        elements = SceneAPI.get_selected_elements()
        count = set_ghost(elements, True)
        show_message(f"Ghosted {count}", 2000)

    def GhostTree(self) -> None:
        """Ghost current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_ghost(elements, True)
        show_message(f"Ghosted {count}", 2000)

    def GhostOther(self) -> None:
        """Ghost all except selection subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import ghost_except
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        count = ghost_except(all_elements, selected)
        show_message(f"Ghosted {count}", 2000)

    def GhostAll(self) -> None:
        """Ghost all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        elements = SceneAPI.collect_all_sculpt_objects()
        count = set_ghost(elements, True)
        show_message(f"Ghosted {count}", 2000)

    def UnghostCur(self) -> None:
        """Unghost current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        elements = SceneAPI.get_selected_elements()
        count = set_ghost(elements, False)
        show_message(f"Unghosted {count}", 2000)

    def UnghostTree(self) -> None:
        """Unghost current subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        current = SceneAPI.get_current_element()
        if not current:
            return
        elements = SceneAPI.collect_subtree(current)
        count = set_ghost(elements, False)
        show_message(f"Unghosted {count}", 2000)

    def UnghostOther(self) -> None:
        """Unghost all except selection subtree."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import set_ghost
        selected = SceneAPI.get_selected_elements()
        all_elements = SceneAPI.collect_all_sculpt_objects()
        others = self._get_other_elements(selected, all_elements)
        count = set_ghost(others, False)
        show_message(f"Unghosted {count}", 2000)

    def UnghostAll(self) -> None:
        """Unghost all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import unghost_elements
        elements = SceneAPI.collect_all_sculpt_objects()
        count = unghost_elements(elements)
        show_message(f"Unghosted {count}", 2000)

    def InvertGhost(self) -> None:
        """Invert ghost on all."""
        from _utils.scene_api import SceneAPI
        from _utils.SceneElement_visibility_utils import invert_ghost_on_elements
        elements = SceneAPI.collect_all_sculpt_objects()
        count = invert_ghost_on_elements(elements)
        show_message(f"Inverted {count}", 2000)

    # ==================== SMART ACTIONS HANDLERS ====================

    def UniformResample(self) -> None:
        """Resample subtree children to match parent density."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import resample_to_match_density
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a sculpt object", 2000)
            return
        ref_vol = reference.Volume()
        subtree = SceneAPI.collect_subtree(reference)
        children = [el for el in subtree if el !=
                    reference and el.isSculptObject()]
        if not children:
            show_message("No children to process", 2000)
            return
        count: int = 0
        for child in children:
            resample_to_match_density(child, ref_vol)
            count += 1
        reference.selectOne()
        show_message(f"Resampled {count} to uniform", 2000)

    def UniformSmart(self) -> None:
        """Smart density match subtree (subdivide/decimate)."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import smart_match_density
        reference = SceneAPI.get_current_element()
        if not reference or not reference.isSculptObject():
            show_message("Select a sculpt object", 2000)
            return
        ref_vol = reference.Volume()
        subtree = SceneAPI.collect_subtree(reference)
        children = [el for el in subtree if el !=
                    reference and el.isSculptObject()]
        if not children:
            show_message("No children to process", 2000)
            return
        subdivided: int = 0
        decimated: int = 0
        for child in children:
            result = smart_match_density(child, ref_vol)
            if result == "subdivided":
                subdivided += 1
            elif result == "decimated":
                decimated += 1
        reference.selectOne()
        show_message(f"Sub:{subdivided} Dec:{decimated}", 2000)

    def RemeshResymmCur(self) -> None:
        """Remesh and symmetrize current selection."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import make_symmetrical, ensure_surface_mode
        from _utils.mesh_utils import cleanup_after_mesh_operation
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
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import make_symmetrical, ensure_surface_mode
        from _utils.mesh_utils import cleanup_after_mesh_operation
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
        import random
        from _utils.scene_api import SceneAPI
        from _utils.coat_ui_utils import CMD_FILL_LAYER
        reference = SceneAPI.get_current_element()
        if not reference:
            show_message("No selection", 2000)
            return
        subtree = SceneAPI.collect_subtree(reference)
        for el in subtree:
            if el.isSculptObject():
                el.selectOne()
                el.setVisibility(True)
                r = random.uniform(0, 255)
                g = random.uniform(0, 255)
                b = random.uniform(0, 255)
                coat.Volume.color(r, g, b)
                coat.ui.cmd(CMD_FILL_LAYER)
                el.setVisibility(False)
        # Show all again
        for el in subtree:
            el.setVisibility(True)
        reference.selectOne()
        show_message(f"Filled {len(subtree)} with ID colors", 2000)

    def SplitMasked(self) -> None:
        """Split frozen/masked area to new object."""
        from _utils.scene_api import SceneAPI
        from _utils.mesh_utils import ensure_surface_mode
        from _utils.coat_ui_utils import (
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
        from _utils.scene_api import SceneAPI
        from _utils.coat_ui_utils import wait_frames
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
        from _utils.autopo_utils import AutopoParams
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

    def _save_autopo_settings(self) -> None:
        """Save autopo settings to cache."""
        settings = get_settings()
        settings.autopo_polycount = self.autopo_polycount
        settings.autopo_capture_details = self.autopo_capture_details
        settings.autopo_auto_density = self.autopo_auto_density
        settings.autopo_hardsurface = self.autopo_hardsurface
        settings.autopo_voxelize = self.autopo_voxelize
        settings.autopo_voxelize_polycount = self.autopo_voxelize_polycount
        settings.autopo_decimate_if_above = self.autopo_decimate_if_above
        settings.autopo_decimation_limit = self.autopo_decimation_limit
        settings.autopo_tangent_smooth = self.autopo_tangent_smooth
        settings.autopo_bypass_density_modal = self.autopo_bypass_modal
        save_settings()

    def RunAutopo(self) -> None:
        """Run autopo with current settings."""
        from _utils.autopo_utils import execute_autopo
        self._save_autopo_settings()
        execute_autopo(self._get_autopo_params())

    def AutopoToSculpt(self) -> None:
        """Run autopo and import to sculpt."""
        from _utils.autopo_utils import autopo_to_sculpt
        self._save_autopo_settings()
        autopo_to_sculpt(self._get_autopo_params())

    def AutopoToMultires(self) -> None:
        """Run autopo and import as multiresolution."""
        from _utils.autopo_utils import autopo_to_multiresolution
        self._save_autopo_settings()
        autopo_to_multiresolution(self._get_autopo_params())

    # ==================== LAYERS HANDLER ====================

    def SetupLayers(self) -> None:
        """Setup standard two-layer configuration."""
        from _utils.Scene_layer_utils import ensure_standard_layers
        ensure_standard_layers()
        show_message("Layers configured", 2000)

    # ==================== SAVE HANDLER ====================

    def SaveSettings(self) -> None:
        """Save all settings to disk."""
        settings = get_settings()
        settings.auto_subdivide = self.auto_subdivide
        settings.details_level = int(self.details_level)
        settings.remove_stretching = self.remove_stretching
        self._save_autopo_settings()
        save_settings()
        show_message("Settings saved", 2000)


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
