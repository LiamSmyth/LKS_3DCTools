# LKS 3DCoat Addon - Session Recovery Document

This document summarizes all work completed in prior sessions that needs to be rebuilt after accidental deletion.

---

## Overview

The LKS addon provides a centralized tools panel and action scripts for 3DCoat, with these main feature areas:
1. **Dynamic Subdivision Settings** - Control auto_subdivide, details_level, remove_stretching across all brushes
2. **Autopo Workflow** - Run autopo with cached settings, import results back to sculpt
3. **Object Operations** - Scale, decimate, and manipulate sculpt objects
4. **Layer Utilities** - Layer opacity, consolidation operations

---

## Architecture

### Folder Structure
```
UserProjects/
├── LKS_Tools_Panel.py         # Main panel with all UI
├── Brush_IncrementDetailsLevel.py
├── Brush_DecrementDetailsLevel.py
├── Brush_ApplyDynamicSubdivSettings.py
├── Autopo_Run.py
├── Autopo_ToSculpt.py
├── Autopo_ToMultires.py
├── SculptObject_Scale_Half.py
├── SculptObject_Scale_Double.py
├── _utils/
│   ├── __init__.py
│   ├── lks_settings.py
│   ├── coat_ui_utils.py
│   ├── brush_settings_utils.py
│   ├── autopo_utils.py
│   ├── object_utils.py
│   └── scene_iteration_utils.py
```

### Design Principles
- **Thin action scripts** - Root `.py` files just configure and invoke utilities
- **Abstract magic strings** - All 3DCoat `$CommandName` strings go in `_utils/`
- **Centralized settings** - `lks_settings.py` provides singleton settings cache
- **Panel syncs to cache** - Panel properties sync to JSON via `_sync_to_cache()`

---

## Feature 1: Settings System

### `_utils/lks_settings.py`

```python
"""Persistent settings cache for LKS tools."""
import coat

SETTINGS_FILE = "UserPrefs/Addons/LKS/lks_settings.json"

DEFAULTS = {
    # Dynamic Subdiv
    "details_level": 1,
    "auto_subdivide": True,
    "remove_stretching": True,
    
    # Autopo
    "autopo_density": 10000,
    "autopo_optimize_mesh": True,
    "autopo_keep_creases": False,
    "autopo_add_to_scene": True,
    
    # Decimate
    "decimate_reduction": 50,
}

class LKSSettings:
    """Singleton settings with attribute access."""
    _instance = None
    
    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()
    
    def _load(self):
        if coat.io.fileExists(SETTINGS_FILE):
            coat.io.fromJsonFile(self._data, SETTINGS_FILE)
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        return self._data.get(name, DEFAULTS.get(name))
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

def get_settings() -> LKSSettings:
    if LKSSettings._instance is None:
        LKSSettings._instance = LKSSettings()
    return LKSSettings._instance

def save_settings() -> None:
    settings = get_settings()
    coat.io.toJson(settings._data, SETTINGS_FILE)
```

---

## Feature 2: UI Utilities

### `_utils/coat_ui_utils.py`

```python
"""UI command abstractions hiding magic strings."""
import coat

# Dialog buttons
CMD_DIALOG_OK = "$DialogButton#1"
CMD_DIALOG_CANCEL = "$DialogButton#2"

def confirm_dialog() -> None:
    """Click OK on current dialog."""
    coat.ui.cmd(CMD_DIALOG_OK)

def cancel_dialog() -> None:
    """Click Cancel on current dialog."""
    coat.ui.cmd(CMD_DIALOG_CANCEL)

def command_with_confirm(command: str) -> None:
    """Execute command and auto-confirm dialog."""
    coat.ui.cmd(command, lambda: coat.ui.cmd(CMD_DIALOG_OK))

def switch_to_room(room: str, wait_frames: int = 4) -> None:
    """Switch to room and wait for transition."""
    if coat.ui.currentRoom() != room:
        coat.ui.toRoom(room)
        coat.io.step(wait_frames)

def show_message(text: str, duration_ms: int = 2000) -> None:
    """Show toast message."""
    coat.ui.showInfoMessage(text, duration_ms)
```

---

## Feature 3: Brush Settings

### `_utils/brush_settings_utils.py`

