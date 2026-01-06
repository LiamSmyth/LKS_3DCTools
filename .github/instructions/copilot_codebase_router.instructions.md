---
applyTo: '**'
---

# LKS 3DCoat cModule - Codebase Router

Quick reference to all scripts in the workspace. Read individual files for implementation details.

## 🚦 Start Here

- `copilot_style_guide.instructions.md` - Python conventions for this workspace
- `copilot_3dcoat.instructions.md` - 3DCoat cModule patterns, Qt UI
- `copilot_3dcoat_api.instructions.md` - 3DCoat API gotchas and quirks

## 🖥️ Environment

- **Windows + PowerShell** - Chain commands with `;`
- **cModule format** - Located at `StdScripts/cModules/LKS/`
- **Dependencies** - `requirements.txt` (PySide6), auto-installed by 3DCoat
- **3DCoat embedded Python** - `coat` module provided at runtime

## 🗺️ Folder Structure

```
LKS/
├── __init__.py, __onstartup.py, requirements.txt
├── LKS.py                    # Main extension + Qt panel
├── coat.pyi                  # Type hints for IDE
├── actions/                  # Action scripts (menu-exposed)
├── ops/                      # Operators (workflow orchestration)
├── utils/                    # Low-level utilities
├── ui/                       # Qt UI components
├── data/                     # Settings JSON files
├── _docs/                    # Documentation (hidden)
└── .github/instructions/     # Copilot instructions
```

---

## 🔌 Entry Points

| File | Description |
|------|-------------|
| `LKS.py` | Main cExtension with per-frame hooks + LKSPanel Qt widget |
| `__onstartup.py` | Qt/PySide6 initialization on 3DCoat startup |
| `requirements.txt` | Pip packages (PySide6) auto-installed by 3DCoat |

---

## 🎯 Operators (`ops/`)

Reusable workflows called by action scripts and panel buttons. Each has `main()` with typed params.

| File | Description |
|------|-------------|
| `SculptObject_Decimate.py` | Decimate by percent or target polycount with scope |
| `SculptObject_SetGhost.py` | Ghost/unghost/invert/isolate with scope and mode |
| `SculptObject_IdColors.py` | Fill objects with random ID colors for baking |
| `SculptObject_Scale.py` | Scale elements by factor |
| `SculptObject_Resample.py` | Resample to half or target polycount |
| `SculptObject_ModeConvert.py` | Convert between surface and voxel modes |
| `SculptObject_Subdivide.py` | Subdivide (double polys) and symmetry ops |

---

## 🧩 Action Scripts (`actions/`)

Thin invokers exposed to 3DCoat menus. Naming: `<Context>_<Action>_<Config>_<Scope>.py`

### Brush
| File | Description |
|------|-------------|
| `Brush_IncrementDetailsLevel.py` | Increment dynamic subdiv detail level |
| `Brush_DecrementDetailsLevel.py` | Decrement dynamic subdiv detail level |
| `Brush_ApplyDynamicSubdivSettings.py` | Apply cached settings to all brushes |

### Autopo
| File | Description |
|------|-------------|
| `Autopo_Run.py` | Run autopo with cached settings |
| `Autopo_ToSculpt.py` | Autopo + import to sculpt room |
| `Autopo_ToMultires.py` | Autopo + import as multiresolution |

### SculptObject - Decimate
| File | Description |
|------|-------------|
| `SculptObject_Decimate_Half_Selected.py` | Decimate selected 50% |
| `SculptObject_Decimate_Half_Subtree.py` | Decimate subtree 50% |
| `SculptObject_Decimate_16x_Toggle.py` | Toggle 16x decimate proxy |
| `SculptObject_Decimate_TargetDensity_All.py` | Decimate all to uniform density |

### SculptObject - Scale
| File | Description |
|------|-------------|
| `SculptObject_Scale_Down100x_Selected.py` | Scale down 100x |
| `SculptObject_Scale_Up100x_Selected.py` | Scale up 100x |

### SculptObject - Mode Conversion
| File | Description |
|------|-------------|
| `SculptObject_ToSurface_All.py` | Convert all to surface mode |
| `SculptObject_ToVoxel_All.py` | Convert all to voxels |
| `SculptObject_ToVoxel_2x.py` / `4x` / `8x` | Convert to voxels with multiplied polycount |
| `SculptObject_ToggleMeshVox_Selected.py` | Toggle mesh/voxel preserving polycount |

