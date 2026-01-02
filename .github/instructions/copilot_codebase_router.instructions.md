---
applyTo: '**'
---

# LKS 3DCoat Addon - Codebase Router

A ledger of existing code, utilities, and resources. This file provides quick links to what currently exists in the repository.

## 🚦 Start Here

- `copilot_style_guide.instructions.md`: Python scripting conventions for this workspace
- `copilot_3dcoat.instructions.md`: 3DCoat-specific patterns, folder visibility, panel development
- `copilot_3dcoat_api.instructions.md`: 3DCoat API reference, magic strings, known commands

## 🖥️ Environment

- **Windows + PowerShell** - Chain commands with `;`, normalize paths with `Resolve-Path`
- **Self-contained** - No pip, no venv, no external dependencies
- **3DCoat embedded Python** - The `coat` module is provided at runtime

## 🗺️ Folder Structure

```
UserProjects/
├── <ActionScript>.py          # Exposed to 3DCoat - minimal invokers
├── LKS_Tools_Panel.py         # Main tools panel with all functionality
├── _utils/                    # Hidden from 3DCoat - shared utilities
│   ├── __init__.py            # Package exports
│   ├── scene_api.py           # Thin wrappers for coat iterators
│   ├── scope_utils.py         # Scope enum and resolution
│   ├── visibility_utils.py    # Pure visibility/ghost functions
│   ├── layer_utils.py         # Layer management
│   ├── coat_ui_utils.py       # UI command abstractions
│   ├── object_utils.py        # Object manipulation
│   ├── mesh_utils.py          # Mesh operations (decimate, resample, etc.)
│   ├── SceneElement_boolean_utils.py # 🆕 Live boolean operations
│   ├── Scene_tiling_utils.py  # 🆕 Tiling grid setup
│   ├── lks_settings.py        # Persistent settings singleton
│   ├── brush_settings_utils.py # Brush configuration
│   ├── autopo_utils.py        # Autopo workflow automation
│   └── scene_iteration_utils.py # Legacy - prefer scene_api.py
├── _archive/                  # Old/deprecated scripts
├── _example_code/             # Reference implementations
└── <Category>/                # Visible subfolders become categories
```

**Visibility rules:**
- Root `.py` files appear in 3DCoat's script browser
- `_` prefixed folders are hidden but importable
- Non-prefixed subfolders appear as categories

## 🧩 Action Scripts (Root Level)

Scripts exposed to 3DCoat. Naming: `<Context>_<Action>_<Config>_<Scope>.py`

### Brush/Dynamic Subdiv
- `Brush_IncrementDetailsLevel.py` - Increment dynamic subdiv detail level
- `Brush_DecrementDetailsLevel.py` - Decrement dynamic subdiv detail level
- `Brush_ApplyDynamicSubdivSettings.py` - Apply settings to all brushes

### Autopo
- `Autopo_Run.py` - Run autopo with cached settings
- `Autopo_ToSculpt.py` - Run autopo and import to sculpt
- `Autopo_ToMultires.py` - Run autopo and import as multiresolution

### SculptObject Operations
- `SculptObject_Decimate_Half_Selected.py` - Decimate selected 50%
- `SculptObject_Decimate_Half_Subtree.py` - Decimate subtree 50%
- `SculptObject_Decimate_16x_Toggle.py` - Toggle 16x decimate proxy
- `SculptObject_Scale_Down100x_Selected.py` - Scale down 100x
- `SculptObject_Scale_Up100x_Selected.py` - Scale up 100x
- `SculptObject_ToSurface_All.py` - Convert all to surface
- `SculptObject_ToVoxel_All.py` - Convert all to voxels
- `SculptObject_Ghost_Toggle_Subtree.py` - Toggle ghost on subtree
- `SculptObject_Ghost_Invert_All.py` - Invert all ghost states
- `SculptObject_Ghost_Isolate_Selected.py` - Ghost all except selected
- `SculptObject_Unghost_All.py` - Unghost all objects
- `SculptObject_Subdivide_Double_Subtree.py` - Subdivide subtree
- `SculptObject_Resample_Half_Subtree.py` - Resample subtree to half
- `SculptObject_Remesh_Half_Selected.py` - Remesh selected to half
- `SculptObject_VoxBool_Intersect.py` - Voxel boolean intersect
- `SculptObject_VoxBool_Subtract.py` - Voxel boolean subtract
- `SculptObject_VoxBool_Union.py` - Voxel boolean union

### Scene/Export
- `Scene_SetupTiling_BoxGrid.py` - Setup box grid tiling
- `Scene_SetupTiling_PlaneGrid.py` - Setup plane grid tiling
- `Export_ScaleSave_Meshes.py` - Scale and save meshes

## 🛠️ Utility Modules (`_utils/`)

### `scene_api.py` 🆕
**Primary interface for 3DCoat scene context and iteration.**
Wraps callback-based iterators into list-returning functions.

