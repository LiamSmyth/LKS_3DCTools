---
applyTo: '**'
---

# LKS 3DCoat cModule - Codebase Router

A ledger of existing code, utilities, and resources. This file provides quick links to what currently exists in the repository.

## 🚦 Start Here

- `copilot_style_guide.instructions.md`: Python scripting conventions for this workspace
- `copilot_3dcoat.instructions.md`: 3DCoat-specific patterns, cModule development, Qt UI
- `copilot_3dcoat_api.instructions.md`: 3DCoat API gotchas and quirks

## 🖥️ Environment

- **Windows + PowerShell** - Chain commands with `;`, normalize paths with `Resolve-Path`
- **cModule format** - Located at `StdScripts/cModules/LKS/` for working cExtension hooks
- **Dependencies via requirements.txt** - Auto-installed by 3DCoat (PySide6, etc.)
- **3DCoat embedded Python** - The `coat` module is provided at runtime

## 🗺️ Folder Structure

```
LKS/                           # cModule root (in StdScripts/cModules/)
├── __init__.py               # Package marker
├── __onstartup.py            # Runs on 3DCoat startup (Qt init + action registration)
├── requirements.txt          # PySide6, etc. (auto-installed)
├── LKS.py                    # Main extension (cExtension + Qt panel)
├── coat.pyi                  # Type hints for IDE
├── actions/                  # Action scripts for menu registration
│   ├── Autopo_*.py           # Autopo workflow actions
│   ├── Brush_*.py            # Brush setting actions
│   ├── SculptObject_*.py     # Sculpt object actions
│   └── ...
├── ops/                      # Operators (workflow orchestration)
│   ├── __init__.py
│   ├── SculptObject_Decimate.py    # Decimate with scope/config
│   ├── SculptObject_SetGhost.py    # Ghost/unghost/invert/isolate
│   ├── SculptObject_IdColors.py    # Fill with ID colors
│   ├── SculptObject_Scale.py       # Scale elements
│   ├── SculptObject_Resample.py    # Resample operations
│   ├── SculptObject_ModeConvert.py # Mode conversion
│   ├── SculptObject_Subdivide.py   # Subdivide operations
│   └── ...
├── utils/                    # Low-level utilities
│   ├── __init__.py           # Package exports
│   ├── action_discovery.py   # 🆕 Pure Python action script discovery
│   ├── coat_menu_utils.py    # 🆕 3DCoat menu registration wrapper
│   ├── scene_api.py          # Thin wrappers for coat iterators
│   ├── scope_utils.py        # Scope enum and resolution
│   ├── SceneElement_visibility_utils.py  # Pure visibility/ghost functions
│   ├── Scene_layer_utils.py  # Layer management
│   ├── coat_ui_utils.py      # UI command abstractions
│   ├── object_utils.py       # Object manipulation
│   ├── Volume_decimate_utils.py  # Decimate operations (raw args)
│   ├── Volume_resample_utils.py  # Resample operations (raw args)
│   ├── Volume_subdivide_utils.py # Subdivide/symmetry (raw args)
│   ├── Volume_mode_utils.py  # Mode conversion (raw args)
│   ├── Volume_density_utils.py   # Density matching (raw args)
│   ├── Scene_cleanup_utils.py    # Cleanup after mesh ops
│   ├── SceneElement_boolean_utils.py # Live boolean operations
│   ├── Scene_tiling_utils.py # Tiling grid setup
│   ├── lks_settings.py       # Persistent settings singleton
│   ├── brush_settings_utils.py # Brush configuration
│   ├── autopo_utils.py       # Autopo workflow automation
│   └── scene_iteration_utils.py # Legacy - prefer scene_api.py
├── ui/                       # Qt UI components
│   ├── __init__.py           # Exports DARK_STYLESHEET
│   ├── styles.py             # Qt stylesheets and color constants
│   └── widgets.py            # Reusable Qt widgets (CollapsibleSection, ButtonGrid, ActivityLog)
├── data/                     # Runtime state and settings
│   ├── lks_settings.json     # General settings
│   ├── lks_brush_settings.json # Brush settings
│   ├── lks_autopo_settings.json # Autopo settings
│   └── lks_panel_state.json  # Panel state
├── .docs/                    # Documentation (hidden from 3DCoat)
│   ├── cmodule_migration_plan.md  # Migration from Addon to cModule
│   └── magic_ui_strings.md   # Registry of 3DCoat magic strings
├── .example_code/            # Reference implementations (hidden)
└── .github/instructions/     # Copilot instruction files
```

