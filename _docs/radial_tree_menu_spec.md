# Radial Tree Menu Specification

## Overview

A **radial menu** (also known as a "marking menu" or "pie menu") is a circular context menu that appears around the mouse cursor. Instead of clicking precise buttons, users move the mouse in a **direction** to select an action. This is faster and more ergonomic than traditional menus for frequent operations.

A **radial tree menu** extends this concept with nested submenus: selecting a direction can reveal child actions, allowing hierarchical organization while maintaining gesture-based selection.

---

## Core UX Principles

### 1. Anchor Point

- When the menu is invoked, the cursor's current position becomes the **anchor point**
- The radial menu appears centered on this anchor
- All angle calculations are relative to the anchor
- Submenus have their own anchors (the branch node position)

### 2. Direction-Based Selection (Not Precision Clicking)

- User does NOT need to click on a button
- User moves mouse in a **direction** from anchor
- Selection is based on **angle from anchor**, not cursor position over a widget
- Only **leaf nodes** (nodes without children) participate in angle-based selection
- **Branch nodes** (nodes with children) require actual mouse hover to enter

### 3. Dead Zone

- A circular area around the anchor point where NO selection occurs
- Prevents accidental selection when the menu first appears
- Typical radius: 40-60 pixels
- Cursor must exit dead zone before any leaf node can be highlighted
- When cursor is in dead zone: no item is highlighted, releasing key invokes nothing

**Submenu Dead Zone ("Donut Hole"):**
- Submenus also have a dead zone around their anchor (the exit node)
- This allows users to exit the submenu without accidentally invoking a leaf
- Pizza slices start outside this inner dead zone radius

### 3. Key Hold → Move → Release Pattern

```
1. User HOLDS trigger key (e.g., Q)
2. Radial menu appears centered on cursor position
3. User MOVES mouse toward desired action (sector highlights)
4. User RELEASES trigger key
5. Highlighted action is invoked (if any)
6. Menu disappears
```

