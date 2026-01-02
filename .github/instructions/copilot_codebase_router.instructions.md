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
│   ├── scene_api.py           # 🆕 Thin wrappers for coat iterators
│   ├── scope_utils.py         # Scope enum and resolution
│   ├── visibility_utils.py    # 🆕 Pure visibility/ghost functions
│   ├── layer_utils.py         # Layer management
│   ├── coat_ui_utils.py       # UI command abstractions
│   ├── object_utils.py        # Object manipulation
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

Scripts exposed to 3DCoat. Naming: `<Context>_<Action>_<Variant>.py`

### Brush/Dynamic Subdiv
- `Brush_IncrementDetailsLevel.py` - Increment dynamic subdiv detail level by 1
- `Brush_DecrementDetailsLevel.py` - Decrement dynamic subdiv detail level by 1
- `Brush_ApplyDynamicSubdivSettings.py` - Apply cached subdiv settings to all brushes

### Autopo
- `Autopo_Run.py` - Run autopo with cached settings
- `Autopo_ToSculpt.py` - Run autopo and import result to sculpt
- `Autopo_ToMultires.py` - Run autopo and import as multiresolution

### Object Operations
- `SculptObject_Scale_Half.py` - Scale selected object to 50%
- `SculptObject_Scale_Double.py` - Scale selected object to 200%
- _(add more as created)_

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

### `brush_settings_utils.py`
Brush configuration for all brush types.
- `BrushSettingsUtils.apply_global_brush_settings(auto_sub, detail, stretch)`

### `autopo_utils.py`
Autopo workflow automation.
- `run_autopo_with_settings()` - Run autopo using cached settings
- `autopo_to_sculpt()` - Autopo + import to sculpt
- `autopo_to_multiresolution()` - Autopo + import as multires

### `scene_iteration_utils.py` (Legacy)
**Prefer `scene_api.py` for new code.**
- `SceneIterationUtils` - Static methods for iteration

## 🖼️ Panels

### `LKS_Tools_Panel.py`
Main comprehensive tools panel containing:
- Decimate section (reduction slider, actions)
- Object operations section (scale, etc.)
- Layer utilities section
- Dynamic Subdiv section (auto_subdivide, details_level, remove_stretching)
- Autopo section (density, options, run/import actions)

## 📄 Documentation

- `.github/instructions/copilot_style_guide.instructions.md` - Style conventions
- `.github/instructions/copilot_3dcoat.instructions.md` - 3DCoat patterns
- `.github/instructions/copilot_3dcoat_api.instructions.md` - API reference
- `.github/instructions/copilot_codebase_router.instructions.md` - This file
- `_docs/session_recovery.md` - Recovery doc for rebuilding lost work

---

## ⚠️ Keeping This Router Updated

Update this file whenever you:
- Add a new action script to root
- Create a new utility module in `_utils/`
- Add new settings to `lks_settings.py`
- Add new functions to utility modules
- Create or modify panels