## 🔌 cModule Entry Points

### `LKS.py` - Main Extension
- Defines `LKSExtension(cPy.cCore.cExtension)` with per-frame hooks
- Contains `LKSPanel` Qt widget for non-blocking UI
- Auto-registers extension on import, shows panel when run

### `__onstartup.py` - Startup Initialization
- Configures Qt/PySide6 for 3DCoat compatibility
- Creates QApplication with OpenGL workarounds

### `requirements.txt` - Dependencies
- Lists pip packages auto-installed by 3DCoat
- Currently: `PySide6`

## 🎯 Operators (`ops/`)

Operators are configurable scripts that encapsulate reusable workflows.
Both action scripts and panel buttons call operators, ensuring consistent behavior.

**Pattern:** Each operator has a `main()` function with explicit parameters:
```python
# ops/SculptObject_SetGhost.py
def main(scope: Scope, ghost: bool = True, mode: GhostMode = GhostMode.SET) -> int:
    ...
```

**Usage from action script:**
```python
from ops.SculptObject_SetGhost import main as op_main
from utils.scope_utils import Scope
op_main(scope=Scope.ALL, ghost=False)
```

### Available Operators

#### `SculptObject_Decimate.py`
Decimate sculpt objects by percentage or to target polycount.

**Parameters:**
- `scope: Scope` - Which objects (CURRENT, TREE, ALL)
- `reduction_percent: float | None` - Percentage to reduce (e.g., 50.0)
- `target_polycount: int | None` - Absolute target (overrides percent)
- `use_16x: bool` - Quick 16x proxy mode
- `preserve_selection: bool` - Restore selection after

**Used by:** DecCurrent, DecTree, DecAll, Dec50, Dec80 (panel), SculptObject_Decimate_*.py (actions)

#### `SculptObject_SetGhost.py`
Ghost/unghost operations with modes for set, invert, and isolate.

**Parameters:**
- `scope: Scope` - Which objects (CURRENT, TREE, OTHER, ALL)
- `ghost: bool` - True = ghost, False = unghost (for SET mode)
- `mode: GhostMode` - SET, INVERT, or ISOLATE
- `preserve_selection: bool` - Restore selection after

**Used by:** GhostCur/Tree/All, UnghostCur/Tree/All, InvertGhost (panel), SculptObject_Ghost_*.py (actions)

#### `SculptObject_IdColors.py`
Fill objects with random ID colors for texture baking.

**Parameters:**
- `scope: Scope` - Which objects (TREE, ALL)
- `layer_name: str` - Layer to use/create (default: "IDMap")
- `min_color: int` - Minimum RGB value to avoid pure black
- `restore_layer: bool` - Restore Layer 0 after