**Classes:**
- `SceneAPI` - Static methods for scene element collection
  - `get_sculpt_root()` → `coat.SceneElement | None`
  - `get_current_element()` → `coat.SceneElement | None`
  - `get_current_volume()` → `coat.Volume | None`
  - `get_selected_elements()` → `list[coat.SceneElement]`
  - `collect_subtree(root)` → `list[coat.SceneElement]`
  - `collect_all_sculpt_objects()` → `list[coat.SceneElement]`

- `SelectionAPI` - Static methods for selection state
  - `save_selection()` → `list[coat.SceneElement]`
  - `restore_selection(elements)` → `None`
  - `select_one(element)` → `None`
  - `select_add(element)` → `None`

**Pure functions:**
- `apply_to_elements(elements, operation)` → `int`
- `filter_elements(elements, predicate)` → `list`
- `filter_sculpt_objects(elements)` → `list`
- `deduplicate_elements(elements)` → `list`

### `scope_utils.py`
Scope enum and resolution for batch operations.

**Enum:**
- `Scope.CURRENT` - Selected object(s) only
- `Scope.TREE` - Selection + all children
- `Scope.OTHER` - Everything except selection subtree
- `Scope.ALL` - Entire sculpt tree

**Functions:**
- `resolve_scope(scope, selected?)` → `list[coat.SceneElement]`
- `apply_to_scope(scope, operation, preserve_selection?)` → `int`

### `visibility_utils.py` 🆕
Pure functions for visibility/ghost manipulation.
All functions receive elements as arguments - no context fetching.

- `set_visibility(elements, visible)` → `int`
- `hide_elements(elements)` → `int`
- `show_elements(elements)` → `int`
- `set_ghost(elements, ghosted)` → `int`
- `ghost_elements(elements)` → `int`
- `unghost_elements(elements)` → `int`
- `invert_visibility_on_elements(elements)` → `int`
- `invert_ghost_on_elements(elements)` → `int`
- `hide_except(all_elements, keep_visible)` → `int`
- `ghost_except(all_elements, keep_unghosted)` → `int`

### `layer_utils.py`
Layer management for standard 2-layer setup.

**Constants:**
- `LAYER_SCULPT: str` - "Sculpt" (Layer 0, depth only)
- `LAYER_COLOR: str` - "Color" (Layer 1, color only)

**Functions:**
- `ensure_standard_layers()` - Setup standard layers
- `activate_sculpt_layer()` - Activate Layer 0
- `activate_color_layer()` - Activate Layer 1
- `cleanup_after_destructive_op()` - Clean up after decimate etc.

### `coat_ui_utils.py`
UI command abstractions hiding magic strings.

**Constants (all typed `str`):**
- `CMD_DIALOG_OK`, `CMD_DIALOG_CANCEL`
- `ROOM_SCULPT`, `ROOM_RETOPO`, `ROOM_PAINT`, etc.
- `CMD_DECIMATE_TO_RETOPO`, `CMD_AUTOPO`, etc.
- `DEFAULT_WAIT_FRAMES: int`, `DEFAULT_MESSAGE_DURATION_MS: int`

**Functions:**
- `confirm_dialog()` - Click OK on current dialog
- `cancel_dialog()` - Click Cancel on current dialog
- `command_with_confirm(cmd)` - Execute and auto-confirm
- `switch_to_room(room, wait_frames?)` - Switch room with wait
- `ensure_sculpt_room()`, `ensure_retopo_room()`, `ensure_paint_room()`
- `show_message(text, duration_ms?)`, `show_error(text, duration_ms?)`
- `wait_frames(n)` - Wait for async operations

### `object_utils.py`
Object validation and manipulation.

**Class `ObjectUtils`:**
- `get_current_sculpt_object()` → `coat.SceneElement | None`
- `get_volume_from_element(element)` → `coat.Volume | None`
- `validate_volume_has_polygons(vol)` → `bool`
- `get_current_sculpt_volume()` → `tuple | None`
- `ensure_surface_mode(vol)` - Convert from voxels if needed
- `print_polycount_info(name, before, after)`
- `show_polycount_message(operation, polycount)`

**Pure functions:**
- `scale_element(element, scale_factor)` - Scale without selection
- `scale_element_with_select(element, scale_factor)` - Select and scale
- `scale_elements(elements, scale_factor)` → `int`

### `lks_settings.py`
Persistent settings cache with singleton pattern.
- `get_settings()` - Get singleton settings instance
- `save_settings()` - Persist to JSON file

### `mesh_utils.py` 🆕
**Primary module for mesh modification operations (resample, decimate, voxelize, subdivide).**
Uses dataclass + configurator pattern.

**Dataclasses:**
- `ResampleParams(target_polycount, scale)` - Resample parameters
- `DecimateParams(target_polycount?, reduction_percent?)` - Decimate parameters
- `VoxelizeParams(suggested_polycount)` - Voxelize parameters

**Configurators:**
- `configure_resample_dialog(params)` → `Callable`
- `configure_decimate_dialog(params)` → `Callable`
- `configure_voxelize_dialog(params)` → `Callable`

**Execute Functions:**
- `execute_resample(params)` - Run resample with params
- `execute_decimate(params)` - Run decimate with params
- `execute_voxelize(params)` - Run voxelize with params

