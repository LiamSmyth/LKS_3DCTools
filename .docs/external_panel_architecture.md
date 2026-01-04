# LKS External Panel Architecture

This document describes the architecture for running pure Python UI tools that communicate bidirectionally with 3DCoat without blocking the viewport.

---

## Problem Statement

3DCoat's built-in `coat.dialog()` panels block viewport input even in "transparent" mode. We need external UI that:
- Runs in a separate process (no viewport blocking)
- Can send commands to 3DCoat (invoke actions)
- Can receive scene state updates (display scene info)
- Self-heals dependencies on first run
- Is fully self-contained (unzip and go)

---

## Solution Overview

```
┌─────────────────────────────────────┐     ┌─────────────────────────────────────┐
│          3DCoat Process             │     │       External Python Process       │
│                                     │     │                                     │
│  ┌─────────────────────────────┐    │     │    ┌─────────────────────────────┐  │
│  │     LKSExtension            │    │     │    │    LKS Panel App            │  │
│  │     (cExtension)            │    │     │    │    (tkinter/ttkbootstrap)   │  │
│  │                             │    │     │    │                             │  │
│  │  preprocess():              │    │     │    │  - Scene element list       │  │
│  │    - Poll commands.json     │◄───┼─────┼────┤  - Action buttons           │  │
│  │    - Execute commands       │    │     │    │  - Settings controls        │  │
│  │    - Write results.json     │────┼─────┼───►│                             │  │
│  │    - Write scene_state.json │    │     │    │  Polls results.json         │  │
│  │                             │    │     │    │  Polls scene_state.json     │  │
│  └─────────────────────────────┘    │     │    └─────────────────────────────┘  │
│                                     │     │                                     │
└─────────────────────────────────────┘     └─────────────────────────────────────┘
                    │                                         │
                    └──────────────┬──────────────────────────┘
                                   │
                            ┌──────▼──────┐
                            │   _ipc/     │
                            │             │
                            │ commands.json
                            │ results.json
                            │ scene_state.json
                            │ heartbeat.json
                            └─────────────┘
```

---

## Key Components

### 1. IPC Protocol (`_utils/ipc_protocol.py`)

Shared data structures and atomic file operations. Python 3.8 compatible.

```python
# Command from UI → 3DCoat
@dataclass
class IPCCommand:
    id: str           # UUID for tracking
    action: str       # "list_elements", "decimate", etc.
    params: dict      # Action-specific parameters
    timestamp: float  # For ordering/staleness

# Result from 3DCoat → UI
@dataclass
class IPCResult:
    command_id: str   # Matches IPCCommand.id
    success: bool
    data: Any         # Action-specific result
    error: str | None

# Scene state broadcast
@dataclass
class SceneState:
    timestamp: float
    elements: list[dict]  # Simplified element info
    current_room: str
    selection: list[str]
```

### 2. cExtension Subclass (`_utils/lks_extension.py`)

Runs inside 3DCoat, polls IPC folder every frame:

```python
class LKSExtension(coat.cExtension):
    def __init__(self):
        self._frame_counter = 0
        self._poll_interval = 5  # Check every 5 frames
    
    def preprocess(self):
        self._frame_counter += 1
        if self._frame_counter >= self._poll_interval:
            self._frame_counter = 0
            self._process_commands()
            self._update_scene_state()
            self._write_heartbeat()
```

### 3. External Panel App (`_external/lks_panel_app.py`)

Tkinter app with graceful ttkbootstrap fallback:

```python
# Self-healing dependency check on startup
def ensure_dependencies():
    required = ["ttkbootstrap"]
    missing = [p for p in required if not is_installed(p)]
    if missing:
        # Show simple tk dialog asking to install
        # Use coat.io.pipInstall() via IPC or subprocess
```

### 4. Launch Script (`LKS_ExternalPanel_Launch.py`)

Action script visible in 3DCoat's Scripts menu:

```python
import sys
import coat

def main():
    # 1. Register extension if not already
    # 2. Launch external panel as separate process
    python_exe = sys.executable
    script = coat.io.documents("UserProjects/_external/lks_panel_app.py")
    coat.io.exec(python_exe, script)

main()
```

---

## IPC File Protocol

### File Locations

All IPC files live in `UserProjects/_ipc/`:

| File | Writer | Reader | Purpose |
|------|--------|--------|---------|
| `commands.json` | External UI | 3DCoat | Pending commands queue |
| `results.json` | 3DCoat | External UI | Command execution results |
| `scene_state.json` | 3DCoat | External UI | Current scene snapshot |
| `heartbeat.json` | 3DCoat | External UI | Extension alive signal |
| `shutdown.flag` | External UI | 3DCoat | Graceful shutdown signal |

### Atomic Write Pattern

To prevent partial reads, all writes use atomic rename:

```python
def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    tmp.replace(path)  # Atomic on same filesystem
```

### Command Flow

1. **UI sends command:** Append to `commands.json` array
2. **3DCoat reads:** In `preprocess()`, read and clear `commands.json`
3. **3DCoat executes:** Run action, collect result
4. **3DCoat writes result:** Append to `results.json` array
5. **UI reads result:** Poll `results.json`, match by `command_id`

---

## Lifecycle

### Startup

1. User clicks `LKS_ExternalPanel_Launch.py` in 3DCoat
2. Script registers `LKSExtension` (if not already)
3. Script launches `lks_panel_app.py` via `coat.io.exec()`
4. External app checks dependencies, installs if needed
5. External app starts polling `scene_state.json`
6. Extension starts writing heartbeats

### Runtime

- Extension runs `preprocess()` every frame
- Every N frames, checks for commands and broadcasts state
- External app shows UI, sends commands on button clicks
- Results flow back via `results.json`

### Shutdown

**Option A: Close external window**
1. External app writes `shutdown.flag`
2. Extension sees flag, stops broadcasting
3. Extension deletes flag

**Option B: Run `LKS_ExternalPanel_Stop.py`**
1. Script writes `shutdown.flag`
2. External app polls for shutdown, exits
3. Extension cleans up

---

## Self-Healing Dependencies

The external panel implements a bootstrap sequence:

```python
# lks_panel_app.py - entry point
import sys
import subprocess

REQUIRED_PACKAGES = ["ttkbootstrap"]

def check_and_install():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        # Show minimal tk messagebox
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno(
            "Install Dependencies",
            f"The following packages are required:\n{', '.join(missing)}\n\nInstall now?"
        ):
            for pkg in missing:
                subprocess.run([sys.executable, "-m", "pip", "install", pkg])
            messagebox.showinfo("Restart Required", "Please run the panel again.")
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    check_and_install()
    # Now safe to import ttkbootstrap
    from lks_panel import main
    main()
```

---

## Example: List Scene Elements

**UI Action:**
```python
def on_refresh_click():
    send_command("list_elements", {})
```

**3DCoat Handler:**
```python
def handle_list_elements(params: dict) -> dict:
    elements = []
    root = coat.Scene.sculptRoot()
    if root:
        def collect(el):
            elements.append({
                "name": el.name(),
                "visible": el.isVisible(),
                "ghosted": el.isGhost(),
                "polycount": el.Volume().polycount() if el.Volume() else 0
            })
            return False  # continue
        root.iterateVisibleSubtree(collect)
    return {"elements": elements}
```

**UI Display:**
```python
def on_result_received(result: IPCResult):
    if result.success:
        for el in result.data["elements"]:
            self.tree.insert("", "end", values=(el["name"], el["polycount"]))
```

---

## Future Extensions

This architecture supports:
- **Custom tools:** Add new action handlers in extension
- **Real-time preview:** Increase poll rate for specific operations
- **Multiple panels:** Launch different UI scripts
- **Remote control:** IPC folder could be network-shared
- **Plugin system:** Dynamic handler registration

---

## Files Overview

```
UserProjects/
├── LKS_ExternalPanel_Launch.py    # Action: Launch panel
├── LKS_ExternalPanel_Stop.py      # Action: Stop panel
├── _external/                     # External panel code
│   ├── lks_panel_app.py          # Entry point with dep check
│   ├── lks_panel/                # Main panel module
│   │   ├── __init__.py
│   │   ├── app.py                # Tkinter application
│   │   ├── ipc_client.py         # IPC communication
│   │   └── widgets.py            # UI components
│   └── requirements.txt          # ttkbootstrap
├── _ipc/                          # IPC exchange folder
│   └── .gitkeep
└── _utils/
    ├── ipc_protocol.py           # Shared protocol
    ├── ipc_server.py             # Command handlers
    └── lks_extension.py          # cExtension subclass
```
