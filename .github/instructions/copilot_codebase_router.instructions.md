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
│   ├── __init__.py
│   ├── lks_settings.py        # Persistent settings singleton
│   ├── coat_ui_utils.py       # UI command abstractions
│   ├── brush_settings_utils.py # Brush configuration
│   ├── autopo_utils.py        # Autopo workflow automation
│   ├── object_utils.py        # Object manipulation
│   └── scene_iteration_utils.py # Scene tree traversal
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

### `lks_settings.py`
Persistent settings cache with singleton pattern.
- `get_settings()` - Get singleton settings instance
- `save_settings()` - Persist to JSON file
- `LKSSettings` class with attribute access

**Current settings:**
- `details_level: int` - Dynamic subdiv detail level
- `auto_subdivide: bool` - Enable auto subdivision
- `remove_stretching: bool` - Enable remove stretching
- `autopo_density: int` - Target poly count for autopo
- `autopo_optimize_mesh: bool` - Mesh optimization toggle
- `autopo_keep_creases: bool` - Keep hard edges toggle
- `autopo_add_to_scene: bool` - Add retopo to scene

### `coat_ui_utils.py`
UI command abstractions hiding magic strings.
- `confirm_dialog()` - Click OK on current dialog
- `cancel_dialog()` - Click Cancel on current dialog
- `switch_to_room(room, wait=4)` - Switch room with wait
- `show_message(text, duration_ms)` - Show toast message

### `brush_settings_utils.py`
Brush configuration for all brush types.
- `BrushSettingsUtils.apply_global_brush_settings(auto_sub, detail, stretch)`
- `set_auto_subdivide_all(enabled)` - Set auto subdivide on all brushes
- `set_details_level_all(level)` - Set detail level on all brushes
- `set_remove_stretching_all(enabled)` - Set remove stretching globally

### `autopo_utils.py`
Autopo workflow automation.
- `run_autopo_with_settings()` - Run autopo using cached settings
- `autopo_to_sculpt()` - Autopo + import to sculpt, hide original
- `autopo_to_multiresolution()` - Autopo + import as multires

### `object_utils.py`
Object manipulation utilities.
- _(document as created)_

### `scene_iteration_utils.py`
Scene tree traversal utilities.
- _(document as created)_

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