**Used by:** IdColorsTree (panel), SculptObject_IdColors_FromParts.py (action)

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
- `SculptObject_Decimate_TargetDensity_All.py` - Decimate all to target density
- `SculptObject_Scale_Down100x_Selected.py` - Scale down 100x
- `SculptObject_Scale_Up100x_Selected.py` - Scale up 100x
- `SculptObject_ToSurface_All.py` - Convert all to surface
- `SculptObject_ToVoxel_All.py` - Convert all to voxels
- `SculptObject_ToVoxel_2x.py` - Convert to voxels with 2x polycount
- `SculptObject_ToVoxel_4x.py` - Convert to voxels with 4x polycount
- `SculptObject_ToVoxel_8x.py` - Convert to voxels with 8x polycount
- `SculptObject_ToggleMeshVox_Selected.py` - Toggle mesh/voxel preserving polycount
- `SculptObject_Ghost_Toggle_Subtree.py` - Toggle ghost on subtree
- `SculptObject_Ghost_Invert_All.py` - Invert all ghost states
- `SculptObject_Ghost_Isolate_Selected.py` - Ghost all except selected
- `SculptObject_Unghost_All.py` - Unghost all objects
- `SculptObject_Visibility_Toggle_Subtree.py` - Toggle visibility on subtree
- `SculptObject_Subdivide_Double_Subtree.py` - Subdivide subtree (2x polys)
- `SculptObject_Resample_Half_Subtree.py` - Resample subtree to half
- `SculptObject_Remesh_Half_Selected.py` - Remesh selected to half
- `SculptObject_RemeshResymm_Safe_Selected.py` - Remesh + symmetrize selected
- `SculptObject_RemeshResymm_Safe_Subtree.py` - Remesh + symmetrize subtree
- `SculptObject_Remesh_PreserveParts_Selected.py` - Remesh preserving parts
- `SculptObject_Merge_PreserveParts_Subtree.py` - Merge subtree preserving parts
- `SculptObject_Split_Masked_Selected.py` - Split frozen/masked area
- `SculptObject_IdColors_FromParts.py` - Fill subtree with random ID colors
- `SculptObject_UniformDensity_Resample_Subtree.py` - Resample to uniform density
- `SculptObject_UniformDensity_Smart_Subtree.py` - Smart density matching
- `SculptObject_VoxBool_Intersect.py` - Voxel boolean intersect
- `SculptObject_VoxBool_Subtract.py` - Voxel boolean subtract
- `SculptObject_VoxBool_Union.py` - Voxel boolean union
- `SculptObject_Instance_Tile_Selected.py` - Create tiled instances

### Scene/Export
- `Scene_SetupTiling_BoxGrid.py` - Setup box grid tiling
- `Scene_SetupTiling_PlaneGrid.py` - Setup plane grid tiling
- `Export_ScaleSave_Meshes.py` - Scale and save meshes

### External Panel
- `LKS_ExternalPanel_Launch.py` - Launch external panel and register extension
- `LKS_ExternalPanel_Stop.py` - Stop external panel and unregister extension

### Registration & Lifecycle
- `LKS_Register.py` - Register the addon (extension + actions + show panel)
- `LKS_Unregister.py` - Unregister the addon (close panel + remove actions)
- `LKS_FullReload.py` - Full reload for development (reload modules + re-register)

## 🛠️ Utility Modules (`utils/`)

> **Architecture Note:** Utils take RAW PRIMITIVE ARGUMENTS only (no dataclasses).
> Dataclasses for configuration belong in operators (`_ops/`).
> See `copilot_style_guide.instructions.md` Section 5 for details.

> **Naming Convention:** Prefix indicates 3DCoat dependency:
> - `coat_` prefix: Direct 3DCoat API wrappers (imports `coat`)
> - `<CoatType>_` prefix: Operations on 3DCoat types (`Volume_`, `Scene_`, `SceneElement_`)
> - No prefix: Pure Python, testable outside 3DCoat

### `action_discovery.py` 🆕
**Pure Python module for scanning and categorizing action scripts. NO coat dependency.**

**Dataclasses:**
- `ActionInfo` - Information about a discovered action (filename, path, context, action_name, display_name, menu_id)
- `ActionCategory` - Group of actions by context (context, display_name, actions list)

