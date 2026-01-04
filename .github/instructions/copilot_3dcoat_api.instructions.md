---
applyTo: '**'
---

# 3DCoat API Gotchas & Quirks

This document captures **only** non-obvious behaviors and quirks discovered through experimentation. This is NOT a full API reference — use `coat.pyi` for that.

---

## 🔴 CRITICAL: Verify Methods in coat.pyi

**The `coat` module API is proprietary. Always verify methods exist before using them.**

1. **Search `coat.pyi`** in `UserProjects/` - this is the authoritative type stub
2. Use `grep_search` with the method name to confirm existence
3. Check the exact signature (parameter names, types, return type)

```
# Example verification:
grep_search: "setEditBoxValue" includePattern="coat.pyi"
```

---

## ⏱️ Timing & Async Operations

3DCoat operations are often asynchronous. Use `coat.io.step(n)` to wait frames:

| Operation | Recommended Wait |
|-----------|------------------|
| Room switch (`coat.ui.toRoom`) | `coat.io.step(4)` minimum |
| After dialog commands | `coat.io.step(2)` |
| Complex/baking operations | `coat.io.step(4-8)` |

**Without waiting, subsequent operations may fail or read stale state.**

---

## 🔄 Iteration Callbacks

When using `iterateVisibleSubtree(callback)`:
- Return `False` to **continue** iteration
- Return `True` to **stop** iteration
- Callback receives scene element, use `.Volume()` to get the volume

---

## 🎚️ Per-Brush-Type Settings Require Global Enable

Some settings must be enabled **both globally AND per-brush-type**:

```python
# BOTH are required for RemoveStretching to work:
coat.ui.setBoolValue("$RemoveStretching", True)  # Global
coat.ui.setBoolValue(f"$BrushConstructor::RemoveStretching[{brush}]", True)  # Per-brush
```

---

## 📝 Magic String Patterns

| Pattern | Example | Meaning |
|---------|---------|---------|
| `$CommandName` | `$DecimateToRetopo` | UI command |
| `$Category::Setting` | `$BrushConstructor::AutoSubdivide` | Namespaced setting |
| `$Setting[Type]` | `$BrushConstructor::DetailsLevel[carve]` | Per-type setting |
| `$DialogButton#N` | `$DialogButton#1` | Dialog button (1=OK usually) |

---

## �️ Dialogs Block Viewport Input

`coat.dialog().noModal()` does NOT make the dialog truly non-blocking:
- Execution continues after `.show()`, but...
- **The dialog still captures mouse/keyboard input**
- You cannot sculpt/paint while any dialog is open

**Correct workflow:**
1. Open panel to configure settings
2. Close panel
3. Sculpt normally
4. Use hotkeys to apply tools

---

## 📦 Selection Preservation Pattern

Operations that change selection should restore it:

```python
# Cache selection
selected = root.collectSelected()

# Do operation (may change selection)
do_something()

# Restore
if selected:
    selected[0].selectOne()
    for el in selected[1:]:
        el.select()
```

---

## 🎨 Layer Operations Auto-Create Layers

Decimate and similar operations often create unwanted layers:
- Call `coat.Scene.removeEmptyLayers()` after destructive operations
- Re-activate the correct layer with `coat.Scene.setActiveLayer(id)`

---

## ⚠️ coat.ui.apply() Triggers Mesh Revoxelization

`coat.ui.apply()` simulates pressing Enter. **AVOID using it after setting dialog values.**

**Problem:** On surface meshes, `apply()` triggers a full mesh revoxelization, corrupting the source mesh.

```python
# BAD - triggers revoxelize on surface objects
coat.ui.setEditBoxValue("$SomeDialog::Value", 5000)
coat.ui.apply()  # DON'T DO THIS

# GOOD - use dialog OK button instead
coat.ui.cmd("$DialogButton#1")
```

---

## 📄 coat.io.toJson Requires Object with __dict__

`coat.io.toJson()` serializes Python objects to JSON, but **plain dicts don't serialize correctly**.

**Problem:** Passing a plain Python `dict` to `coat.io.toJson()` produces an empty file.