This is faster than click-to-open, click-to-select because:
- Single key hold replaces two clicks
- Direction can be selected during the hold motion
- Muscle memory develops quickly (expert users don't even look)

**Key Release Behavior:**
- If cursor is over a **highlighted leaf node** → invoke that action
- If cursor is in **dead zone** → nothing happens, menu closes
- If cursor is over **branch node** (Phase 2) → nothing happens, menu closes
- If cursor is over **exit node** (Phase 2) → nothing happens, menu closes
- Menu **always** closes on key release (user must hold key entire time)

### 4. Pizza Slice Regions (Angle-Based Selection)

Leaf nodes are selected via invisible "pizza slice" regions:

- Each leaf node owns an angular region around its position
- Slice boundaries are the **bisecting angles** between adjacent nodes
- Branch nodes are **excluded** from slice ownership (they require hover)
- When cursor exits dead zone, the slice containing the cursor angle highlights that leaf

```
Example: 3 leaf nodes at 0°, 120°, 240° (evenly spaced)

         Leaf A (0°)
            │
     ───────┼───────  ← slice boundary at 60°
           ╱ ╲
          ╱   ╲
         ╱     ╲
    Leaf C     Leaf B
    (240°)     (120°)

Slice A: 300° to 60° (owns top region)
Slice B: 60° to 180°
Slice C: 180° to 300°
```

### 5. Node Positioning

**Default (unspecified angles):**
- Nodes distributed evenly around the anchor
- First node at 12 o'clock (0° / "Up")
- Subsequent nodes proceed clockwise

**Explicit positioning:**
- Nodes can specify angle: `0°` = 12 o'clock, `90°` = 3 o'clock (right), etc.
- Named directions: `"Up"`, `"Right"`, `"Down"`, `"Left"`, `"UpRight"`, etc.
- Mixed: some nodes positioned, others fill remaining space evenly

### 6. Visual Feedback

| State | Visual |
|-------|--------|
| Dead zone | Dimmed/subtle center circle |
| No selection (in dead zone) | All nodes equally styled, none highlighted |
| Leaf highlighted | That node has accent color/glow |
| Branch node | Small arrow/chevron indicator |
| Branch node hovered | Highlight + "ready to enter" state |

---

## Radial Menu (Phase 1) vs Radial Tree Menu (Phase 2)

### Phase 1: Simple Radial Menu

- Single level of 4-8 sectors arranged radially
- Each sector = one action
- Key hold shows menu, release invokes
- No nesting

```
        [Action 1]
           ↑
[Action 4] ● [Action 2]    (● = dead zone center)
           ↓
        [Action 3]
```

### Phase 2: Radial Tree Menu

- **Branch nodes** have children (submenu items)
- **Leaf nodes** have no children (invoke action directly)
- Hovering over a branch node for a short dwell time **enters** the submenu
- Submenu appears with branch node position as new anchor
- A **"string"** (dotted line) traces from current cursor back through anchors
- Deeper nesting possible (but 2 levels is practical max)

**Submenu Visibility:**
- When entering a submenu, **only that submenu's nodes are visible**
- Parent menu nodes are kept in memory but completely hidden/deactivated
- User only sees UI elements that actively affect behavior
- Keeps the interface clean and focused

**Exit Node:**
- When a branch node is entered, it becomes an **exit node** in the submenu
- Exit node displays "✕" or "Exit" indicator at the submenu anchor position
- To exit submenu: hover over exit node + dwell time (same as entering a branch)
- This prevents accidental exits when passing over the exit zone
- Cursor must **leave and re-enter** the exit zone to trigger dwell timer

**Dwell Timer Rules:**
- Timer starts when cursor enters branch/exit node hover region
- Timer resets if cursor leaves the region before dwell completes
- Timer restarts fresh on re-entry
- Typical dwell time: 150-300ms

```
Initial state:               After entering "Booleans" branch:
                             
    [Decimate]                         [Subtract]
        ↑                                  ↑
[Ghost] ●───[Booleans→]        ●╌╌╌╌╌╌╌●───[Intersect]
        ↓       ▲              root   bool    ↓
    [Resample]  │                    anchor [Union]
                │
         (branch node,               (string traces back to root)
          requires hover             (re-hover Booleans to exit)
          to enter)
```

### The "String" Visualization

- A dotted/dashed line from **current cursor** back to **current anchor**
- When entering a submenu, string is "pinned" at the branch node
- Multiple segments form if nested: `cursor ╌╌ branch2 ╌╌ branch1 ╌╌ root`
- Provides visual reference for navigation path
- Helps user understand where to move to exit submenus

---

## Integration with LKS

### Trigger Mechanism

1. **Action Script Entry Point**: Create `actions/LKS_RadialMenu_Show.py`
2. **Hotkey Assignment**: User assigns hotkey to this action in 3DCoat preferences
3. **Alternative**: LKS panel button or menu item for testing

This approach allows:
- Standard 3DCoat hotkey remapping
- No need for custom global key hooks initially
- Works within existing action infrastructure

### Menu Content

Phase 1: Hardcoded curated list of common actions:
```python
MENU_ITEMS = [
    MenuItem(label="Decimate 50%", action=lambda: decimate(50)),
    MenuItem(label="Resample Half", action=resample_half),
    MenuItem(label="Ghost Toggle", action=ghost_toggle),
    MenuItem(label="To Surface", action=to_surface),
    # etc.
]
```

Future: User-configurable menu builder (JSON config or Qt-based editor).

---

## Technical Architecture

### File Structure

```
utils/ui/widgets/
├── radial_menu.py           # Phase 1: RadialMenuWidget + RadialMenuItem
├── radial_menu_manager.py   # Singleton manager, event handling
└── radial_tree_menu.py      # Phase 2: Tree extension

actions/
└── LKS_RadialMenu_Show.py   # Action to trigger menu

data/
└── radial_menu_config.json  # Future: user menu configuration
```

### Core Classes

```python
@dataclass
class RadialMenuItem:
    """Single menu item in a radial sector."""
    label: str
    action: Callable[[], None]
    icon: str | None = None          # Emoji or icon path
    children: list[RadialMenuItem] | None = None  # Phase 2

class RadialMenuWidget(QWidget):
    """Frameless overlay widget displaying radial sectors."""
    # Uses Qt.ToolTip | Qt.FramelessWindowHint pattern
    # Paints sectors via QPainter
    # Tracks mouse for sector highlighting
    # Emits signal on selection

class RadialMenuManager:
    """Singleton managing menu lifecycle."""
    # Shows menu at cursor position
    # Handles key release detection
    # Invokes selected action
```

### Geometry Math

Selection uses polar coordinates with pizza slice regions:

```python
def cursor_to_angle(cursor: QPoint, anchor: QPoint) -> float:
    """Return angle in degrees, 0° = up (12 o'clock), clockwise."""
    dx = cursor.x() - anchor.x()
    dy = cursor.y() - anchor.y()
    # atan2 gives angle from positive X axis, counter-clockwise
    # We want angle from negative Y axis (up), clockwise
    angle = math.atan2(dx, -dy)  # Note: (dx, -dy) not (dy, dx)
    angle_deg = math.degrees(angle)
    if angle_deg < 0:
        angle_deg += 360
    return angle_deg

def get_highlighted_leaf(
    cursor: QPoint,
    anchor: QPoint,
    leaf_angles: list[float],  # Sorted angles of leaf nodes only
) -> int | None:
    """Return index of highlighted leaf, or None if in dead zone."""
    dx = cursor.x() - anchor.x()
    dy = cursor.y() - anchor.y()
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < DEAD_ZONE_RADIUS:
        return None  # In dead zone, no selection
    
    cursor_angle = cursor_to_angle(cursor, anchor)
    
    # Find which pizza slice contains cursor_angle
    # Slice boundaries are midpoints between adjacent leaf angles
    for i, angle in enumerate(leaf_angles):
        next_angle = leaf_angles[(i + 1) % len(leaf_angles)]
        # Calculate slice boundaries (bisecting angles)
        lower = (leaf_angles[i - 1] + angle) / 2 if i > 0 else ...
        upper = (angle + next_angle) / 2
        if lower <= cursor_angle < upper:
            return i
    return None
```

**Key points:**
- Branch nodes are **not in `leaf_angles`** — they don't own pizza slices
- Slice boundaries are bisecting angles between adjacent leaves
- 0° = 12 o'clock (up), angles increase clockwise

---

## Standalone Testing

The radial menu can be tested outside 3DCoat using 3DCoat's embedded Python:

```powershell
# Find 3DCoat's Python (same method as hotkey editor standalone)
$python = "C:\Program Files\3DCoat-2025\Python\python.exe"  # Or discovered path

# Run test script
& $python -c "from utils.ui.widgets.radial_menu import test_standalone; test_standalone()"
```

The `test_standalone()` function:
1. Creates a QApplication
2. Shows RadialMenuWidget at screen center
3. Prints selected sector to console
4. Exits on Escape or selection

---

## Configuration (Future)

```json
{
  "trigger_key": "Q",
  "dead_zone_radius": 50,
  "menu_radius": 150,
  "sectors": [
    {"label": "Decimate", "action": "ops.SculptObject_Decimate.main", "children": [
      {"label": "50%", "action": "..."},
      {"label": "75%", "action": "..."}
    ]},
    {"label": "Resample", "action": "ops.SculptObject_Resample.main"},
    ...
  ]
}
```

---

---

## Out of Scope (For Now)

### Screen Edge Clipping

If the anchor is near a screen edge, menu nodes may be clipped. Addressing this would require complex dynamic repositioning (e.g., where does a node at 2 o'clock go when the right edge clips?). 

**Decision:** Ignore for initial implementation. Users should invoke menu away from screen edges. May revisit in a future iteration.

---

## References

- **Maya Marking Menus**: The gold standard for radial menus in 3D software
- **Blender Pie Menus**: Similar concept, built into Blender's Python API
- **Krita Pie Menu**: Art software implementation

---

## Document History

| Date | Change |
|------|--------|
| 2026-02-01 | Initial specification |