**Functions:**
- `parse_action_filename(filename)` → `tuple[str, str] | None` - Parse "Context_Action.py" into (context, action_name)
- `generate_display_name(context, action_name)` → `str` - Human-readable name like "LKS: Decimate Half Selected"
- `generate_menu_id(context, action_name)` → `str` - Unique ID like "LKS_SculptObject_Decimate_Half_Selected"
- `discover_actions(actions_dir)` → `list[ActionInfo]` - Discover all valid action scripts
- `group_actions_by_context(actions)` → `list[ActionCategory]` - Group for submenu organization
- `iter_actions(actions_dir)` → `Iterator[ActionInfo]` - Generator version

**Constants:**
- `KNOWN_CONTEXTS` - Set of known context prefixes (SculptObject, Brush, Scene, etc.)
- `EXCLUDED_SCRIPTS` - Set of scripts to exclude from auto-registration (panels, lifecycle)

### `coat_menu_utils.py` 🆕
**3DCoat menu registration utilities. Depends on `coat` module.**

**Path Functions:**
- `get_lks_root()` → `Path` - Get LKS cModule root directory
- `get_actions_dir()` → `Path` - Get actions folder path
- `resolve_script_path(script_path)` → `str` - Resolve path to 3DCoat format (forward slashes)

**Registration Functions:**
- `register_action(menu_id, display_name, script_path, menu_name)` → `bool` - Register single action
- `register_actions_from_discovery(actions, menu_name)` → `tuple[int, int]` - Register multiple, returns (registered, skipped)
- `unregister_all_lks_actions()` → `int` - Informational (no unregister API in 3DCoat)

**Debugging:**
- `log_registration_status()` - Log registration status to 3DCoat console

**Initialization:**
- `initialize_lks_menu()` → `tuple[int, int]` - Discover and register all actions (call from `__onstartup.py`)

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

**Instance Detection (Experimental):**
- `get_volume_tree_id(element)` → `int | None` - Get underlying VoxTreeBranch pointer ID
- `deduplicate_instances(elements)` → `list` - Remove elements that are instances of already-seen geometry
- `partition_instances(elements)` → `tuple[list, list]` - Split into (unique, instance_duplicates)

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

### `SceneElement_visibility_utils.py`
Pure functions for visibility/ghost manipulation on SceneElements.
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

### `Scene_layer_utils.py`
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
- `validate_and_ensure_surface_mode()` → `bool` - Validate current object and ensure surface mode
- `scale_element(element, scale_factor)` - Scale without selection
- `scale_element_with_select(element, scale_factor)` - Select and scale
- `scale_elements(elements, scale_factor)` → `int`

### `lks_settings.py`
Persistent settings cache with separate singletons for brush, autopo, and general settings.

**Files:**
- `lks_brush_settings.json` - Brush settings (details_level, auto_subdivide, etc.)
- `lks_autopo_settings.json` - Autopo workflow configuration
- `lks_settings.json` - General settings (decimate, etc.)

**Brush Settings Functions:**
- `get_brush_settings()` - Get brush settings singleton
- `save_brush_settings()` - Persist brush settings to disk
- `reload_brush_settings()` - Force reload from disk

**Autopo Settings Functions:**
- `get_autopo_settings()` - Get autopo settings singleton
- `save_autopo_settings()` - Persist autopo settings to disk
- `reload_autopo_settings()` - Force reload from disk

**General Settings Functions:**
- `get_settings()` - Get general settings singleton
- `save_settings()` - Persist general settings to disk
- `reload_settings()` - Force reload from disk
- `reset_settings()` - Reset to defaults

### `Volume_decimate_utils.py`
**Decimate operations on Volumes. Raw primitive args only.**

- `configure_decimate_dialog(reduction_percent?, target_polycount?)` → `Callable`
- `execute_decimate(reduction_percent?, target_polycount?)` - Decimate current object
- `decimate_by_percent(percent)` - Quick percent-based decimate
- `decimate_to_target(polycount)` - Decimate to specific polycount
- `decimate_to_half()` - 50% reduction
- `decimate_16x()` - Quick 1/16 proxy