```python
# BAD - plain dict doesn't serialize
data = {"key": "value"}
coat.io.toJson(data, "file.json")  # Creates empty or invalid file

# GOOD - use native Python json module for dicts
import json
with open(path, "w") as f:
    json.dump(data, f, indent=2)

# OR use an object with __dict__ if you need coat.io.toJson
class Settings:
    def __init__(self):
        self.key = "value"
settings = Settings()
coat.io.toJson(settings, "file.json")  # Works
```

---

## 📁 Path Utilities: coat.io.documents()

Use `coat.io.documents(path)` to convert relative paths to absolute 3DCoat documents paths.

```python
# Convert relative to absolute path in documents folder
rel_path: str = "UserPrefs/Addons/LKS/settings.json"
abs_path: str = coat.io.documents(rel_path)
# Returns: C:\Users\...\Documents\3DCoat\UserPrefs\Addons\LKS\settings.json
```

**Note:** There is NO `coat.documentsPath()` method - this is a common hallucination.

---

## 🔄 Singleton Settings Staleness in Action Scripts

Action scripts (root-level .py files) may be re-executed with stale module state.

**Problem:** When 3DCoat runs an action script, Python module singletons may retain values from previous runs, even if the disk file changed.

**Solution:** Always reload settings from disk at the start of action scripts:

```python
# In action script - force fresh disk read
from _utils.lks_settings import reload_brush_settings, get_brush_settings

reload_brush_settings()  # Clear cache, re-read from disk
settings = get_brush_settings()
```

---

## 🔮 Magic UI Strings Reference

> **Full registry:** See `_docs/magic_ui_strings.md`

Magic strings are UI element IDs passed to `coat.ui.cmd()`, `coat.ui.setEditBoxValue()`, 
`coat.ui.setBoolValue()`, etc. They are **NOT exposed in Python** and are undocumented.

**Discovery method:** RMB+MMB on UI element copies ID to clipboard

**Store as constants** at top of utility modules (see `_utils/autopo_utils.py`):

```python
CMD_MY_COMMAND: str = "$MyCommand"
SETTING_MY_PARAM: str = "$MyParams::Value"
```

---

## � Python Environment & Dependencies

3DCoat embeds **Python 3.8.10** with its own site-packages. Key APIs:

| API | Purpose |
|-----|---------|
| `coat.io.pythonPath()` | Returns site-packages folder path |
| `coat.io.pipInstall("pkg")` | Install packages (what menu "Install Python packages" does) |
| `coat.io.pipUninstall("pkg")` | Uninstall packages |
| `coat.io.installPath()` | 3DCoat installation directory |
| `coat.io.documents(rel)` | Convert relative path to documents folder absolute path |

**Check if package installed:**
```python
def is_installed(module: str) -> bool:
    try:
        __import__(module.replace("-", "_"))
        return True
    except ImportError:
        return False
```

---

## 🚀 External Process Execution

For launching external programs (including Python scripts as separate processes):

| API | Behavior |
|-----|----------|
| `coat.io.exec(cmd, args)` | Launch non-blocking (fire and forget) |
| `coat.io.execAndWait(cmd, args)` | Launch and wait, returns stdout as string |

**Use 3DCoat's own Python for external scripts:**
```python
import sys
python_exe: str = sys.executable  # 3DCoat's Python interpreter
script_path: str = coat.io.documents("UserProjects/_external/app.py")
coat.io.exec(python_exe, script_path)  # Runs as separate process
```

---

## 🔌 cExtension: Per-Frame Hooks

`cExtension` class provides hooks that run every frame WITHOUT blocking viewport:

```python
class MyExtension(coat.cExtension):
    def preprocess(self):   # Before tools processing
    def postprocess(self):  # After tools processing  
    def afterUI(self):      # After UI rendering
    def onNew(self):        # New scene created
    def onChangeTool(self): # Tool changed
    def onChangeRoom(self): # Room changed
```

**Register extension:** Instantiate the class; it auto-registers.
**Send messages:** `coat.cExtension.Message("ExtName", "msg")` → received in `onMessage(msg)`

---

## �📋 Adding to This Document

**Keep this file lean.** Only add:
- ✅ Non-obvious gotchas that could trip someone up
- ✅ Critical patterns needed during development

**Move to `_docs/magic_ui_strings.md`:**
- Comprehensive magic string tables
- Detailed parameter lists