```python
"""Brush configuration utilities for all brush types."""
import coat

BRUSH_TYPES = [
    "carve", "flatten", "clay", "build", "draw", "smooth",
    "pinch", "inflate", "layer", "shift", "scrape", "fill",
    "growclay", "claytubes", "dam", "crease", "cut", "cutoff",
    "voxhide", "pose", "snake", "muscules", "twist", "move",
    "rapid", "polish", "brush3d", "chisel", "planar", "hpolish",
    "sweep", "caps", "reconstruct", "measure"
]

class BrushSettingsUtils:
    @staticmethod
    def apply_global_brush_settings(
        auto_subdivide: bool, 
        details_level: float, 
        remove_stretching: bool
    ) -> None:
        """Apply dynamic subdiv settings to ALL brush types."""
        BrushSettingsUtils.set_auto_subdivide_all(auto_subdivide)
        BrushSettingsUtils.set_details_level_all(details_level)
        BrushSettingsUtils.set_remove_stretching_all(remove_stretching)
    
    @staticmethod
    def set_auto_subdivide_all(enabled: bool) -> None:
        for brush_type in BRUSH_TYPES:
            setting = f"$BrushConstructor::AutoSubdivide[{brush_type}]"
            coat.ui.setBoolValue(setting, enabled)
    
    @staticmethod
    def set_details_level_all(level: float) -> None:
        for brush_type in BRUSH_TYPES:
            setting = f"$BrushConstructor::DetailsLevel[{brush_type}]"
            coat.ui.setFloatValue(setting, level)
    
    @staticmethod
    def set_remove_stretching_all(enabled: bool) -> None:
        # Set global setting (required for it to work)
        coat.ui.setBoolValue("$RemoveStretching", enabled)
        # Also set per-brush-type
        for brush_type in BRUSH_TYPES:
            setting = f"$BrushConstructor::RemoveStretching[{brush_type}]"
            coat.ui.setBoolValue(setting, enabled)
```

### Action Scripts

**`Brush_IncrementDetailsLevel.py`**
```python
"""Increment Details Level - adds 1 to current level."""
from _utils.lks_settings import get_settings, save_settings
from _utils.brush_settings_utils import BrushSettingsUtils

settings = get_settings()
settings.details_level = settings.details_level + 1
settings.auto_subdivide = True
save_settings()

BrushSettingsUtils.apply_global_brush_settings(
    settings.auto_subdivide,
    settings.details_level,
    settings.remove_stretching
)
coat.ui.showInfoMessage(f"Details Level: {settings.details_level}", 2000)
```

**`Brush_DecrementDetailsLevel.py`**
```python
"""Decrement Details Level - subtracts 1 (floor at 0)."""
from _utils.lks_settings import get_settings, save_settings
from _utils.brush_settings_utils import BrushSettingsUtils

settings = get_settings()
settings.details_level = max(0, settings.details_level - 1)
settings.auto_subdivide = True
save_settings()

BrushSettingsUtils.apply_global_brush_settings(
    settings.auto_subdivide,
    settings.details_level,
    settings.remove_stretching
)
coat.ui.showInfoMessage(f"Details Level: {settings.details_level}", 2000)
```

---

## Feature 4: Autopo Utilities

### `_utils/autopo_utils.py`

```python
"""Autopo workflow automation."""
import coat
from _utils.lks_settings import get_settings
from _utils.coat_ui_utils import switch_to_room, command_with_confirm

CMD_AUTOPO = "$AutoRetopo"
CMD_IMPORT_MULTIRES = "$RetopoBuildMR"

def run_autopo_with_settings() -> None:
    """Run autopo using cached settings."""
    settings = get_settings()
    
    # Set autopo parameters
    coat.ui.setIntValue("$AutoRetopo::TargetPolycount", settings.autopo_density)
    coat.ui.setBoolValue("$AutoRetopo::OptimizeMesh", settings.autopo_optimize_mesh)
    coat.ui.setBoolValue("$AutoRetopo::KeepCreases", settings.autopo_keep_creases)
    coat.ui.setBoolValue("$AutoRetopo::AddToScene", settings.autopo_add_to_scene)
    
    # Run autopo with auto-confirm
    command_with_confirm(CMD_AUTOPO)

def autopo_to_sculpt() -> None:
    """Run autopo, import to sculpt, hide original."""
    # Cache original object info
    original = coat.Scene.current().Volume()
    original_element = original.inScene()
    original_name = original_element.name()
    original_parent = original_element.parent()
    
    # Run autopo
    run_autopo_with_settings()
    coat.io.step(4)
    
    # Switch to retopo, then back to sculpt
    switch_to_room("Retopo", 4)
    switch_to_room("Sculpt", 4)
    
    # Import retopo to sculpt
    command_with_confirm("$RetopoToSculpt")
    coat.io.step(4)
    
    # Hide original (new object is now selected)
    # Find and ghost the original
    original_element.ghost(True)
    
    coat.ui.showInfoMessage(f"Imported retopo, hid '{original_name}'", 3000)

def autopo_to_multiresolution() -> None:
    """Run autopo and import as multiresolution lowest level."""
    run_autopo_with_settings()
    coat.io.step(4)
    
    # Must be in Sculpt room for multires import
    switch_to_room("Sculpt", 4)
    
    # Import as multiresolution
    command_with_confirm(CMD_IMPORT_MULTIRES)
    coat.io.step(4)
    
    coat.ui.showInfoMessage("Imported as multiresolution", 3000)
```

---

## Feature 5: Main Panel

### `LKS_Tools_Panel.py` Structure