### `Volume_resample_utils.py`
**Resample operations on Volumes. Raw primitive args only.**

- `configure_resample_dialog(target_polycount, scale?)` → `Callable`
- `execute_resample(target_polycount, scale?)` - Resample current object
- `resample_to_half(current_polycount)` - 50% resample
- `resample_to_target(initial, target)` - Resample to target

### `Volume_subdivide_utils.py`
**Subdivide and symmetry operations on Volumes. Raw primitive args only.**

- `subdivide_once()` - Double polycount
- `make_symmetrical()` - Make object symmetrical

### `Volume_mode_utils.py`
**Mode conversion on Volumes. Raw primitive args only.**

- `convert_to_surface(volume)` - Voxels → surface
- `convert_to_voxels(volume, polycount?)` - Surface → voxels
- `ensure_surface_mode(volume)` - Ensure surface mode
- `resample_and_voxelize(volume, target_polycount)` - Resample then voxelize

### `Volume_density_utils.py`
**Uniform density operations. Raw primitive args only.**

- `calculate_target_polycount_by_scale(ref_vol, target_vol)` → `int`
- `resample_to_match_density(element, ref_vol)` - Match reference density
- `smart_match_density(element, ref_vol, tolerance?)` - Smart density matching

### `Scene_cleanup_utils.py`
**Scene cleanup after mesh operations.**

- `cleanup_after_mesh_operation()` - Remove empty layers, reset active layer

### `SceneElement_boolean_utils.py`
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

### `registration_utils.py`
Addon lifecycle management - registration, unregistration, and module reloading.

**Constants:**
- `ACTION_DEFINITIONS: list[tuple]` - List of (script_path, menu_location, id) tuples
- `LKS_MODULES: list[str]` - List of module paths for reloading

**Functions:**
- `register_actions()` - Register all action scripts with 3DCoat menus
- `unregister_actions()` - Remove all registered actions
- `register_addon(show_panel?)` - Full registration (extension + actions + optionally show panel)
- `unregister_addon()` - Full cleanup (close panel + remove actions)
- `reload_modules(modules?)` → `tuple[int, int]` - Reload modules, returns (success, failed) counts
- `full_reload()` - Complete development reload (unregister + reload modules + re-register)

**Used by:** `actions/LKS_Register.py`, `actions/LKS_Unregister.py`, `actions/LKS_FullReload.py`

## 🎨 UI Components (`ui/`)

Reusable PySide6 widget primitives for the LKS panel.

### `styles.py`
Qt stylesheets and color constants for dark theme.

**Constants:**
- `DARK_STYLESHEET: str` - Complete dark theme stylesheet for Qt widgets
- `DARK_BG: str`, `DARK_SURFACE: str`, `DARK_BORDER: str` - Color constants

### `widgets.py`
Reusable Qt widgets for the LKS panel.

**Widgets:**
- `CollapsibleSection(title, color?, collapsed?)` - Expandable/collapsible section with arrow toggle
  - `toggle_section()` - Expand/collapse the section
  - `set_collapsed(collapsed)` - Set collapsed state
  - `content_layout: QVBoxLayout` - Layout for adding content widgets
  - Signals: `toggled(bool)` - Emitted when section is toggled

- `ButtonGrid(columns)` - Grid layout for buttons with uniform sizing
  - `add_button(text, callback, tooltip?)` - Add a button to the grid
  - Auto-wraps buttons to new rows based on column count

- `ActivityLog(max_lines?)` - Scrollable activity log with colored messages
  - `log_info(text)` - Log info message (gray)
  - `log_warn(text)` - Log warning (yellow)
  - `log_error(text)` - Log error (red)
  - `log_success(text)` - Log success (green)
  - `log_debug(text)` - Log debug (dim gray)
  - `clear()` - Clear all messages
  - HTML-based with auto-scrolling

