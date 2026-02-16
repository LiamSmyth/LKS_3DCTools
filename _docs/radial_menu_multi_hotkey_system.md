# Multiple Hotkey-Mappable Radial Menus

## 🎉 What's New

You can now create **multiple radial menus**, each with its own hotkey! Previously, there was only one radial menu. Now you can:

- Create custom radial menus for different workflows (sculpting, retopo, painting, etc.)
- Save each menu to the library
- Register each menu as a separate hotkey-mappable action
- Assign different hotkeys to different menus

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  User Creates Menu → Saves to Library → Auto-Registered        │
│  ↓                                                              │
│  Action Script Generated → Appears in 3DCoat Scripts Menu      │
│  ↓                                                              │
│  User Assigns Hotkey → Press Hotkey → Menu Opens!             │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Library Storage**: `data/library/radial_menus/my_menu.json`
2. **Action Script**: `actions/radial/LKS_RadialMenu_MyMenu.py` (auto-generated)
3. **Menu Registration**: 3DCoat menu item `LKS_Radial_MyMenu`
4. **Registry State**: `data/state/radial_menu_registry.json` (tracks registration)

## 📚 Key Components

### New Files Created

| File | Purpose |
|------|---------|
| `generators/action_generator.py` | Template-based action script generation (reusable) |
| `utils/radial_menu_registry.py` | Core registry - uses action_generator, manages registration |
| `utils/radial_menu_cleanup.py` | Cleanup orphaned scripts and stale XML files |
| `actions/radial/` | Folder for auto-generated action scripts |
| `actions/radial/README.md` | Documentation for the radial actions folder |
| `data/library/radial_menus/README.md` | User guide for library management |

### Modified Files

| File | Changes |
|------|---------|
| `ui/ui_tab_radial_menu.py` | Added registration controls, auto-register checkbox, status display |
| `.github/instructions/copilot_codebase_router.instructions.md` | Documented new system |

## 🎯 Usage

### Quick Start

1. **Open LKS Panel** → Go to **"🎯 Radial"** tab
2. **Build your menu** using ➕ and ➕📁 buttons
3. **Click "💾 Save"** → Select "📚 Library" → Enter name → Save
4. **Check "Auto-register when saving to library"** is enabled (default)
5. **✅ Menu is now registered!** Status will show green checkmark
6. **Assign hotkey**: 3DCoat Preferences → Hotkeys → Scripts → "Radial: {YourMenuName}"

### Registration Controls (in Radial Tab)

- **Status Label**: Shows registration status (✅ registered or ❌ not registered)
- **Auto-register checkbox**: Automatically register when saving to library (recommended)
- **✅ Register button**: Manually register current menu
- **❌ Unregister button**: Remove menu from Scripts menu
- **🔄 Sync All button**: Sync all library menus with registry (useful after manual edits)

### Example Workflow: Multiple Menus

```python
# Create 3 menus for different workflows:
# 1. "sculpt_tools.json" - Decimation, subdivision, density tools
# 2. "visibility_tools.json" - Ghost, hide, isolate operations  
# 3. "export_tools.json" - Export, scale, save operations

# Each gets its own hotkey:
# - Q → Sculpt Tools (assigned in 3DCoat preferences)
# - W → Visibility Tools
# - E → Export Tools
```

## 🔧 Technical Details

### Action Script Generation (New: `generators/action_generator.py`)

Action script generation is now abstracted into a reusable generator module:

```python
from generators.action_generator import (
    generate_radial_menu_script,
    write_action_script,
    sanitize_identifier,
)

# Generate from template
script_content = generate_radial_menu_script(
    config_filename="my_menu.json",
    display_name="My Menu"
)

# Write to disk
script_path = write_action_script(
    output_dir=Path("actions/radial"),
    script_name="LKS_RadialMenu_MyMenu.py",
    content=script_content
)
```

**Benefits:**
- Reusable for other dynamic action generation needs
- Template-based with support for custom templates
- Identifier sanitization utilities (PascalCase, snake_case, kebab-case)
- Centralized action script generation logic

### Menu ID Generation

