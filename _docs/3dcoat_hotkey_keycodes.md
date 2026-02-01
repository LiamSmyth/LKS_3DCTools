# 3DCoat Hotkey Keycodes Reference

This document maps physical keyboard keys to 3DCoat's internal keycode representations
as stored in `Options_Hotkeys.xml`.

**Source:** Observations from actual 3DCoat-generated XML files.

**Last Updated:** 2026-01-27

---

## Key Encoding Rules

3DCoat uses several encoding strategies for different key types:

| Strategy | When Used | Example |
|----------|-----------|---------|
| Literal character | Most printable chars | `A`, `?`, `~`, `[` |
| Named key | Special keys | `ENTER`, `SPACE`, `Tab` |
| NUM prefix | Numpad keys | `NUM5`, `NUM*`, `NUM/` |
| XML entity | XML-breaking chars | `&lt` for `<`, `&gt` for `>` |
| Scancode hex | Unmappable keys | `key_DC` for `\` |
| `key_00` | Unassigned/None | No binding |

---

## Complete Keycode Reference

### Letters (A-Z)

All letters are stored as **uppercase single characters**.

| Physical Key | 3DCoat Code |
|--------------|-------------|
| A | `A` |
| B | `B` |
| C | `C` |
| ... | ... |
| Z | `Z` |

**Note:** Case is always uppercase regardless of Shift modifier.

---

### Numbers (Top Row)

Stored as **single digit characters**.

| Physical Key | 3DCoat Code |
|--------------|-------------|
| 1 | `1` |
| 2 | `2` |
| 3 | `3` |
| 4 | `4` |
| 5 | `5` |
| 6 | `6` |
| 7 | `7` |
| 8 | `8` |
| 9 | `9` |
| 0 | `0` |

---

### Numpad Keys

Prefixed with `NUM` OR uses scancode. Note naming inconsistency!

| Physical Key | 3DCoat Code | Notes |
|--------------|-------------|-------|
| Numpad 0 | `NUM0` | |
| Numpad 1 | `NUM1` | |
| Numpad 2 | `NUM2` | |
| Numpad 3 | `NUM3` | |
| Numpad 4 | `NUM4` | |
| Numpad 5 | `NUM5` | |
| Numpad 6 | `NUM6` | |
| Numpad 7 | `NUM7` | |
| Numpad 8 | `NUM8` | |
| Numpad 9 | `NUM9` | |
| Numpad / | `NUM/` | No underscore |
| Numpad * | `NUM*` | No underscore |
| Numpad - | `NUM_MINUS` | Has underscore! ✅ Confirmed |
| Numpad + | `NUM_PLUS` | Has underscore! ✅ Confirmed |
| Numpad Enter | - | ⛔ UNMAPPABLE |
| Numpad . | `key_6E` | Uses scancode! 0x6E = VK_DECIMAL ✅ Confirmed |

**⚠️ Inconsistency:** 
- `NUM_MINUS` and `NUM_PLUS` use underscore
- `NUM/` and `NUM*` don't use underscore  
- `Numpad .` uses scancode format instead of `NUM` prefix!

---

### Function Keys

Format: `F` followed by number.

| Physical Key | 3DCoat Code |
|--------------|-------------|
| F1 | `F1` |
| F2 | `F2` |
| ... | ... |
| F9 | `F9` |
| F10 | `F10` |
| F11 | `F11` |
| F12 | `F12` |

---

### Special/Named Keys

Full name, usually uppercase (but not always consistent).

| Physical Key | 3DCoat Code | Notes |
|--------------|-------------|-------|
| Enter | `ENTER` | Main keyboard Enter |
| Escape | `ESC` | |
| Space | `SPACE` | |
| Tab | `Tab` | Mixed case! |
| Backspace | - | ⛔ UNMAPPABLE - reserved for Clear |
| Delete | `DELETE` | Full word ✅ Confirmed |
| Insert | `INS` | Abbreviated ✅ Confirmed |
| Home | `HOME` | ✅ Confirmed |
| End | - | ⛔ UNMAPPABLE |
| Page Up | `PGUP` | ✅ Confirmed |
| Page Down | `PGDN` | ✅ Confirmed |

**⚠️ Inconsistency:** `DELETE` is full word but `INS` is abbreviated!

---

### Arrow Keys

Capitalized names.

| Physical Key | 3DCoat Code |
|--------------|-------------|
| Up Arrow | `Up` |
| Down Arrow | `Down` |
| Left Arrow | `Left` |
| Right Arrow | `Right` |

---

### Symbol Keys (Stored Literally)

These characters don't conflict with XML and are stored as-is.

| Physical Key | 3DCoat Code | Notes |
|--------------|-------------|-------|
| ` (backtick/grave) | `` ` `` | Below Esc |
| ~ (tilde) | `~` | Shift+` |
| - (minus) | `-` | Top row |
| = (equals) | `=` | Assumed |
| + (plus) | `+` | Shift+= |
| [ | `[` | |
| ] | `]` | |
| \ (backslash) | `key_DC` | See scancode section |
| ; | `;` | |
| ' (apostrophe) | `'` | |
| , (comma) | `&lt` | ⚠️ Stored as shifted char! See below |
| . (period) | `&gt` | ⚠️ Stored as shifted char! See below |
| / (slash) | `/` | Assumed |
| ? | `?` | Shift+/ |

---

### XML-Encoded Keys (CRITICAL)

These characters have special meaning in XML and MUST be entity-encoded.

| Physical Key | 3DCoat Code | Why Encoded |
|--------------|-------------|-------------|
| < (less than) | `&lt` | Opens XML tags |
| > (greater than) | `&gt` | Closes XML tags |

**⚠️ Note:** The trailing semicolon is often missing (`&lt` not `&lt;`).
Most XML parsers handle this gracefully, but it's technically malformed.

**NEVER store these literally** - `<Code><</Code>` is invalid XML!

---

### ⚠️ CRITICAL: Shifted-Character Storage Pattern

**3DCoat stores the SHIFTED character for `,` and `.` keys, NOT the base character!**

For keys where the shifted variant is `<` or `>`, 3DCoat stores the shifted character:

| Physical Key | What You Press | Code in XML | Shift Field | Notes |
|--------------|----------------|-------------|-------------|-------|
| Period key | `.` alone | `&gt` (=`>`) | `false` | ✅ Confirmed |
| Period key | `>` (Shift+.) | `&gt` (=`>`) | `true` | ✅ Confirmed |
| Comma key | `,` alone | `&lt` (=`<`) | `false` | ✅ Confirmed |
| Comma key | `<` (Shift+,) | `&lt` (=`<`) | `true` | ✅ Confirmed |

**Conversion logic for hotkey editor:**

```python
# READING from XML:
if code == ">" and not shift:  # &gt with Shift=false
    display_key = "."          # User pressed period