- `SectionHeader(text, color?)` - Styled section header label
- `LabeledSlider(label, min, max, value)` - Slider with label and value display
- `add_tooltip(widget, text)` - Add tooltip to any widget

**Usage:**
```python
from ui.styles import DARK_STYLESHEET
from ui.widgets import CollapsibleSection, ButtonGrid, ActivityLog

self.setStyleSheet(DARK_STYLESHEET)

section = CollapsibleSection("Decimate", color="#ffb74d")
grid = ButtonGrid(columns=3)
grid.add_button("Cur", self._on_cur, "Decimate current")
grid.add_button("Tree", self._on_tree, "Decimate subtree")
section.content_layout.addWidget(grid)

self._log = ActivityLog()
self._log.log_success("Operation completed")
```

## 🖼️ Panels

### `LKS_Tools_Panel.py`
Comprehensive tools panel with all functionality.

**Auto-save:** Panel uses `process()` callback to detect field changes and auto-save
to the appropriate JSON files (brush, autopo, general).

**Dynamic Subdiv section:**
- `auto_subdivide`, `details_level`, `remove_stretching` controls
- Apply to brushes, increment/decrement level buttons (fixed: always enables auto_subdivide)
- Auto-saves to `lks_brush_settings.json`

**Mesh Operations section (with headers):**
- **Decimate:** percent slider, Current/Tree/All buttons, 50%/80% quick buttons
- **Resample:** Half (Cur/Tree/All), Double, Subdivide
- **Mode Conversion:** To Surface/To Voxels (Cur/Tree/All)

**Scale section:**
- Scale Down 100x (Cur/Tree/All)
- Scale Up 100x (Cur/Tree/All)

**Visibility section (with headers):**
- **Hide:** Hide/Show (Cur/Tree/Other/All), Invert Hide
- **Ghost:** Ghost/Unghost (Cur/Tree/Other/All), Invert Ghost

**Smart Actions section (with headers):**
- **Uniform Density:** UniformResample, UniformSmart (subtree density matching)
- **Remesh + Symmetry:** RemeshResymmCur, RemeshResymmTree
- **Other:** IdColorsTree, SplitMasked, MergePreserve

**Autopo section (ALL parameters exposed):**
- `autopo_polycount`, `autopo_capture_details`, `autopo_auto_density`
- `autopo_decimation_limit`, `autopo_hardsurface`, `autopo_voxelize`
- `autopo_tangent_smooth`, `autopo_bypass_modal`
- Run Autopo, Autopo to Sculpt, Autopo to Multires
- Auto-saves to `lks_autopo_settings.json`

**Layers section:**
- Setup Layers button (creates Sculpt/Color layers)

**Settings:**
- Save Settings button (manually saves all settings)

**Dev Tools:**
- Reload Scripts button (reloads all _utils modules)

## 📄 Documentation

### Instruction Files (Always Loaded)
- `.github/instructions/copilot_style_guide.instructions.md` - Style conventions
- `.github/instructions/copilot_3dcoat.instructions.md` - 3DCoat patterns
- `.github/instructions/copilot_3dcoat_api.instructions.md` - API gotchas (slim)
- `.github/instructions/copilot_codebase_router.instructions.md` - This file

### Reference Docs (`_docs/` - Load on Demand)
- `_docs/magic_ui_strings.md` - **Comprehensive registry of all magic UI strings**
- `_docs/session_recovery.md` - Recovery doc for rebuilding lost work
- `_docs/external_panel_architecture.md` - **External panel IPC system architecture**

---

## 🔌 External Panel System (`_external/`)

The external panel is a standalone tkinter/ttkbootstrap app that communicates with 3DCoat via IPC files. It runs in a separate process to avoid blocking the viewport.

### Architecture

See `_docs/external_panel_architecture.md` for full details.

