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

3. **Abstract magic strings.** 3DCoat uses undocumented internal string identifiers. Store as typed constants at the top of utility modules and reference `_docs/magic_ui_strings.md` for the full registry.

4. **Thin action scripts.** Root-level `.py` files are exposed to 3DCoat. Keep them minimal—just import and invoke utilities.

5. **Use `coat.io.step(n)` for timing.** 3DCoat operations are asynchronous. Wait for UI to settle before proceeding.

6. **Only document verified truth.** Instruction files must contain ONLY correct, verified information. Never document things that don't exist. When discovering hallucinated API, research the correct approach via `coat.pyi` and document what DOES work.

7. **No shims or compatibility layers.** When deprecating code, DELETE the deprecated file entirely. Do not create re-export shims or adapter code. Reroute users to the new location.

8. **Maintain todo list continuously.** Throughout the conversation, always keep a todo list updated. Work incrementally—mark tasks in-progress before starting, completed immediately after finishing. One task at a time.

9. **Check existing utilities first.** Before writing new code, consult `copilot_codebase_router.instructions.md` and search `_utils/` for existing functions. Reuse and extend existing utilities rather than duplicating functionality.

10. **Update docs with API discoveries.** When discovering 3DCoat API quirks or gotchas, immediately add a concise entry to `copilot_3dcoat_api.instructions.md`. Keep entries brief (these files are always loaded into context).

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
LKS/                           # cModule root
├── <ActionScript>.py          # Exposed to 3DCoat - minimal invokers (in actions/)
├── ops/                       # Configurable operators
│   ├── __init__.py
│   ├── SculptObject_Decimate.py
│   ├── SculptObject_SetGhost.py
│   └── ...
├── utils/                     # Shared utilities
│   ├── __init__.py
│   ├── coat_api.py            # Low-level 3DCoat API wrappers
│   ├── coat_ui_utils.py       # UI command abstractions
│   ├── coat_scene_utils.py    # Scene/object manipulation
│   ├── lks_settings.py        # Persistent settings cache
│   └── ...
├── ui/                        # Qt UI components
│   ├── __init__.py
│   └── styles.py              # Stylesheets and themes
├── data/                      # Runtime state and settings
│   └── lks_*.json             # Settings files
├── .docs/                     # Documentation (hidden)
├── .example_code/             # Reference implementations (hidden)
└── actions/                   # Action scripts for menu registration
    └── <Script>.py
```

**Folder visibility rules:**
- Folders starting with `.` are hidden from 3DCoat (`.docs`, `.example_code`)
- `actions/` folder contains scripts exposed to 3DCoat's script browser
- `ops/`, `utils/`, `ui/`, `data/` are internal modules

## 5. Layered Architecture

The codebase has three layers with distinct responsibilities:

```
┌─────────────────────────────────────────────────────────────┐
│  ACTIONS / PANEL BUTTONS  (Entry Points)                    │
│  - Thin wrappers, exposed to 3DCoat UI                      │
│  - Construct Config, call operators                         │
│  - NO business logic                                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  OPERATORS (`ops/`)       (Workflow Orchestration)          │
│  - Own their Config dataclass (when >3 params)              │
│  - Handle scope resolution (SceneElement → list)            │
│  - Compose utils, manage selection, return counts           │
│  - Bridge SceneElement ↔ Volume for utils                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  UTILS (`utils/`)         (Low-Level Primitives)            │
│  - Raw primitive arguments ONLY (no dataclasses)            │
│  - Operate on coat.Volume or coat.SceneElement directly     │
│  - Abstract magic strings, wrap 3DCoat API                  │
│  - Single-responsibility, composable fragments              │
└─────────────────────────────────────────────────────────────┘
```

### 5.1 Config Pattern Rule

**Blend kwargs and Config dataclass based on parameter count:**

| Parameters | Pattern | Example |
|------------|---------|---------|
| ≤3 params | Use kwargs directly | `main(scope, ghost=True, mode=GhostMode.SET)` |
| >3 params | Use Config dataclass | `main(scope, config=DecimateConfig(...))` |

**Config dataclasses live in operators, NOT in utils:**
```python
# GOOD - Config in operator
# _ops/SculptObject_Decimate.py
@dataclass
class DecimateConfig:
    reduction_percent: float = 50.0
    target_polycount: int | None = None
    preserve_selection: bool = True

