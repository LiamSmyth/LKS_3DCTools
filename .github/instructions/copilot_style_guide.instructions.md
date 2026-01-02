---
applyTo: '**'
---

# Python Scripting Style Guide (3DCoat Addon)

This style guide is tailored for the LKS 3DCoat addon workspace. It provides conventions for writing clean, maintainable Python scripts within 3DCoat's embedded Python environment.

---

## ⚡ Critical Rules (Read First)

**These rules prevent the most common failures. Internalize before proceeding.**

1. **Self-contained codebase.** No pip, no venv, no external dependencies. All code lives within this workspace.

2. **Verify API before use.** Always search `coat.pyi` to confirm methods exist before using them. Never assume.

3. **Abstract magic strings.** 3DCoat uses undocumented internal string identifiers. Always wrap them in utility functions in `_utils/`.

4. **Thin action scripts.** Root-level `.py` files are exposed to 3DCoat. Keep them minimal—just import and invoke utilities.

5. **Use `coat.io.step(n)` for timing.** 3DCoat operations are asynchronous. Wait for UI to settle before proceeding.

6. **Only document verified truth.** Instruction files must contain ONLY correct, verified information. Never document things that don't exist. When discovering hallucinated API, research the correct approach via `coat.pyi` and document what DOES work.

---

## 1. Purpose and Scope

- A practical rulebook for building Python scripts that run inside 3DCoat's embedded interpreter.
- Optimize for clean separation between 3DCoat API calls (fragile) and reusable logic (stable).
- Keep action scripts thin, utilities robust, and magic strings abstracted.

## 2. How to Use This Guide

- **Humans:** Skim Section 3 (Core Principles), then jump to what you need.
- **LLMs:** Read Sections 3-5 thoroughly; follow all must/should rules.

## 3. Core Principles

- **Single responsibility:** One clear behavior per function or script.
- **Clear naming:** Function names are verbs (`scale_object`, `apply_brush_settings`). Script filenames describe outcome (`SculptObject_Scale_Half.py`).
- **Utility-first:** Push shared logic into `_utils/`. Action scripts just configure and invoke.
- **Abstract fragility:** 3DCoat's magic strings and timing quirks belong in utilities, not action scripts.
- **Determinism:** Produce stable outputs for identical inputs.
- **Windows-safe:** Sanitize paths, respect path length limits, use `pathlib.Path`.

## 4. Repository Layout

```
UserProjects/
├── <ActionScript>.py          # Exposed to 3DCoat - minimal invokers
├── _utils/                    # Hidden from 3DCoat - shared utilities
│   ├── __init__.py
│   ├── coat_api.py            # Low-level 3DCoat API wrappers
│   ├── coat_ui_utils.py       # UI command abstractions
│   ├── coat_scene_utils.py    # Scene/object manipulation
│   ├── lks_settings.py        # Persistent settings cache
│   └── ...
├── _archive/                  # Old/deprecated scripts
├── _example_code/             # Reference implementations
└── <Category>/                # Visible subfolders become categories
    └── <Script>.py
```

**Folder visibility rules:**
- Any `.py` file in `UserProjects/` root appears in 3DCoat's script browser
- Subfolders starting with `_` are hidden from 3DCoat but still importable
- Subfolders without `_` prefix appear as script categories

## 5. Script Types

### 5.1 Action Scripts (Root Level)

**Location:** `UserProjects/*.py`
**Purpose:** Minimal invokers exposed to 3DCoat's script browser
**Naming:** `<Context>_<Action>_<Variant>.py`

Examples:
- `SculptObject_Scale_Half.py`
- `Brush_IncrementDetailsLevel.py`
- `Layer_SetOpacity_Zero.py`

**Pattern:**
```python
"""
Brief description.

Room: Sculpt
Action: One-line description
"""
from _utils.some_utils import some_function

# Minimal logic - just configure and invoke
some_function(param1=value1)
```

### 5.2 Utility Modules (`_utils/`)

**Location:** `UserProjects/_utils/*.py`
**Purpose:** Reusable logic, 3DCoat API abstraction, shared state
**Pattern:** Static functions with configuration parameters

```python
# _utils/brush_utils.py
"""Brush configuration utilities."""

import coat

# Constants - abstract magic strings
CMD_DIALOG_OK = "$DialogButton#1"
SETTING_AUTO_SUBDIVIDE = "$BrushConstructor::AutoSubdivide"

def apply_brush_settings(auto_subdivide: bool, details_level: int) -> None:
    """Apply brush settings to all brush types."""
    # Implementation with magic strings hidden here
    ...
```

### 5.3 Panel Scripts

**Purpose:** Complex UI panels with multiple controls
**Pattern:** Class inheriting from `coat.scripted_panel`

