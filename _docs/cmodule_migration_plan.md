# LKS cModule Migration Plan

This document captures our learnings about 3DCoat's cModule system and the migration plan from Addon format to cModule format.

---

## Why Migrate from Addon to cModule?

### The Problem with Addons

The Addon format (`UserPrefs/Addons/LKS/UserProjects/`) has limitations:

1. **`cExtension` hooks don't work** - We confirmed that subclassing `coat.cExtension` or `cCore.cExtension` from an Addon does NOT register per-frame hooks (`preprocess`, `postprocess`, etc.)
2. **`extensionHandler` is always `None`** - The internal registration mechanism isn't wired up for Addons
3. **`coat.dialog()` blocks viewport** - Any dialog (even `.noModal()`) captures mouse/keyboard input, preventing sculpting while open
4. **External IPC required** - To get a non-blocking panel, we needed file-based IPC to a separate process (complex, fragile)

### What cModules Provide

The cModule format (`UserPrefs/StdScripts/cModules/LKS/`) provides:

1. ✅ **Working `cExtension` hooks** - `preprocess()`, `postprocess()`, etc. are called every frame
2. ✅ **PySide6/Qt integration** - Non-blocking UI that doesn't capture viewport input
3. ✅ **Auto dependency installation** - `requirements.txt` installs packages automatically
4. ✅ **Access to internal APIs** - `cPy.cCore`, `cPy.cIDE`, `cPy.cRender`, etc.
5. ✅ **`__onstartup.py` hook** - Code that runs when 3DCoat starts

---

## Key Discoveries (From Investigation)

### 1. cExtension Registration Pattern

```python
import cPy.cCore  # NOT coat.cExtension!

class MyExtension(cPy.cCore.cExtension):
    def __init__(self):
        cPy.cCore.cExtension.__init__(self)

    def preprocess(self):
        # Called EVERY FRAME before tools processing
        pass

    def postprocess(self):
        # Called EVERY FRAME after tools processing
        pass

# Just instantiate - auto-registers!
myExtension = MyExtension()
```

### 2. Qt Integration Pattern (From QT cModule)

```python
# __onstartup.py - runs on 3DCoat startup
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication

app = QApplication(["-no-opengl"])
QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL, True)
app.processEvents()

# Main extension file
class QTExtension(cPy.cCore.cExtension):
    def preprocess(self):
        app.processEvents()  # Pump Qt event loop each frame
```

### 3. Menu Item Registration (User-Assignable Shortcuts)

```python
import coat

# Add translations
coat.ui.addTranslation("LKS_MyAction", "LKS: My Action Description")

# Insert into menu (user assigns shortcut via Preferences → Hotkeys)
if not coat.ui.checkIfMenuItemInserted("LKS_MyAction"):
    coat.ui.insertInMenu("SCRIPTS", "LKS_MyAction", 
                         "UserPrefs/StdScripts/cModules/LKS/actions/my_action.py")
```

### 4. Dependency Installation

Create `requirements.txt` in the cModule folder:
```
PySide6
```

3DCoat auto-installs these when the module loads.

### 5. Import Paths in cModules

```python
# From within cModule files, use:
from cModules.LKS._utils.scene_api import SceneAPI
from cModules.LKS._ops.SculptObject_Decimate import main as decimate_op

# The cModules path is automatically in sys.path
```

---

## Folder Structure Comparison

### Before (Addon Format)
```
UserPrefs/Addons/LKS/
├── UserProjects/           # Required subfolder for Addons
│   ├── _ops/
│   ├── _utils/
│   ├── ActionScript.py     # Visible in 3DCoat Scripts menu
│   └── coat.pyi
├── _docs/
├── .github/instructions/
└── lks_settings.json
```

### After (cModule Format)
```
UserPrefs/StdScripts/cModules/LKS/
├── __init__.py             # Package marker
├── __onstartup.py          # Runs on 3DCoat startup
├── requirements.txt        # Auto-installed dependencies
├── LKS.py                  # Main extension (cExtension + UI)
├── _ops/                   # Operators (same as before)
├── _utils/                 # Utilities (same as before)
├── actions/                # Thin scripts for menu items
│   ├── decimate_half_selected.py
│   └── ghost_toggle_subtree.py
├── _docs/
├── .github/instructions/
├── coat.pyi                # Type hints
└── lks_settings.json
```

---

## Migration Checklist

### Phase 1: Prepare (Before Moving)
- [x] Document cModule learnings (this file)
- [x] Update instruction files with cModule context
- [x] Move files from `UserProjects/` up to root `LKS/`
- [x] Create stub cModule entry files (`__init__.py`, `__onstartup.py`, `LKS.py`)
- [x] Create minimal Qt stub UI

### Phase 2: Move to cModules Location
- [ ] Copy/move `LKS/` folder to `UserPrefs/StdScripts/cModules/LKS/`
- [ ] Restart 3DCoat to load the cModule
- [ ] Verify cExtension hooks are firing (check console output)
- [ ] Verify Qt panel appears and doesn't block viewport

### Phase 3: Update Imports
- [ ] Update all imports from `from _utils.` to `from cModules.LKS._utils.`
- [ ] Update all imports from `from _ops.` to `from cModules.LKS._ops.`
- [ ] Test all operators still work

### Phase 4: Register Menu Items
- [ ] Register all actions as menu items in `__onstartup.py`
- [ ] Reassign shortcuts via Edit → Preferences → Hotkeys
- [ ] Remove old Addon from `UserPrefs/Addons/`

---

## Useful Code Snippets

### Check if cExtension is Working
```python
class DebugExtension(cPy.cCore.cExtension):
    def __init__(self):
        cPy.cCore.cExtension.__init__(self)
        self._frame_count = 0

    def preprocess(self):
        self._frame_count += 1
        if self._frame_count % 100 == 0:
            print(f"[LKS] Frame {self._frame_count}")

debugExt = DebugExtension()
```

### Minimal Qt Window
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class LKSPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LKS Tools")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("LKS Panel Active"))
        layout.addWidget(QPushButton("Decimate 50%", clicked=self.on_decimate))
        self.setLayout(layout)
    
    def on_decimate(self):
        from cModules.LKS._ops.SculptObject_Decimate import main
        main(scope=Scope.CURRENT, reduction_percent=50.0)
```

---

## Known Issues / Gotchas

1. **Qt OpenGL conflict** - Use `QApplication(["-no-opengl"])` to avoid conflicts with 3DCoat's OpenGL
2. **Module reloading** - cModules may cache; use `importlib.reload()` during development
3. **Path separators** - Use forward slashes `/` in script paths for `insertInMenu()`
4. **Settings files** - Can still use `coat.io.documents()` for settings persistence

---

## References

- 3DCoat Python API: https://pilgway.com/files/3dcoat/PythonAPI/index.html
- Existing cModules to study: `StdScripts/cModules/QT/`, `StdScripts/cModules/PythonTerminal/`
- Menu sections list: `UserPrefs/Scripts/ExtraMenuItems/menu_sections.txt`