Menu filename `my_cool_menu.json` becomes:
- **Menu ID**: `LKS_Radial_MyCoolMenu` (PascalCase, alphanumeric only)
- **Action Script**: `LKS_RadialMenu_MyCoolMenu.py`
- **Display Name**: "Radial: My Cool Menu" (in Scripts menu)

### Registry State File

`data/state/radial_menu_registry.json`:
```json
{
  "sculpt_tools.json": "Sculpt Tools",
  "visibility_tools.json": "Visibility Tools"
}
```

Maps menu filenames to their display names.

### Auto-Generated Action Scripts

Each registered menu gets a wrapper script like:

```python
"""Show radial menu: Sculpt Tools"""
from utils.action_base import action

@action
def main() -> None:
    from utils.radial_menu_config import load_menu_config
    from utils.ui.widgets import get_manager
    
    config_path = "data/library/radial_menus/sculpt_tools.json"
    items = load_menu_config(config_path)
    get_manager().show_menu(items)

main()
```

## 🔄 Sync and Cleanup

### When to Sync

Run **🔄 Sync All** when:
- Manually adding/removing `.json` files in library
- After addon updates or reinstalls
- Registry state seems out of sync
- Action scripts are missing or corrupted

### Cleanup Operations

```python
from utils.radial_menu_cleanup import cleanup_all, reset_all_menus

# Clean up orphaned files
cleanup_all()

# DESTRUCTIVE: Reset everything (requires confirm=True)
reset_all_menus(confirm=True)
```

## ⚠️ Important Notes

### DO NOT Edit Manually

- **Action scripts** in `actions/radial/` are auto-generated - edits will be overwritten
- **Registry state** in `data/state/radial_menu_registry.json` is managed by code

### Menu XML Persistence

3DCoat persists menu items as XML files in:
```
Documents/3DCoat/UserPrefs/Scripts/ExtraMenuItems/LKS_Radial_*.xml
```

These files persist even after unregistering. **Restart 3DCoat** to fully clear unregistered menus.

### Menu Naming

- Use descriptive filenames (they become part of hotkey name)
- Avoid special characters (use underscores or hyphens)
- Keep names concise (shown in menu)

## 🎨 Design Tips

### Menu Organization

- **4-8 root items**: Easy to select without overwhelming
- **Submenus for variants**: Group related actions (e.g., Decimate → 50%, 25%, 16x)
- **Fixed angles**: Use 0°, 45°, 90°, 135°, etc. for muscle memory
- **Emoji icons**: Visually distinctive and fun (🔻 🔄 ⚙️ 📏 👁️)

### Workflow-Specific Menus

```
sculpt_tools.json       # Decimation, subdivision, remesh
visibility_tools.json   # Ghost, hide, isolate, show
export_tools.json       # Scale, save, export operations  
brush_tools.json        # Details level, auto-subdiv settings
retopo_tools.json       # Autopo, convert, baking
```

Assign hotkeys based on usage frequency.

## 🐛 Troubleshooting

### Menu not in Scripts menu
1. Check registration status (should be green ✅)
2. Click **🔄 Sync All**
3. Restart 3DCoat

### Can't assign hotkey
1. Ensure menu is registered (green ✅ status)
2. Look in: Scripts → "Radial: {YourMenuName}"
3. Restart 3DCoat if missing

### "Already registered" but status shows ❌
1. Registry state is stale
2. Click **🔄 Sync All** to refresh
3. If still broken, use cleanup utilities

### Duplicate menus in Scripts menu
1. Old XML files from previous registrations
2. Run `cleanup_menu_xml_files()` or restart 3DCoat

## 📖 Documentation

- **User Guide**: [data/library/radial_menus/README.md](data/library/radial_menus/README.md)
- **Codebase Router**: [.github/instructions/copilot_codebase_router.instructions.md](.github/instructions/copilot_codebase_router.instructions.md)
- **Registry API**: `utils/radial_menu_registry.py` (docstrings)

## 🎊 Summary

You now have a complete system for managing multiple hotkey-mappable radial menus:

- ✅ Create unlimited custom menus
- ✅ Save/load from library
- ✅ Auto-register as hotkey-mappable actions
- ✅ Assign different hotkeys to different menus
- ✅ Sync and cleanup utilities
- ✅ Full UI integration in panel

Enjoy your custom radial menus! 🎉