**Convenience Functions:**
- `resample_to_half(current_polycount)`
- `resample_to_target(initial, target)`
- `decimate_by_percent(percent)`
- `decimate_to_target(polycount)`
- `decimate_to_half()`
- `decimate_16x()` - Quick 1/16 proxy
- `subdivide_once()` - Double polycount

**Conversion Functions:**
- `convert_to_surface(volume)` - Voxels → surface
- `convert_to_voxels(volume, polycount?)` - Surface → voxels
- `ensure_surface_mode(volume)` - Ensure surface mode
- `voxelize_to_polycount(target)`

**Cleanup:**
- `cleanup_after_mesh_operation()` - Remove empty layers, reset active layer

### `SceneElement_boolean_utils.py` 🆕
**Live boolean operations on SceneElements (voxel mode required).**

**Enum:**
- `BooleanMode` - NONE=0, SUBTRACT=1, INTERSECT=2, UNION=3

**Core Function:**
- `create_boolean_child(parent, mode, name?, apply_extrusion?, extrusion_amount?)` → `coat.SceneElement`

**Convenience Functions:**
- `create_subtract_child(parent)` → `coat.SceneElement`
- `create_intersect_child(parent)` → `coat.SceneElement`
- `create_union_child(parent)` → `coat.SceneElement`

### `Scene_tiling_utils.py` 🆕
**Tiling grid setup with instances and translational symmetry.**

**Enum:**
- `PrimitiveType` - PLANE, BOX

**Dataclass:**
- `TilingParams(base_size, thickness, border_ratio, primitive_type)`

**Instance Functions:**
- `duplicate_as_instance(source, location)` → `coat.SceneElement`
- `create_grid_instance_locations(base_size)` → `list[vec3]`

**Symmetry Functions:**
- `disable_symmetry()` - Disable symmetry mode
- `setup_translation_symmetry(step_x, step_z)` - Configure translation symmetry

**Primitive Functions:**
- `create_plane_mesh(size, divisions)` → `Mesh`
- `create_box_mesh(size, thickness)` → `Mesh`

**Main Function:**
- `setup_tiling_grid(params)` → `coat.SceneElement` - Full tiling setup

### `brush_settings_utils.py` 🔄
Brush configuration with dataclass pattern.

**Dataclass:**
- `BrushDynamicSubdivParams(auto_subdivide, details_level, remove_stretching)`

**Apply Functions:**
- `apply_brush_settings(params)` - Apply to all brush types
- `apply_auto_subdivide_all(enabled)` - Set auto subdivide on all
- `apply_details_level_all(level)` - Set details level on all
- `apply_remove_stretching_all(enabled)` - Set remove stretching on all
- `apply_auto_subdivide(brush_type, enabled)` - Set for single brush
- `apply_details_level(brush_type, level)` - Set for single brush
- `apply_remove_stretching(brush_type, enabled)` - Set for single brush

### `autopo_utils.py` 🔄
Autopo workflow with dataclass/configurator pattern.

**Dataclass:**
- `AutopoParams(target_polycount, capture_details, auto_density, ...)` - All autopo settings

**Configure/Execute:**
- `configure_autopo(params)` - Set all UI values without executing
- `execute_autopo(params)` → `bool` - Run autopo with params

**Import Functions:**
- `import_retopo_to_sculpt()` → `bool` - Import retopo mesh
- `import_as_multiresolution()` → `bool` - Import as multires
- `clear_retopo_mesh()` - Clear retopo data

**High-Level Workflows:**
- `autopo_to_sculpt(params?)` → `bool` - Full workflow: autopo + import + ghost
- `autopo_to_multiresolution(params?)` → `bool` - Autopo + multires import

### `scene_iteration_utils.py` (Legacy)
**Prefer `scene_api.py` for new code.**
- `SceneIterationUtils` - Static methods for iteration

## 🖼️ Panels

### `LKS_Tools_Panel.py`
Main comprehensive tools panel containing:
- **Dynamic Subdiv section:** auto_subdivide, details_level, remove_stretching
- **Object Operations section:** scale 100x up/down, convert to surface/voxel
- **Visibility section:** ghost toggle, unghost all, isolate, invert ghost
- **Decimate section:** reduction percent slider, decimate current/tree
- **Autopo section:** density, run autopo, import to sculpt/multires
- **Settings:** save/load persistent settings

## 📄 Documentation

### Instruction Files (Always Loaded)
- `.github/instructions/copilot_style_guide.instructions.md` - Style conventions
- `.github/instructions/copilot_3dcoat.instructions.md` - 3DCoat patterns
- `.github/instructions/copilot_3dcoat_api.instructions.md` - API gotchas (slim)
- `.github/instructions/copilot_codebase_router.instructions.md` - This file

### Reference Docs (`_docs/` - Load on Demand)
- `_docs/magic_ui_strings.md` - **Comprehensive registry of all magic UI strings**
- `_docs/session_recovery.md` - Recovery doc for rebuilding lost work

---

## ⚠️ Keeping This Router Updated

Update this file whenever you:
- Add a new action script to root
- Create a new utility module in `_utils/`
- Add new settings to `lks_settings.py`
- Add new functions to utility modules
- Create or modify panels