### SculptObject - Ghost/Visibility
| File | Description |
|------|-------------|
| `SculptObject_Ghost_Toggle_Subtree.py` | Toggle ghost on subtree |
| `SculptObject_Ghost_Invert_All.py` | Invert all ghost states |
| `SculptObject_Ghost_Isolate_Selected.py` | Ghost all except selected |
| `SculptObject_Ghost_ToggleIsolate_Selected.py` | Toggle ghost isolation |
| `SculptObject_Unghost_All.py` | Unghost all objects |
| `SculptObject_Visibility_Toggle_Subtree.py` | Toggle visibility on subtree |
| `SculptObject_Visibility_ToggleIsolate_Selected.py` | Toggle visibility isolation |

### SculptObject - Mesh Operations
| File | Description |
|------|-------------|
| `SculptObject_Subdivide_Double_Subtree.py` | Subdivide subtree (2x polys) |
| `SculptObject_Resample_Half_Subtree.py` | Resample subtree to half |
| `SculptObject_Remesh_Half_Selected.py` | Remesh selected to half |
| `SculptObject_RemeshResymm_Safe_Selected.py` | Remesh + symmetrize selected |
| `SculptObject_RemeshResymm_Safe_Subtree.py` | Remesh + symmetrize subtree |
| `SculptObject_Remesh_PreserveParts_Selected.py` | Remesh preserving parts |
| `SculptObject_Merge_PreserveParts_Subtree.py` | Merge subtree preserving parts |
| `SculptObject_Split_Masked_Selected.py` | Split frozen/masked area |
| `SculptObject_UniformDensity_Resample_Subtree.py` | Resample to uniform density |
| `SculptObject_UniformDensity_Smart_Subtree.py` | Smart density matching |

### SculptObject - Other
| File | Description |
|------|-------------|
| `SculptObject_IdColors_FromParts.py` | Fill subtree with random ID colors |
| `SculptObject_VoxBool_Intersect.py` | Voxel boolean intersect |
| `SculptObject_VoxBool_Subtract.py` | Voxel boolean subtract |
| `SculptObject_VoxBool_Union.py` | Voxel boolean union |
| `SculptObject_Instance_Tile_Selected.py` | Create tiled instances |

### Scene/Export
| File | Description |
|------|-------------|
| `Scene_SetupTiling_BoxGrid.py` | Setup box grid tiling |
| `Scene_SetupTiling_PlaneGrid.py` | Setup plane grid tiling |
| `Export_ScaleSave_Meshes.py` | Scale and save meshes |

### Debug
| File | Description |
|------|-------------|
| `Debug_InstanceReport.py` | Report on instances in scene |

### Lifecycle
| File | Description |
|------|-------------|
| `LKS_Register.py` | Register addon (extension + actions + panel) |
| `LKS_Unregister.py` | Unregister addon |
| `LKS_FullReload.py` | Full reload for development |
| `LKS_Tools_Panel.py` | Launch comprehensive tools panel |
| `LKS_ExternalPanel_Launch.py` | Launch external panel (IPC-based) |
| `LKS_ExternalPanel_Stop.py` | Stop external panel |

---

## 🛠️ Utilities (`utils/`)

Low-level primitives. Prefix indicates coat dependency: `coat_*` or `Volume_*`/`Scene_*`/`SceneElement_*` = uses coat; no prefix = pure Python.

| File | Description |
|------|-------------|
| `scene_api.py` | Primary interface for scene context and iteration (SceneAPI, SelectionAPI); `collect_subtree_direct()` for instance-safe traversal |
| `scope_utils.py` | Scope enum (CURRENT/TREE/OTHER/ALL) and resolution |
| `SceneElement_visibility_utils.py` | Pure visibility/ghost functions, isolation toggle |
| `Scene_layer_utils.py` | Layer management, UI command workarounds, `consolidate_layers()` |
| `coat_ui_utils.py` | UI command abstractions hiding magic strings |
| `object_utils.py` | Object validation and manipulation |
| `Volume_decimate_utils.py` | Decimate operations on Volumes |
| `Volume_resample_utils.py` | Resample operations on Volumes |
| `Volume_subdivide_utils.py` | Subdivide and symmetry on Volumes |
| `Volume_mode_utils.py` | Mode conversion (surface/voxel) on Volumes |
| `Volume_density_utils.py` | Uniform density matching on Volumes |
| `Scene_cleanup_utils.py` | Cleanup after mesh operations |
| `SceneElement_boolean_utils.py` | Live boolean operations (voxel mode) |
| `Scene_tiling_utils.py` | Tiling grid setup with instances |
| `lks_settings.py` | Persistent settings (brush, autopo, general) |
| `brush_settings_utils.py` | Brush dynamic subdiv configuration |
| `autopo_utils.py` | Autopo workflow automation |
| `action_base.py` | `@action` decorator for hot-reload |
| `action_discovery.py` | Pure Python action script discovery |
| `hot_reload.py` | Dynamic module discovery and reload |
| `coat_menu_utils.py` | 3DCoat menu registration |
| `menu_cleanup.py` | Delete stale LKS_*.xml menu entries |
| `registration_utils.py` | Addon lifecycle (register/unregister) |
| `scene_iteration_utils.py` | Legacy - prefer `scene_api.py` |
| `hotkey_utils.py` | Hotkey XML parsing, validation, dedup, backup (standalone) |
| `hotkey_editor.py` | Qt-based hotkey editor window (standalone or from panel) |