```python
import coat
from _utils.lks_settings import get_settings, save_settings
from _utils.brush_settings_utils import BrushSettingsUtils

class LKSToolsPanel(coat.scripted_panel):
    caption = "LKS Tools"
    docking = "right"
    min_width = 280
    min_height = 600
    
    def __init__(self):
        settings = get_settings()
        
        # Dynamic Subdiv section
        self.auto_subdivide = settings.auto_subdivide
        self.details_level = settings.details_level
        self.remove_stretching = settings.remove_stretching
        
        # Autopo section
        self.autopo_density = settings.autopo_density
        self.autopo_optimize_mesh = settings.autopo_optimize_mesh
        self.autopo_keep_creases = settings.autopo_keep_creases
        self.autopo_add_to_scene = settings.autopo_add_to_scene
        
        # Decimate section
        self.decimate_reduction = settings.decimate_reduction
    
    def _sync_to_cache(self):
        """Sync panel properties to settings cache."""
        settings = get_settings()
        settings.auto_subdivide = self.auto_subdivide
        settings.details_level = self.details_level
        settings.remove_stretching = self.remove_stretching
        settings.autopo_density = self.autopo_density
        settings.autopo_optimize_mesh = self.autopo_optimize_mesh
        settings.autopo_keep_creases = self.autopo_keep_creases
        settings.autopo_add_to_scene = self.autopo_add_to_scene
        settings.decimate_reduction = self.decimate_reduction
        save_settings()
    
    # ==================== DYNAMIC SUBDIV ====================
    def ApplyDynamicSubdiv(self):
        self._sync_to_cache()
        BrushSettingsUtils.apply_global_brush_settings(
            self.auto_subdivide,
            self.details_level,
            self.remove_stretching
        )
        coat.ui.showInfoMessage(
            f"DynSubdiv: {'ON' if self.auto_subdivide else 'OFF'}, "
            f"Detail={self.details_level}, "
            f"Stretch={'ON' if self.remove_stretching else 'OFF'}", 
            3000
        )
    
    # ==================== AUTOPO ====================
    def RunAutopo(self):
        self._sync_to_cache()
        from _utils import autopo_utils
        autopo_utils.run_autopo_with_settings()
    
    def AutopoToSculpt(self):
        self._sync_to_cache()
        from _utils import autopo_utils
        autopo_utils.autopo_to_sculpt()
    
    def AutopoToMultires(self):
        self._sync_to_cache()
        from _utils import autopo_utils
        autopo_utils.autopo_to_multiresolution()
    
    # ==================== UI LAYOUT ====================
    def ui(self):
        return [
            "#Dynamic Subdiv",
            "auto_subdivide",
            "details_level,[0,16]",
            "remove_stretching",
            "ApplyDynamicSubdiv",
            
            "---",
            
            "#Autopo",
            "autopo_density",
            "autopo_optimize_mesh",
            "autopo_keep_creases",
            "autopo_add_to_scene",
            "[1 1 1]",
            "RunAutopo",
            "AutopoToSculpt",
            "AutopoToMultires",
            
            "---",
            
            "#Decimate",
            "decimate_reduction,[0,100]",
            # ... more sections
        ]

LKSToolsPanel()
```

---

## Key Discoveries

### Magic String Patterns
- `$CommandName` - UI commands
- `$DialogButton#1` - OK button
- `$DialogButton#2` - Cancel button
- `$Category::Setting[Type]` - Per-type settings
- `$GlobalSetting` - Global settings

### Timing Requirements
- Room switches need `coat.io.step(4)` minimum
- Complex operations need `coat.io.step(4-8)`
- Dialog callbacks may need their own timing

### Settings Gotchas
- `$RemoveStretching` is a global setting, not per-brush-type
- Must set both global AND per-brush-type for some settings
- Panel properties sync to `self.*` immediately, but JSON only saves on `_sync_to_cache()`

### Autopo Workflow
- Must return to Sculpt room before running multires import
- Original object can be ghosted after new object is created
- Use `command_with_confirm()` for dialogs that need auto-OK

---

## Rebuild Checklist

1. ✅ Create instruction files (style guide, 3dcoat patterns, API reference)
2. ⬜ Create `_utils/__init__.py`
3. ⬜ Create `_utils/lks_settings.py`
4. ⬜ Create `_utils/coat_ui_utils.py`
5. ⬜ Create `_utils/brush_settings_utils.py`
6. ⬜ Create `_utils/autopo_utils.py`
7. ⬜ Create `LKS_Tools_Panel.py`
8. ⬜ Create `Brush_IncrementDetailsLevel.py`
9. ⬜ Create `Brush_DecrementDetailsLevel.py`
10. ⬜ Create `Brush_ApplyDynamicSubdivSettings.py`
11. ⬜ Create `Autopo_Run.py`
12. ⬜ Create `Autopo_ToSculpt.py`
13. ⬜ Create `Autopo_ToMultires.py`
14. ⬜ Refactor existing scripts to use `_utils/`
