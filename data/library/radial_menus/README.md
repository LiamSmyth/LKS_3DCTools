# Radial Menus Library

This folder contains your saved radial menu configurations. Each menu can be registered as a hotkey-mappable action in 3DCoat.

## 📁 What's Here

- **User-created menus**: JSON files with your custom radial menu layouts
- **Example menus**: Pre-made menu configurations for reference

## 🎯 How to Use

### 1. Create a Radial Menu

1. Open the **LKS Tools Panel** in 3DCoat
2. Go to the **"🎯 Radial"** tab
3. Build your menu structure:
   - Click **➕** to add root items
   - Click **➕📁** to add child items (submenus)
   - Configure each item's label, icon, and action

### 2. Save to Library

1. Click **💾 Save** in the Radial tab
2. Select **"📚 Library"** mode
3. Enter a filename (e.g., `sculpt_tools.json`)
4. Click **Save**

### 3. Register for Hotkey Mapping

**Option A: Auto-register (Recommended)**
- Ensure "Auto-register when saving to library" checkbox is checked
- Menu is automatically registered when you save to library

**Option B: Manual register**
- Click **✅ Register** button in the Radial tab
- Or use **🔄 Sync All** to register all library menus

### 4. Assign Hotkey

1. Open **3DCoat Preferences** (Ctrl+P)
2. Go to **Hotkeys** section
3. Find your menu in **Scripts → Radial: {YourMenuName}**
4. Assign a hotkey (e.g., `Q` for quick menu)

## 📝 Menu Config Format

```json
{
  "version": 2,
  "name": "My Menu",
  "items": [
    {
      "type": "branch",
      "label": "Action",
      "icon": "🔨",
      "description": "Description shown in tooltip",
      "angle": 0.0,
      "children": [
        {
          "type": "action",
          "label": "Submenu Item",
          "action": "$SomeCommand"
        }
      ]
    }
  ]
}
```

### Action Types

1. **3DCoat UI Command**: `"$CommandName"` (e.g., `"$Symmetry"`)
2. **Action Script**: `"actions/SculptObject_Decimate_Half_Selected.py"`
3. **Operator Function**: `"ops.SculptObject_Decimate.main"` (with optional `action_args`)

## 🔧 Troubleshooting

### Menu not appearing in Scripts menu
- Check registration status in Radial tab (should show green ✅)
- Click **🔄 Sync All** to force registration
- Restart 3DCoat to refresh menu system

### Can't assign hotkey to menu
- Menu must be **registered** first (click ✅ Register)
- Look for "Radial: {MenuName}" in Scripts menu
- If missing, run **Sync All** and restart 3DCoat

### "Already registered" but hotkey not working
- Restart 3DCoat (menu registration persists in XML files)
- Re-assign hotkey in Preferences

### Want to remove a menu
- Click **❌ Unregister** in Radial tab
- Delete the `.json` file from this folder
- Restart 3DCoat to clear menu item

## 📚 Example Menus

Check out the example menus in this folder:
- `example_menu.json` - Basic menu structure demo
- `LKS_Radial_V1.json` - Comprehensive LKS tools menu

You can load these as templates and customize them.

## 🔄 Registry Management

### Sync All Menus
Synchronizes all `.json` files in this library with the registration system:
- Registers new menus
- Unregisters deleted menus
- Regenerates action scripts for existing menus

**When to use:**
- After manually adding/removing `.json` files
- After script updates or reinstalls
- When registration state seems out of sync

### Auto-generated Files

**DO NOT edit these directly:**
- `actions/radial/LKS_RadialMenu_*.py` - Auto-generated action scripts
- `data/state/radial_menu_registry.json` - Registration state tracking

These are managed by the registry system and will be overwritten.

## 🎨 Icons

Emojis work great as icons:
- 🔨 Tools
- ⚙️ Settings
- 🎨 Paint
- 🔻 Reduce
- 📦 Pack
- ✨ Effect

Copy emojis from: https://emojipedia.org/

## 💡 Tips

1. **Organize by workflow**: Create separate menus for sculpting, retopo, painting
2. **Use submenus**: Keep root items to 4-8 for easy selection
3. **Consistent angles**: Use fixed angles (0°, 45°, 90°, etc.) for muscle memory
4. **Descriptive names**: Menu filenames become part of the hotkey name
5. **Test with Preview**: Use 👁️ Preview button before saving

## 🆘 Need Help?

- Check the main LKS documentation in `_docs/`
- Review example menus for syntax reference
- Open the Radial tab and hover tooltips for guidance

