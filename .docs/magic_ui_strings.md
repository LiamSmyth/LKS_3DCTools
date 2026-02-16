# 3DCoat Magic UI Strings Reference

This document is a comprehensive registry of all known magic UI strings used in 3DCoat scripting.
These strings are **NOT** documented in `coat.pyi` and are discovered through experimentation.

> **Discovery Method:** RMB+MMB on a UI element copies its ID to clipboard 
> (requires Edit→Preferences→General→Script info type setting)

---

## 📋 Table of Contents

- [Dialog Buttons](#dialog-buttons)
- [Autopo / Quadrangulation](#autopo--quadrangulation)
- [Resample](#resample)
- [Decimate](#decimate)
- [Voxelize](#voxelize)
- [Retopo Commands](#retopo-commands)
- [Sculpt Layers Panel](#sculpt-layers-panel)
- [Brush Settings (Per-Brush-Type)](#brush-settings-per-brush-type)
- [Symmetry Parameters](#symmetry-parameters)
- [Extrude Parameters](#extrude-parameters)
- [Smooth Parameters](#smooth-parameters)
- [Export Options](#export-options)
- [Texture / Baking](#texture--baking)
- [Miscellaneous Commands](#miscellaneous-commands)
- [coat.settings Keys](#coatsettings-keys)

---

## Dialog Buttons

Used to auto-confirm or cancel dialogs.

| String | Purpose | Type |
|--------|---------|------|
| `$DialogButton#1` | OK / Confirm button | cmd |
| `$DialogButton#2` | Cancel button | cmd |

**Utility Location:** `_utils/coat_ui_utils.py` → `CMD_DIALOG_OK`, `CMD_DIALOG_CANCEL`

---

## Autopo / Quadrangulation

Parameters for the autopo (automatic retopology) feature.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$Quadrangulate` | Open autopo dialog | cmd | - |
| `$QuadragulationTask::RequiredPolycount` | Target poly count | int | e.g., 10000 |
| `$QuadragulationTask::CaptureDetails` | Detail capture percentage | float | 0.0-100.0 |
| `$QuadragulationTask::HardsurfaceRetopology` | Hard surface mode | bool | true/false |
| `$QuadragulationTask::AutoDensityInfluence` | Auto density influence | float | 0.0-2.0 |
| `$QuadragulationTask::Voxelize` | Voxelize before autopo | bool | true/false |
| `$QuadragulationTask::VoxelizedObjectPolycount1` | Voxelize target polycount (K) | int | e.g., 1000 |
| `$QuadragulationTask::DecimateIfAbove` | Enable decimation if above limit | bool | true/false |
| `$QuadragulationTask::DecimationLimit1` | Decimation limit (K) | int | e.g., 1000 |
| `$QuadragulationTask::TangentSmoothRes` | Tangent smooth result | bool | true/false |
| `$QuadragulationTask::BypassDensityAndStrokes` | Skip density modal | bool | true/false |
| `COMBOBOX_QuadQuality` | Quality preset dropdown | combo | draft/intermediate/best |

**Utility Location:** `_utils/autopo_utils.py`

---

## Resample

Parameters for the resample operation.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$Resample` | Execute resample command | cmd | - |
| `$ResampleParams::RequiredPolycount` | Target poly count | int | e.g., 50000 |
| `$ResampleParams::ResamplingScale` | Scale factor | float | e.g., 2.0, 0.5 |

**Utility Location:** `_utils/ui_dialog_utils.py`

**Example Usage:**
```python
def ui_command():
    coat.ui.setEditBoxValue("$ResampleParams::RequiredPolycount", target)
    coat.ui.setSliderValue("$ResampleParams::ResamplingScale", scale)
    coat.ui.cmd("$DialogButton#1")
coat.ui.cmd("$Resample", ui_command)
```

---

## Decimate

Parameters for the decimate operation.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$Decimate` | Execute decimate command | cmd | - |
| `$Decimate16X` | Decimate to 1/16th | cmd | - |
| `$DecimationParams::ReducedPolycount` | Target poly count | int | e.g., 25000 |
| `$DecimationParams::ReductionPercent` | Reduction percentage | float | 0.0-100.0 |

**Utility Location:** `_utils/ui_dialog_utils.py`

---

## Voxelize

Parameters for converting to voxels.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$ToVoxels` | Execute voxelize command | cmd | - |
| `$VoxelizeParams::SuggestedPolycount` | Target voxel density | int | e.g., 100000 |

**Utility Location:** `_utils/ui_dialog_utils.py`

---

## Retopo Commands

Commands for retopology operations.

| String | Purpose | Type |
|--------|---------|------|
| `$DecimateToRetopo` | Decimate current object to retopo | cmd |
| `$DecimateAllToRetopo` | Decimate all objects to retopo | cmd |
| `$RetopoToSculpt` | Import retopo mesh to sculpt | cmd |
| `$AddLowestLevelFromRetopo` | Import as multiresolution (lowest level) | cmd |
| `$ClearTM` | Clear retopo mesh | cmd |
| `$UseNamesCorrespondence` | Use names correspondence for baking | bool |

**Utility Location:** `_utils/coat_ui_utils.py`, `_utils/autopo_utils.py`

---

## Sculpt Layers Panel

Commands for the sculpt layers panel. Operate on currently selected layer.

| String | Purpose | Type |
|--------|---------|------|
| `$LayersPanel::AddNewLayer` | Add new layer | cmd |
| `$LayersPanel::DuplicateLayer` | Duplicate current layer | cmd |
| `$LayersPanel::TrashLayer` | Delete current layer | cmd |
| `$LayersPanel::DeleteLayer` | Delete all unused layers | cmd |
| `$LayersPanel::MoveLayerUp` | Move layer up | cmd |
| `$LayersPanel::MoveLayerDown` | Move layer down | cmd |
| `$LayersPanel::MergeDown` | Merge layer down | cmd |

**Note:** No utility module currently wraps these - add to `_utils/layer_utils.py` if needed.

---

## Brush Settings (Per-Brush-Type)

Settings that apply per-brush. Replace `{brush}` with brush type name.

| Pattern | Purpose | Type | Value |
|---------|---------|------|-------|
| `$BrushConstructor::AutoSubdivide[{brush}]` | Auto subdivide toggle | bool | true/false |
| `$BrushConstructor::DetailsLevel[{brush}]` | Detail level | float | 1.0-8.0 |
| `$BrushConstructor::RemoveStretching[{brush}]` | Remove stretching | bool | true/false |
| `$RemoveStretching` | **Global** remove stretching toggle | bool | true/false |

**Common Brush Types:** `BUILDUP`, `SCULPT_PINCH`, `carve`, `flatten`, `clay`, `build`, `draw`, `smooth`, `pinch`, `inflate`, `layer`, `shift`, `scrape`, `fill`

**Utility Location:** `_utils/brush_settings_utils.py`

**Important:** For `RemoveStretching` to work, BOTH global and per-brush must be enabled.

---

## Symmetry Parameters

Parameters for symmetry/tiling settings.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$SymmetryParams::EnableSymmetry` | Enable symmetry | bool | true/false |
| `$SymmetryParams::tNumX` | Tile count X | int | 0+ |
| `$SymmetryParams::tNumY` | Tile count Y | int | 0+ |
| `$SymmetryParams::tNumZ` | Tile count Z | int | 0+ |
| `$SymmetryParams::tStepX` | Tile step X | float | size |
| `$SymmetryParams::tStepY` | Tile step Y | float | size |
| `$SymmetryParams::tStepZ` | Tile step Z | float | size |

**Note:** No utility module currently wraps these.

---

## Extrude Parameters

Parameters for extrude operations.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$ExtrudeVO` | Execute voxel extrude | cmd | - |
| `$ExtrudeParams::Extrusion` | Extrusion amount | float | e.g., 0.2 |

**Note:** No utility module currently wraps these.

---

## Smooth Parameters

Parameters for smooth operations.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$SmoothParams::SmoothingDegree` | Smoothing intensity | float | 0.0-1.0 |

**Note:** No utility module currently wraps these.

---

## Export Options

Parameters for export dialogs.

| String | Purpose | Type | Value |
|--------|---------|------|-------|
| `$EXPORTOBJECT` | Open export dialog | cmd | - |
| `$Blender` | Blender export preset | cmd | - |
| `$ExportOpt::ExportMeshName` | Mesh name for export | string | name |
| `$ExportOpt::ExportTextures` | Export textures | bool | true/false |
| `$ExportOpt::ExportGeometry` | Export geometry | bool | true/false |
| `$ExportOpt::PathForTextures` | Textures export path | string | path |
| `$COMBOBOX_{preset}` | Select export preset | cmd | - |

**Utility Location:** `_utils/coat_ui_utils.py` → `CMD_EXPORT_OBJECT`, `CMD_BLENDER_EXPORT`

---

## Texture / Baking

Parameters for texture and baking operations.

| String | Purpose | Type |
|--------|---------|------|
| `$MergeForDPNM_flatdisp` | Bake normal + flat displacement | cmd |
| `$COMBOBOX_TEXTURE_SIZE_X{size}` | Set texture width | cmd |
| `$COMBOBOX_TEXTURE_SIZE_Y{size}` | Set texture height | cmd |
| `$SnapToNearestAlongNormal` | Snap retopo to sculpt normals | cmd |
| `$ApplyTSm` | Apply tangent smoothing | cmd |

**Utility Location:** `_utils/coat_ui_utils.py`

---

## Miscellaneous Commands

| String | Purpose | Type |
|--------|---------|------|
| `$ToggleCachingVolume` | Toggle volume caching | cmd |
| `$VoxTreeBranch.IncRes_HINT.Root` | Subdivide (increase resolution) | cmd |

---

## coat.settings Keys

Keys used with `coat.settings.getString()`, `coat.settings.setString()`, etc.

| Key | Purpose | Values |
|-----|---------|--------|
| `SoftwarePreset` | Export software target | `Blender`, `UnrealEngine`, etc. |
| `NormalsCalculationMethod` | Normal calculation mode | enum values |
| `NMAP_EXPORT_TYPE` | Normal map export type | enum values |
| `RoughnessPresetForNM` | Roughness preset | enum values |
| `NMResolution` | Normal map resolution | `256`, `512`, `1024`, etc. |

**Note:** These are different from magic UI strings - they use the `coat.settings` API.

---

## 🔧 Where to Add New Discoveries

When you discover new magic strings:

1. **Add to appropriate utility module** as typed constants at the top:
   ```python
   # =============================================================================
   # OPERATION MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
   # =============================================================================
   
   CMD_MY_COMMAND: str = "$MyCommand"
   SETTING_MY_PARAM: str = "$MyParams::Value"
   ```

2. **Update this document** with the new strings

3. **Use constants in code** - never hardcode magic strings in functions

---

## 📝 Adding to This Document

**Only add entries that are:**
- ✅ Verified to work (tested in 3DCoat)
- ✅ Include the exact string, type (cmd/bool/int/float/string), and purpose
- ✅ Note which utility module contains constants for it (if any)

**Pattern Reference:**
- `$CommandName` - UI command/button
- `$Category::Setting` - Namespaced parameter
- `$Setting[Type]` - Per-type setting (e.g., per-brush)
- `$DialogButton#N` - Dialog button (1=OK, 2=Cancel)