```python
import coat

class MyPanel(coat.scripted_panel):
    caption = "My Panel"
    docking = "right"
    
    def __init__(self):
        self.some_setting = True
    
    def ui(self):
        return [
            "#Section Header",
            "some_setting",
            "DoAction",  # Button
        ]
    
    def DoAction(self):
        from _utils import some_utils
        some_utils.do_something(self.some_setting)

MyPanel()
```

## 6. Module Authoring

### 6.1 Structure

- Add module-level docstring summarizing purpose
- Keep functions short (≤80 lines)
- Use type hints for all function parameters and return types

### 6.2 Type Hints

Type hints are mandatory:

```python
def process_objects(names: list[str], scale: float = 1.0) -> bool:
    ...
```

Use modern Python 3.10+ syntax:
```python
result: str | None = None      # Not Optional[str]
items: list[str] = []          # Not List[str]
```

### 6.3 Constants

Use UPPER_SNAKE_CASE for module-level constants. Group magic strings:

```python
# 3DCoat Commands
CMD_DECIMATE_TO_RETOPO = "$DecimateToRetopo"
CMD_DIALOG_OK = "$DialogButton#1"
CMD_DIALOG_CANCEL = "$DialogButton#2"

# Settings paths
SETTING_AUTO_SUBDIVIDE = "$BrushConstructor::AutoSubdivide"
```

### 6.4 Module Reloading

During development, reload modules to pick up changes:

```python
import importlib
from _utils import some_module
importlib.reload(some_module)
from _utils.some_module import some_function
```

## 7. Settings Persistence

Use a centralized settings system for configuration that persists across sessions:

```python
# _utils/lks_settings.py
SETTINGS_FILE = "UserPrefs/Addons/LKS/lks_settings.json"

DEFAULTS = {
    "details_level": 1,
    "auto_subdivide": True,
}

class LKSSettings:
    _instance = None
    
    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()
    
    # ... attribute access pattern

def get_settings() -> LKSSettings:
    if LKSSettings._instance is None:
        LKSSettings._instance = LKSSettings()
    return LKSSettings._instance

def save_settings() -> None:
    settings = get_settings()
    coat.io.toJson(settings._data, SETTINGS_FILE)
```

## 8. Error Handling

- Fail fast on invalid inputs
- Use `coat.ui.showInfoMessage()` for user-facing errors
- Log context with error messages

```python
def require_sculpt_room() -> None:
    """Ensure we're in Sculpt room, raise if not."""
    if coat.ui.currentRoom() != "Sculpt":
        coat.ui.showInfoMessage("Error: Must be in Sculpt room", 3000)
        raise RuntimeError("Operation requires Sculpt room")
```

## 9. Documentation

- **Action scripts:** Brief docstring with Room and Action
- **Utility modules:** Module-level docstring + function docstrings
- **Panels:** Docstrings for methods that aren't self-explanatory
- **Update router:** Keep `copilot_codebase_router.instructions.md` current

## 10. Best Practices

### 10.1 Minimize Action Script Logic

```python
# GOOD - thin invoker
from _utils.brush_utils import increment_details_level
increment_details_level()

# BAD - too much logic in action script
settings = get_settings()
current = settings.details_level
# ... lots of code
```

### 10.2 Abstract Magic Strings

```python
# GOOD - abstracted
from _utils.coat_ui_utils import confirm_dialog
confirm_dialog()

# BAD - magic string in action script
coat.ui.cmd("$DialogButton#1")
```

### 10.3 Handle Timing

```python
# Many operations need frame delays
coat.ui.toRoom("Retopo")
coat.io.step(4)  # Wait for room switch
coat.ui.cmd("$SomeCommand")
```

### 10.4 Document Room Requirements

```python
"""
Scale selected object.

Room: Sculpt
Requires: Object selected
"""
```

## 11. Granularity and Composition

- Keep scripts under ~500 lines
- Factor heavy logic into utilities
- Utilities should be agnostic to specific workflows

## 12. LLM Agent Workflow

### Todo Lists

LLM agents should maintain todo lists for multi-step tasks.

### Major vs. Minor Edits

**Major edits (confirm before proceeding):**
- Creating new modules
- Refactoring existing structure
- Changes affecting >2 files or >100 lines

**Minor edits (may proceed):**
- Typo fixes
- Small bug fixes
- Changes <100 LOC in ≤2 files

## 13. What NOT to Do

1. **Don't use pip or external packages** - 3DCoat has its own interpreter
2. **Don't create .venv** - Not applicable here
3. **Don't put complex logic in root scripts** - Keep them thin
4. **Don't hardcode magic strings in action scripts** - Abstract to utilities
5. **Don't assume synchronous execution** - Use `coat.io.step()`
6. **Don't forget to reload modules during dev** - Use `importlib.reload()`
