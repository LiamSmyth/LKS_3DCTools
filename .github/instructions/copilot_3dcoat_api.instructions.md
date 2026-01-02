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

## �📋 Adding to This Document

**Only add entries that are:**
1. ✅ Verified to be true (tested or confirmed in coat.pyi)
2. ✅ Non-obvious behavior that could trip someone up
3. ✅ Documents what EXISTS and how to use it correctly

**Do NOT add:**
- ❌ References to methods/classes that don't exist
- ❌ Unverified assumptions
- ❌ Standard behavior that's obvious from coat.pyi