elif code == "<" and not shift:  # &lt with Shift=false  
    display_key = ","          # User pressed comma

# WRITING to XML:
if user_key == ".":
    code = "&gt"  # Store as >
    shift = False
elif user_key == ",":
    code = "&lt"  # Store as <
    shift = False
```

---

### Scancode Format (key_XX)

For keys that can't be represented as simple characters or names,
3DCoat uses Windows virtual key scancodes in hex.

| Physical Key | 3DCoat Code | Scancode (Hex) | Scancode (Dec) | VK Constant |
|--------------|-------------|----------------|----------------|-------------|
| (Unassigned) | `key_00` | 0x00 | 0 | - |
| Backslash \ | `key_DC` | 0xDC | 220 | VK_OEM_5 |
| Numpad . | `key_6E` | 0x6E | 110 | VK_DECIMAL |
| ??? | `key_T` | ??? | ??? | Unknown - needs investigation |

**Reference:** Windows Virtual Key Codes
- `0xDC` (220) = `VK_OEM_5` = Backslash on US keyboard
- `0x6E` (110) = `VK_DECIMAL` = Numpad decimal point

**Note:** `key_T` was observed but the pattern is unclear - may be a special case or bug.

---

## Modifier Keys

Modifiers are stored as separate boolean fields, NOT in the Code field.

```xml
<Ctrl>true</Ctrl>
<Alt>false</Alt>
<Shift>false</Shift>
```

The `Code` field contains ONLY the base key.

**Example:** Ctrl+Shift+S is:
```xml
<Code>S</Code>
<Ctrl>true</Ctrl>
<Alt>false</Alt>
<Shift>true</Shift>
```

---

## Room Scope

Determines which room(s) the hotkey is active in.

| Value | Meaning | Example IDs |
|-------|---------|-------------|
| (empty) | **Global** - works in all rooms | UNDO, REDO, VIEW_*, Execute |
| `Voxels` | Sculpt room only | `preset_item_*`, `select_*`, Pick_layer |
| `Retopo` | Retopo room only | ⚠️ Not yet observed |
| `Paint` | Paint room only | ⚠️ Not yet observed |
| `UV` | UV room only | ⚠️ Not yet observed |
| `Render` | Render room only | ⚠️ Not yet observed |

---

## UserDefined Field

Indicates whether the hotkey has been modified from defaults.

| Value | Meaning | Notes |
|-------|---------|-------|
| `0` | **Stock/default** hotkey | Original 3DCoat binding |
| `1` | **User-modified** hotkey | Even keeping same key but editing sets this to 1 |

---

## AllowStack Field

| Value | Meaning |
|-------|---------|
| `false` | Normal exclusive hotkey - only one action per key combo |
| `true` | Can stack with other hotkeys (multiple actions on same key) |

**Note:** All observed entries show `false`. Stacking behavior is rare/advanced.

---

## ID Naming Patterns

The `<ID>` field follows several patterns depending on the command type:

| Pattern | Example IDs | Meaning |
|---------|-------------|---------|
| `UPPER_SNAKE_CASE` | `UNDO`, `VIEW_FRONT`, `MENU_TOGGLE_FREEZE_VIEW` | Built-in system commands |
| `CamelCase` | `QuickPanel`, `ToggleUI`, `CameraUndo`, `ToggleFullscreen` | Built-in actions |
| `preset_item_<Name>` | `preset_item_LKS ClayBuildup Square V1` | **Brush preset hotkeys** |
| `select_<Path>` | `select_UserPrefs/Models/RetopoModels/Cube.obj` | **Model/primitive selection** |
| `VoxTreeBranch.select.<Name>` | `VoxTreeBranch.select.Volume5` | **Vox tree item selection** |
| `Namespace::Action` | `PolynomeBackground::plForward`, `PolynomeBackground::plBack` | Namespaced internal commands |
| `lower_snake_case` | `rotate_around_custom_point` | Some built-in actions |

**Key insight for hotkey editor:**
- IDs starting with `preset_item_` are brush presets
- IDs starting with `select_` are model/primitive shortcuts
- IDs with `::` are namespaced subsystem commands

---

## Common Modifier Combinations

Observed modifier patterns and their typical uses:

| Modifier Combo | Example Commands | Typical Use |
|----------------|------------------|-------------|
| (none) | VIEW_SHADED (5), Pen (T), SYMMETRY (S) | Quick access, view modes |
| Ctrl | UNDO, REDO, COPY, PASTE, SAVE_FILEFAST | Standard app shortcuts |
| Shift | NAVIFRAME, Toggle_vox_visibility | Alternate/extended actions |
| Ctrl+Shift | SAVE_INC, InvertHide, MENU_INVERT_FREEZE | Power user variants |
| Alt | CameraUndo, CameraRedo, SMOOTH_STROKE | Camera/alternate tools |
| Ctrl+Alt | SAVE_FILE (Save As) | Less common combinations |
| Alt+Shift | EditTimelapseSettings, UploadToSketchFab | Specialty features |

---

## Writing Valid Hotkey XML

### Do's ✅

```xml
<!-- Letters: uppercase -->
<Code>A</Code>