# BAD - Config in utils (don't do this)
# _utils/Volume_decimate_utils.py
@dataclass
class DecimateParams:  # NO - utils take raw args
    ...
```

### 5.2 Operators (`_ops/`)

**Location:** `UserProjects/_ops/*.py`
**Purpose:** Configurable workflows that both action scripts and panel buttons invoke
**Naming:** `SculptObject_<Action>.py` (user-facing concept, scope/config are parameters)

**Pattern (≤3 params - use kwargs):**
```python
# _ops/SculptObject_SetGhost.py
"""Ghost/unghost operations with configurable scope and mode."""
from enum import Enum
from utils.scope_utils import Scope, resolve_scope
from utils.SceneElement_visibility_utils import set_ghost, invert_ghost_on_elements

class GhostMode(Enum):
    SET = "set"
    INVERT = "invert"
    ISOLATE = "isolate"

def main(
    scope: Scope = Scope.CURRENT,
    ghost: bool = True,
    mode: GhostMode = GhostMode.SET,
) -> int:
    """Ghost/unghost objects. Returns count processed."""
    elements = resolve_scope(scope)
    # ... compose utils
    return count
```

**Pattern (>3 params - use Config):**
```python
# _ops/SculptObject_Decimate.py
"""Decimate sculpt objects with configurable scope and parameters."""
from dataclasses import dataclass
from utils.scope_utils import Scope, resolve_scope
from utils.Volume_decimate_utils import execute_decimate

@dataclass
class DecimateConfig:
    """Configuration for decimate operation."""
    reduction_percent: float = 50.0
    target_polycount: int | None = None
    use_16x: bool = False
    preserve_selection: bool = True

def main(scope: Scope = Scope.CURRENT, config: DecimateConfig | None = None) -> int:
    """Decimate objects. Returns count of objects processed."""
    if config is None:
        config = DecimateConfig()
    elements = resolve_scope(scope)
    # ... bridge SceneElement → Volume, call utils
    return count
```

**Key principles:**
- Operators have a `main()` with explicit typed parameters
- Own their Config dataclass (when >3 params)
- Use `Scope` enum for element targeting
- Bridge SceneElement → Volume when calling Volume_* utils
- Return count or result for feedback
- Handle selection preservation internally

### 5.3 Action Scripts (Root Level)

**Location:** `UserProjects/*.py`
**Purpose:** Minimal invokers exposed to 3DCoat's script browser
**Naming:** `SculptObject_<Action>_<Config>_<Scope>.py` (user-facing concept)

**Naming components:**
- **Context:** What type of object/domain (e.g., `SculptObject`, `Brush`, `Layer`, `Scene`, `Autopo`, `Export`)
- **Action:** What operation is performed (e.g., `Decimate`, `Scale`, `Ghost`, `ToSurface`)
- **Config:** Configuration/variant (e.g., `Half`, `100x`, `16x`, `PreserveParts`)
- **Scope:** What elements are affected (e.g., `Selected`, `Subtree`, `All`)

Examples:
- `SculptObject_Decimate_Half_Selected.py` - Decimate 50% on selected object
- `SculptObject_Scale_Down100x_Selected.py` - Scale down 100x on selected
- `SculptObject_Ghost_Toggle_Subtree.py` - Toggle ghost on subtree
- `SculptObject_ToSurface_All.py` - Convert all to surface mode
- `Brush_IncrementDetailsLevel.py` - Increment brush detail level
- `Autopo_ToSculpt.py` - Run autopo and import to sculpt

**Pattern (action scripts with @action decorator for hot-reload):**
```python
"""
Brief description.

Room: Sculpt
Action: One-line description
"""
from utils.action_base import action


@action
def main() -> None:
    """Decimate selected object to half polycount."""
    from ops.SculptObject_Decimate import main as op_main
    from utils.scope_utils import Scope
    
    op_main(scope=Scope.CURRENT, reduction_percent=50.0)


main()
```

**Key points:**
- Use `@action` decorator for automatic hot-reload during development
- Imports go INSIDE `main()` so they're reloaded each time
- The decorator calls `reload_all()` before executing the function

### 5.4 Utility Modules (`_utils/`)

**Location:** `UserProjects/_utils/*.py`
**Purpose:** Low-level primitives, 3DCoat API abstraction, single-responsibility functions
**Pattern:** Static functions with RAW PRIMITIVE ARGUMENTS ONLY (no dataclasses)

**Naming Convention:** Prefix indicates 3DCoat dependency

| Prefix | Meaning | Imports `coat`? | Example |
|--------|---------|-----------------|---------|
| `coat_` | Direct 3DCoat API wrappers | Yes | `coat_ui_utils.py`, `coat_menu_utils.py` |
| `<CoatType>_` | Operations on 3DCoat types | Yes | `Volume_decimate_utils.py`, `Scene_layer_utils.py` |
| (no prefix) | Pure Python, testable outside 3DCoat | No | `action_discovery.py`, `scope_utils.py` |

**CoatType prefixes** (match `coat.pyi` types exactly):
- `Volume_` - Sculpt volumes/objects (mesh operations)
- `SceneElement_` - Scene tree elements (visibility, hierarchy)
- `Scene_` - Global scene operations (layers, cleanup)

**Category suffix:** What the utilities do (e.g., `_decimate_utils`, `_visibility_utils`)

**Why this matters:**
- Pure Python modules can be unit tested outside 3DCoat
- Clear at a glance which modules depend on `coat`
- Easier to identify what can be reused in other contexts

**CRITICAL: Utils take raw arguments, NOT dataclasses:**
```python
# GOOD - raw primitive args
def execute_decimate(reduction_percent: float, target_polycount: int | None = None) -> None:
    ...

# BAD - dataclass in utils (belongs in operator)
def execute_decimate(params: DecimateParams) -> None:
    ...
```

**Utils Module Examples:**
```
utils/
├── coat_ui_utils.py            # coat.ui.* wrappers (confirm_dialog, switch_room)
├── coat_menu_utils.py          # coat.ui.insertInMenu, menu registration
├── Volume_decimate_utils.py    # execute_decimate(), configure_decimate_dialog()
├── Volume_resample_utils.py    # execute_resample(), resample_to_half()
├── Volume_subdivide_utils.py   # subdivide_once()
├── Volume_mode_utils.py        # convert_to_surface(), convert_to_voxels()
├── SceneElement_visibility_utils.py  # set_ghost(), set_visibility()
├── Scene_cleanup_utils.py      # cleanup_after_mesh_operation()
├── scene_api.py                # SceneAPI wrappers (depends on coat)
├── action_discovery.py         # Pure Python: scan actions folder, parse filenames
├── scope_utils.py              # Scope enum, resolve_scope (depends on coat)
└── lks_settings.py             # Settings persistence (minimal coat dependency)
```

```python
# _utils/Volume_decimate_utils.py
"""Decimate operations for Volumes. Raw args only."""

import coat
from typing import Callable

# =============================================================================
# MAGIC UI STRINGS
# =============================================================================
CMD_DECIMATE: str = "$DecimateToRetopo"
CMD_DIALOG_OK: str = "$DialogButton#1"
SETTING_TARGET_POLYCOUNT: str = "$DecimateParams::TargetPolycount"

# =============================================================================
# FUNCTIONS (raw primitive args)
# =============================================================================

def configure_decimate_dialog(
    reduction_percent: float | None = None,
    target_polycount: int | None = None,
) -> Callable[[], None]:
    """Create callback to configure decimate dialog. Raw args only."""
    def configurator() -> None:
        if target_polycount is not None:
            coat.ui.setEditBoxValue(SETTING_TARGET_POLYCOUNT, target_polycount)
        # ...
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator

def execute_decimate(
    reduction_percent: float = 50.0,
    target_polycount: int | None = None,
) -> None:
    """Execute decimate on current object. Raw args only."""
    callback = configure_decimate_dialog(reduction_percent, target_polycount)
    coat.ui.cmd(CMD_DECIMATE, callback)
```

### 5.5 Panel Scripts

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
- Use type hints for all function parameters, return types, AND local variables

### 6.2 Type Hints (MANDATORY)

**Explicit typing is mandatory for ALL of the following:**
- Function parameters
- Function return types
- Module-level constants
- Class attributes
- Local variables (when type is not obvious from assignment)

```python
# GOOD - explicit types everywhere
MY_CONSTANT: str = "value"
DEFAULT_COUNT: int = 10
BRUSH_TYPES: list[str] = ["carve", "flatten", "clay"]

def process_objects(names: list[str], scale: float = 1.0) -> bool:
    result: bool = False
    count: int = len(names)
    ...

# BAD - missing types
MY_CONSTANT = "value"
def process_objects(names, scale=1.0):
    result = False
```

Use modern Python 3.10+ syntax:
```python
result: str | None = None      # Not Optional[str]
items: list[str] = []          # Not List[str]
callback: Callable[[coat.SceneElement], bool]  # Typed callbacks
```

### 6.3 Constants & Magic UI Strings

Use UPPER_SNAKE_CASE for module-level constants. **Always include type annotation.**

**Magic UI String Constants (Canonical Pattern):**

When a utility module uses magic UI strings, declare them in a dedicated header section:

```python
# =============================================================================
# OPERATION MAGIC UI STRINGS (NOT in coat.pyi - discovered experimentally)
# =============================================================================

# Commands
CMD_MY_COMMAND: str = "$MyCommand"
CMD_DIALOG_OK: str = "$DialogButton#1"

# Settings
SETTING_MY_PARAM: str = "$MyParams::Value"
SETTING_PER_TYPE: str = "$Category::Setting[{type}]"  # For templated strings
```

See `_utils/autopo_utils.py` for the canonical example. Update `_docs/magic_ui_strings.md` when adding new discoveries.

**Other Constants:**

```python
# Numeric constants
DEFAULT_WAIT_FRAMES: int = 4
MAX_DETAILS_LEVEL: float = 8.0

# String constants
ROOM_SCULPT: str = "Sculpt"
ROOM_RETOPO: str = "Retopo"
```

### 6.4 Prefer Static Functions with Explicit Arguments

**Reduce context/UI operations by passing data explicitly:**

```python
# GOOD - data passed explicitly, no hidden context fetching
def apply_operation_to_elements(
    elements: list[coat.SceneElement],
    operation: Callable[[coat.SceneElement], None]
) -> int:
    count: int = 0
    for el in elements:
        operation(el)
        count += 1
    return count

# BAD - function fetches its own context (magic, harder to test)
def apply_operation_to_selection():
    elements = coat.Scene.sculptRoot().collectSelected()
    for el in elements:
        do_thing(el)
```

**Context should be fetched once at entry points (action scripts) and passed down:**

```python
# Action script (entry point) - OK to fetch context here
from utils.scene_api import SceneAPI
from utils.object_ops import scale_elements

elements: list[coat.SceneElement] = SceneAPI.get_selected_elements()
scale_elements(elements, scale_factor=0.5)
```

### 6.5 Wrap 3DCoat Iterators

Create thin wrappers around 3DCoat's native iterators that return Python lists:

```python
# _utils/scene_api.py - wraps coat iteration patterns
class SceneAPI:
    @staticmethod
    def get_selected_elements() -> list[coat.SceneElement]:
        """Get currently selected elements as a list."""
        root: coat.SceneElement | None = coat.Scene.sculptRoot()
        if not root:
            return []
        return root.collectSelected()
    
    @staticmethod
    def collect_subtree(root: coat.SceneElement) -> list[coat.SceneElement]:
        """Collect all elements in subtree as a list."""
        elements: list[coat.SceneElement] = [root]
        def collector(el: coat.SceneElement) -> bool:
            elements.append(el)
            return False  # continue
        root.iterateVisibleSubtree(collector)
        return elements
```

### 6.4 Module Reloading

During development, reload modules to pick up changes:

```python
import importlib
from _utils import some_module
importlib.reload(some_module)
from utils.some_module import some_function
```

### 6.6 UI Dialog Configurator Pattern

When injecting data into 3DCoat dialogs, use a configurator function that returns a closure.

**Note:** Configurators are typically called from OPERATORS or high-level code. The configurator
function itself lives in utils (with raw args), but Config dataclasses belong in operators.

```python
# In utils: configurator takes RAW ARGS
def configure_decimate_dialog(
    reduction_percent: float | None = None,
    target_polycount: int | None = None,
) -> Callable[[], None]:
    """Create a callback to configure the decimate dialog."""
    def configurator() -> None:
        if target_polycount is not None:
            coat.ui.setEditBoxValue(SETTING_TARGET_POLYCOUNT, target_polycount)
        coat.ui.cmd(CMD_DIALOG_OK)
    return configurator

# In operator: Config dataclass unpacks to raw args
@dataclass
class DecimateConfig:
    reduction_percent: float = 50.0
    target_polycount: int | None = None

def main(scope: Scope, config: DecimateConfig) -> int:
    # Unpack config to raw args for utils
    callback = configure_decimate_dialog(
        reduction_percent=config.reduction_percent,
        target_polycount=config.target_polycount,
    )
    coat.ui.cmd(CMD_DECIMATE, callback)
```

**Key principles:**
- Configurators in utils take raw primitive arguments
- Config dataclasses belong in operators, unpack to raw args when calling utils
- Defaults live as constants at the top of the module where Config is defined
- Configurator returns a closure that captures the args

### 6.7 Separate Large Strings and Data

**Move large strings and data out of main code files for maintainability.**

| Content Type | Extract To | Example |
|--------------|------------|---------|
| Qt stylesheets | `ui/styles.py` | `DARK_STYLESHEET` |
| HTML templates | `ui/templates/<name>.html` | Panel templates |
| Large prompts/text | `data/<name>.txt` | LLM prompts |
| JSON schemas | `schemas/<name>.json` | Validation schemas |
| Default configs | `data/defaults/<name>.json` | Factory settings |

**Pattern for stylesheets:**
```python
# ui/styles.py
DARK_STYLESHEET: str = """
QWidget { ... }
"""

# LKS.py
from ui.styles import DARK_STYLESHEET
self.setStyleSheet(DARK_STYLESHEET)
```

**Pattern for loading text/templates:**
```python
from pathlib import Path

def load_text_resource(name: str) -> str:
    """Load text file from data/ folder."""
    path: Path = Path(__file__).parent / "data" / name
    return path.read_text(encoding="utf-8")
```

**Guidelines:**
- Strings >20 lines should be extracted to separate files
- Use `ui/` folder for Qt-related resources (styles, widgets)
- Use `data/` folder for runtime data (settings, templates)
- Keep test fixtures in `<module>/data/` for isolation

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
from utils.brush_utils import increment_details_level
increment_details_level()

# BAD - too much logic in action script
settings = get_settings()
current = settings.details_level
# ... lots of code
```

### 10.2 Abstract Magic Strings

```python
# GOOD - abstracted
from utils.coat_ui_utils import confirm_dialog
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

### Development Iteration Workflow

The preferred workflow for building new functionality follows a **"prove it first, then refactor"** pattern:

#### Phase 1: Prototype in Action Script
1. Create a new action script (e.g., `SculptObject_MyFeature_Selected.py`)
2. Write the logic inline - imports, business logic, and execution all in one file
3. Test directly in 3DCoat using Scripts menu or hotkey
4. Iterate quickly until the behavior is correct

**Example prototype action script:**
```python
"""Quick prototype - proves the concept works."""
import coat
from utils.scene_api import SceneAPI

# All logic inline for rapid iteration
element = SceneAPI.get_current_element()
if element and element.isSculptObject():
    vol = element.Volume()
    # ... inline logic here
    coat.ui.showInfoMessage("Done!", 1000)
```

#### Phase 2: Extract to Operator + Utils
Once the prototype works:
1. **Identify reusable primitives** → move to `utils/` (raw args only)
2. **Create operator** → move orchestration to `ops/` with Config dataclass if needed
3. **Convert action to thin wrapper** → just `@action` decorator + operator call
4. **Add hot-reload** → use `@action` decorator for automatic module reloading

**Converted thin wrapper:**
```python
"""Thin wrapper - delegates to operator."""
from utils.action_base import action

@action
def main() -> None:
    from ops.SculptObject_MyFeature import main as op_main
    from utils.scope_utils import Scope
    op_main(scope=Scope.CURRENT)

main()
```

#### Hot-Reload Development
The `@action` decorator calls `reload_all()` before execution, enabling:
- Edit `ops/` or `utils/` files
- Run the action script again immediately
- Changes take effect without restarting 3DCoat

**Note:** Complex inline scripts (those with nested functions or module-level state) require manual conversion - the automated converter may break indentation.

## 13. What NOT to Do

1. **Don't use pip or external packages** - 3DCoat has its own interpreter
2. **Don't create .venv** - Not applicable here
3. **Don't put complex logic in root scripts** - Keep them thin
4. **Don't hardcode magic strings in action scripts** - Abstract to utilities
5. **Don't assume synchronous execution** - Use `coat.io.step()`
6. **Don't forget to reload modules during dev** - Use `importlib.reload()`
7. **Don't scatter default values in code** - Use constants at top of module