---

## 🎨 UI Components (`ui/`)

PySide6 widgets for the LKS panel.

### Core UI Files
| File | Description |
|------|-------------|
| `styles.py` | Dark theme stylesheet with 20+ COLOR_* constants and f-string generation |
| `ui_main.py` | Main panel window |
| `ui_tab_tools.py` | Tools tab with reorderable sections via GripBoxContainer |
| `ui_tab_extension.py` | Extension tab (reload, register) |
| `ui_tab_outliner.py` | Scene outliner (objects + layer stub) |
| `ui_widget_sub_header.py` | Sub-header widget |

### Collapsible Sections
| File | Description |
|------|-------------|
| `ui_collapsible_decimate_tools.py` | 🔻 Decimate section with emoji header |
| `ui_collapsible_proxy_tools.py` | 📦 Proxy/cache mode section |
| `ui_collapsible_resample_tools.py` | 🔄 Resample section |
| `ui_collapsible_mode_tools.py` | ⚙️ Surface/Voxels conversion section |
| `ui_collapsible_scale_tools.py` | 📏 Scale section |
| `ui_collapsible_visibility_ghost_tools.py` | 👁️👻 Visibility & Ghost combined section |
| `ui_collapsible_smart_tools.py` | ✨ Smart Actions (uniform density, remesh, ID colors) |
| `ui_collapsible_autopo_tools.py` | 🤖 Autopo configuration (polycount max 100k) |
| `ui_collapsible_subdiv_tools.py` | 🔺 Dynamic Subdiv section |
| `ui_collapsible_layers_tools.py` | 📚 Layer management (setup, clean, consolidate) |
| `ui_collapsible_booleans_tools.py` | Voxel boolean operations |

### Reusable Widgets (`utils/ui/widgets/`)

Individual widget modules for better maintainability. Import from `utils.ui.widgets`.

| File | Description |
|------|-------------|
| `__init__.py` | Re-exports all widgets |
| `collapsible_section.py` | Expandable/collapsible group with styled header |
| `button_grid.py` | Grid of buttons with scope-based layout |
| `activity_log.py` | Scrollable log with timestamped, colored messages |
| `labeled_slider.py` | Slider with label and value display |
| `section_header.py` | Styled section header label |
| `tab_widget.py` | Tabbed container for organizing content |
| `tooltip.py` | Rich HTML tooltip with delayed display |
| `tab_container.py` | TabContainer class + `create_tab_with_revert()` factory for consistent tab structure |
| `grip_box_item.py` | GripBox widget - individual item wrapper with 14px drag column on left |
| `grip_box_container.py` | GripBoxContainer - parent managing drag-drop reordering with live preview |

**Usage:**
```python
from utils.ui.widgets import (
    CollapsibleSection, ButtonGrid, add_tooltip, ToolTip,
    create_tab_with_revert, GripBoxContainer, GripBox
)

# Tab with revert button
tab = create_tab_with_revert(log_success, log_error, title="Tools")
layout = tab.content_layout  # Add content here
return tab.widget

# Reorderable sections
container = GripBoxContainer()
container.add_widget(section1, state_key="section1")
container.add_widget(section2, state_key="section2")
```

---

## 📄 Documentation

| File | Description |
|------|-------------|
| `.github/instructions/copilot_style_guide.instructions.md` | Python conventions |
| `.github/instructions/copilot_3dcoat.instructions.md` | 3DCoat/cModule patterns |
| `.github/instructions/copilot_3dcoat_api.instructions.md` | API gotchas (slim) |
| `_docs/magic_ui_strings.md` | Registry of 3DCoat magic UI strings |
| `_docs/external_panel_architecture.md` | External panel IPC system |

---

## 🔌 External Panel System (`_external/`)

Standalone tkinter/ttkbootstrap app communicating with 3DCoat via IPC files.

| File | Description |
|------|-------------|
| `lks_panel_app.py` | Entry point with dependency checking |
| `lks_panel/app.py` | Main tkinter application |
| `lks_panel/ipc_client.py` | High-level IPC client |
| `lks_panel/widgets.py` | Reusable widgets |
| `utils/ipc_protocol.py` | Shared IPC data structures |
| `utils/ipc_server.py` | Command handlers inside 3DCoat |
| `utils/lks_extension.py` | cExtension for IPC polling |

---

## ⚠️ Keeping This Router Updated

Update when adding new scripts, utilities, or UI components.