<!-- Symbols: literal -->
<Code>?</Code>
<Code>~</Code>
<Code>[</Code>

<!-- Special keys: named -->
<Code>ENTER</Code>
<Code>SPACE</Code>
<Code>PGUP</Code>

<!-- < and > : entity-encoded -->
<Code>&lt</Code>
<Code>&gt</Code>

<!-- Numpad: NUM prefix -->
<Code>NUM5</Code>
<Code>NUM*</Code>

<!-- Unassigned: key_00 -->
<Code>key_00</Code>
```

### Don'ts ❌

```xml
<!-- WRONG: lowercase letters -->
<Code>a</Code>

<!-- WRONG: literal < or > (breaks XML) -->
<Code><</Code>
<Code>></Code>

<!-- WRONG: double-escaped entities -->
<Code>&amp;lt;</Code>

<!-- WRONG: full entity with semicolon in display -->
<!-- (Actually &lt; works but 3DCoat writes &lt) -->
```

---

## Conversion Tables for Hotkey Editor

### Qt Key to 3DCoat Code

When building a hotkey editor, map Qt key events to 3DCoat codes:

```python
QT_TO_3DCOAT: dict[int, str] = {
    # Letters (Qt.Key_A = 65)
    Qt.Key_A: "A",
    Qt.Key_B: "B",
    # ... etc
    
    # Numbers
    Qt.Key_0: "0",
    Qt.Key_1: "1",
    # ... etc
    
    # Function keys
    Qt.Key_F1: "F1",
    Qt.Key_F2: "F2",
    # ... etc
    
    # Special
    Qt.Key_Return: "ENTER",
    Qt.Key_Enter: "ENTER",  # Numpad enter
    Qt.Key_Escape: "ESC",
    Qt.Key_Space: "SPACE",
    Qt.Key_Tab: "Tab",
    Qt.Key_Backspace: "BACK",
    Qt.Key_Delete: "DEL",
    Qt.Key_Insert: "INS",
    Qt.Key_Home: "HOME",
    Qt.Key_End: "END",
    Qt.Key_PageUp: "PGUP",
    Qt.Key_PageDown: "PGDN",
    
    # Arrows
    Qt.Key_Up: "Up",
    Qt.Key_Down: "Down",
    Qt.Key_Left: "Left",
    Qt.Key_Right: "Right",
    
    # Symbols that need entity encoding
    Qt.Key_Less: "&lt",      # <
    Qt.Key_Greater: "&gt",   # >
    
    # Numpad
    Qt.Key_multiply: "NUM*",  # Numpad *
    Qt.Key_division: "NUM/",  # Numpad /
    # Note: Qt numpad numbers need special handling
}
```

### 3DCoat Code to Display String

For showing user-friendly names:

```python
CODE_TO_DISPLAY: dict[str, str] = {
    "key_00": "(None)",
    "&lt": "<",
    "&gt": ">",
    "ENTER": "Enter",
    "ESC": "Escape",
    "SPACE": "Space",
    "PGUP": "Page Up",
    "PGDN": "Page Down",
    "NUM_MINUS": "Num -",
    "NUM*": "Num *",
    "NUM/": "Num /",
    # etc.
}
```

---

## Unknown/Untested Keys

These keys have not been tested. Please update this doc when observed:

- [ ] Numpad Enter (likely `NUM_ENTER`?)
- [ ] Numpad 0 (likely `NUM0` - confirm)
- [ ] Home
- [ ] End  
- [ ] Backspace (likely `BACK`?)
- [ ] Caps Lock
- [ ] Scroll Lock
- [ ] Pause/Break
- [ ] Print Screen
- [ ] Media keys
- [ ] International keyboard layouts
- [x] ~~Numpad +~~ → `NUM_PLUS` ✅
- [x] ~~Numpad .~~ → `key_6E` ✅
- [x] ~~Page Down~~ → `PGDN` ✅
- [x] ~~Delete~~ → `DELETE` ✅
- [x] ~~Insert~~ → `INS` ✅
- [x] ~~F1~~ → `F1` ✅

### Mystery Keys to Investigate

- `key_T` - What physical key produces this? Seen in `preset_item_LKS Vox SoftBuildup V1`

---

## Adding New Observations

When you discover a new keycode:

1. Bind the key in 3DCoat's UI (Edit > Customize Hotkeys)
2. Close 3DCoat (saves the XML)
3. Open `UserPrefs/Preferences/Options_Hotkeys.xml`
4. Find the new entry and note the `<Code>` value
5. Update this document

---

## Related Files

- `utils/hotkey_utils.py` - Hotkey parsing and serialization
- `utils/hotkey_editor/` - Qt-based hotkey editor
- `UserPrefs/Preferences/Options_Hotkeys.xml` - 3DCoat's hotkey file