```
3DCoat Process          External Python Process
┌─────────────────┐     ┌─────────────────────┐
│ LKSExtension    │◄───►│ LKS Panel App       │
│ (cExtension)    │ IPC │ (tkinter)           │
└─────────────────┘     └─────────────────────┘
         │                       │
         └───────┬───────────────┘
                 ▼
          _ipc/ folder
          (JSON files)
```

### Entry Points

- `LKS_ExternalPanel_Launch.py` - Register extension and launch panel
- `LKS_ExternalPanel_Stop.py` - Shutdown panel and unregister extension

### IPC Protocol (`_utils/ipc_protocol.py`)

Shared data structures and atomic file operations for IPC communication.

**Dataclasses:**
- `IPCCommand` - Command from UI → 3DCoat (action, params, id, timestamp)
- `IPCResult` - Result from 3DCoat → UI (command_id, success, data, error)
- `SceneElement` - Simplified element info (name, visible, ghosted, polycount)
- `SceneState` - Scene snapshot (elements, current_room, selected_names)
- `Heartbeat` - Extension alive signal

**File Operations:**
- `atomic_write_json(path, data)` - Atomic write via temp+rename
- `safe_read_json(path, default)` - Safe read with fallback
- `send_command(command)` - Send command to 3DCoat
- `read_pending_commands()` - Read and clear pending commands
- `write_result(result)` - Write result from 3DCoat
- `read_scene_state()` - Read scene state snapshot
- `write_heartbeat()` - Write extension heartbeat
- `is_extension_alive(timeout)` - Check heartbeat recency
- `request_shutdown()` / `is_shutdown_requested()` - Shutdown coordination

### IPC Server (`_utils/ipc_server.py`)

Command dispatch and handlers running inside 3DCoat.

**Built-in Handlers:**
- `ping` - Connection test
- `list_elements` - List sculpt tree elements
- `get_scene_state` - Full scene snapshot
- `select_element` - Select by name
- `ghost_element` - Ghost/unghost by name
- `hide_element` - Hide/show by name
- `run_action` - Run action script by name
- `run_operator` - Run operator with params
- `ui_command` - Execute raw UI command
- `switch_room` - Switch to room
- `list_handlers` - List available handlers

**Adding Custom Handlers:**
```python
from utils.ipc_server import register_handler

@register_handler("my_custom_action")
def handle_my_action(params: dict) -> dict:
    # Do something
    return {"result": "success"}
```

### cExtension (`_utils/lks_extension.py`)

Extension running inside 3DCoat for per-frame IPC polling.

**Key Functions:**
- `register_extension()` - Create and register extension singleton
- `unregister_extension()` - Graceful shutdown
- `is_extension_registered()` - Check registration status
- `send_message(msg)` - Send message to extension

**Extension Hooks Used:**
- `preprocess()` - Poll commands, broadcast state, write heartbeat
- `onNew()`, `onChangeRoom()` - Broadcast state on scene changes

### External Panel App (`_external/`)

Standalone Python app launched via `coat.io.exec()`.

**Structure:**
```
_external/
├── lks_panel_app.py      # Entry point with dep checking
└── lks_panel/
    ├── __init__.py
    ├── app.py            # Main tkinter application
    ├── ipc_client.py     # High-level IPC client
    ├── widgets.py        # Reusable widgets
    └── tooltip.py        # Tooltip utility
```

**Self-Healing Dependencies:**
The entry point (`lks_panel_app.py`) checks for ttkbootstrap and offers to install it via pip if missing.

**IPC Client (`ipc_client.py`):**
- `IPCClient` class with convenient methods
- `is_connected()` - Check extension heartbeat
- `send_and_wait(action, params)` - Synchronous command
- `list_elements()`, `select_element()`, `ghost_element()` - Helpers
- `run_action(script)`, `run_operator(op, **args)` - Action execution

---

## ⚠️ Keeping This Router Updated

Update this file whenever you:
- Add a new action script to root
- Create a new utility module in `_utils/`
- Add new settings to `lks_settings.py`
- Add new functions to utility modules
- Create or modify panels
