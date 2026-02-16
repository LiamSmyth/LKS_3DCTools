# LKS 3DCoat Tools

A comprehensive cModule for [3DCoat](https://3dcoat.com/) that provides powerful workflow automation, hotkey-mappable radial menus, and advanced sculpting tools.

<!-- Add your banner/demo image here -->
<!-- ![LKS Tools Banner](docs/images/banner.png) -->

## 🎯 Features

### 🎨 Radial Menu System
- **Hotkey-mappable radial menus** with unlimited customization
- Visual pie-navigation with cursor line feedback
- Save/load menu configurations from library
- Automatic action script generation for each menu
- Non-blocking Qt interface - sculpt while menu is open

<!-- Add radial menu demo GIF here -->
<!-- ![Radial Menu Demo](docs/images/radial_menu_demo.gif) -->

### ⚡ Smart Sculpting Actions
- **Decimate** - Reduce polycount by percentage or target density
- **Proxy Mode** - Toggle 16x decimated proxy for performance
- **Resample** - Remesh to half or uniform density
- **Mode Convert** - Switch between surface and voxel modes
- **Ghost/Visibility** - Isolate, invert, and toggle visibility states
- **Smart Tools** - Uniform density matching, safe remeshing with symmetry
- **Auto-Subdivide** - Dynamic subdivision control per brush

### 🔧 Workflow Tools
- **Autopo Integration** - One-click retopology with saved presets
- **Layer Management** - Consolidate, clean, and organize layers
- **Instance Tiling** - Create tile grids with instance support
- **ID Colors** - Generate random colors from parts for baking
- **Voxel Booleans** - Union, subtract, intersect operations

### ⌨️ Hotkey Editor
- Standalone hotkey editor with search and filtering
- Conflict detection and resolution
- Backup and restore functionality
- Export/import hotkey profiles

### 📦 Comprehensive UI Panel
- Tabbed interface: Tools, Radial Menu, Hotkeys, Outliner, Dev
- Collapsible sections with drag-to-reorder
- Non-blocking Qt design - viewport remains interactive
- Dark theme optimized for 3DCoat

<!-- Add panel screenshot here -->
<!-- ![LKS Panel](docs/images/panel_screenshot.png) -->

---

## 📥 Installation

### Requirements
- **3DCoat 2024+** (tested on 3DCoat-2025)
- **Python 3.8+** (3DCoat's embedded Python)
- **Windows** (may work on other platforms, untested)

### Download

**[Download Latest Release](https://github.com/LiamSmyth/LKS_3DCTools/releases/latest)** (LKS_3DCoat_cModule_vX.X.X.zip)

### Installation Steps

1. **Download** the latest `LKS_3DCoat_cModule_vX.X.X.zip`

2. **Extract** the `LKS/` folder to your 3DCoat cModules directory:
   ```
   Documents/3DCoat/UserPrefs/StdScripts/cModules/LKS/
   ```

   **Full path example:**
   ```
   C:\Users\YourName\Documents\3DCoat\UserPrefs\StdScripts\cModules\LKS\
   ```

3. **Restart 3DCoat**
   - The cModule will auto-load on startup
   - PySide6 dependency will be auto-installed if needed

4. **Verify Installation**
   - Go to **Scripts** menu → You should see **"LKS Tools Panel"**
   - Run it to open the main panel

5. **Optional: Register Hotkeys**
   - Open **3DCoat Preferences → Hotkeys**
   - Search for **"LKS"** or **"Radial"**
   - Assign hotkeys to your favorite actions

---

## 🚀 Quick Start

### Launch the Panel

**Scripts → LKS Tools Panel** (or assign a hotkey)

### Basic Workflow

1. **Configure Tools** (Tools tab)
   - Set up Autopo preferences
   - Configure dynamic subdivision settings
   - Apply settings to all brushes

2. **Create Radial Menu** (Radial Menu tab)
   - Click nodes to add/edit items
   - Assign actions to pie slices
   - Save to library
   - Menu auto-registers for hotkey assignment

3. **Assign Hotkeys** (Hotkey tab)
   - Click "Launch Hotkey Editor"
   - Search for your actions
   - Assign keys and resolve conflicts

### Common Actions

| Action | Description | Suggested Hotkey |
|--------|-------------|------------------|
| **LKS Tools Panel** | Main UI panel | `F12` |
| **Radial: My Menu** | Custom radial menu | `V` (hold) |
| **Decimate Half Selected** | Quick decimation | `Shift+D` |
| **Toggle Ghost Subtree** | Ghost/unghost hierarchy | `Alt+G` |
| **Toggle Proxy 16x** | Performance proxy mode | `Ctrl+P` |
| **Smart Density Match** | Uniform mesh density | `Shift+R` |

---

## 📂 Project Structure

```
LKS/
├── __init__.py              # Package marker
├── __onstartup.py          # Startup initialization (Qt setup)
├── LKS.py                  # Main cExtension + panel registration
├── requirements.txt        # PySide6 dependency
├── coat.pyi                # Type hints for IDE
│
├── actions/                # Action scripts (exposed to 3DCoat)
│   ├── Autopo_*.py
│   ├── Brush_*.py
│   ├── SculptObject_*.py
│   └── radial/             # Auto-generated radial menu actions
│
├── ops/                    # Operators (workflow orchestration)
│   ├── SculptObject_Decimate.py
│   ├── SculptObject_SetGhost.py
│   └── ...
│
├── utils/                  # Low-level utilities
│   ├── scene_api.py
│   ├── scope_utils.py
│   ├── coat_ui_utils.py
│   └── ui/                 # Qt widgets
│
├── ui/                     # Main UI components
│   ├── ui_main.py          # Main panel window
│   ├── ui_tab_*.py         # Tab implementations
│   └── ui_collapsible_*.py # Collapsible sections
│
├── generators/             # Code generators
│   └── action_generator.py # Radial menu script generator
│
└── data/                   # Data files
    ├── library/            # Saved configurations
    │   └── radial_menus/   # Menu library
    ├── defaults/           # Factory defaults
    └── schemas/            # JSON schemas
```

---

## 🎮 Usage Examples

### Example 1: Decimation Workflow

```python
# Manual approach (without LKS)
1. Select object
2. Geometry → Decimate
3. Set percentage to 50%
4. Click OK
5. Clean up empty layers
6. Re-select original

# With LKS - one hotkey
Shift+D  # Done!
```

### Example 2: Ghost Isolation

```python
# Manual approach
1. Select object
2. Geometry → Ghost/Unghost → Ghost all
3. Geometry → Ghost/Unghost → Unghost selected
4. ... complex multi-step process

# With LKS
Alt+Shift+G  # Toggle isolation
```

### Example 3: Radial Menu

<!-- Add radial menu usage example image -->
<!-- ![Radial Menu Usage](docs/images/radial_menu_usage.png) -->

1. Hold `V` (or your assigned key)
2. Move mouse toward desired action
3. Release to execute
4. Cursor line shows selection feedback

---

## ⚙️ Configuration

### Autopo Settings
Configure once, use everywhere:
- Polycount limits
- Voxelize options
- Auto-heal, symmetry, etc.

Settings persist across sessions in `data/state/lks_autopo_settings.json` (local only).

### Radial Menus
Create unlimited menus, each hotkey-mappable:
- Visual editor with pie layout
- Save/load from library
- Auto-generates action scripts
- Supports nested structures

### Brush Settings
Dynamic subdivision settings:
- Details level (0-8)
- Auto-subdivide toggle
- Remove stretching
- Apply to all brushes or per-brush

---

## 🛠️ Development

### For Users
This is a ready-to-use cModule. No development setup needed!

### For Developers
If you want to extend or modify:

1. Clone the repository
2. Symlink/junction to `StdScripts/cModules/LKS/`
3. Edit `.py` files
4. Use hot-reload via dev tools (no 3DCoat restart needed)

See [Contributing Guidelines](CONTRIBUTING.md) for more details.

---

## 🐛 Troubleshooting

### Panel Doesn't Appear
- Verify installation path: `Documents/3DCoat/UserPrefs/StdScripts/cModules/LKS/`
- Check 3DCoat console for errors (Windows → Show Console)
- Ensure PySide6 is installed (should auto-install on first load)

### Radial Menu Not Responding
- Ensure menu is registered (check Hotkey tab)
- Verify hotkey assignment in 3DCoat Preferences
- Try re-saving the menu from library

### Actions Not Working
- Verify you're in the correct room (most actions require Sculpt room)
- Check if object is selected (required for object-specific actions)
- Look for error messages in 3DCoat console

### Performance Issues
- Use Proxy Mode (16x decimate toggle) for heavy meshes
- Close the panel when not needed (Qt widget overhead)
- Reduce radial menu complexity (fewer items = faster)

---

## 📝 Changelog

### v1.0.0 (2026-02-15)
- Initial public release
- Radial menu system with hotkey mapping
- Comprehensive sculpting actions
- Hotkey editor integration
- Non-blocking Qt UI panel

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution
- Additional action scripts
- UI improvements
- Documentation
- Platform testing (Mac/Linux)
- Bug reports and feature requests

---

## 📄 License

**[Your License Here]** - Add LICENSE file to repository

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/LiamSmyth/LKS_3DCTools/issues)
- **Discussions:** [GitHub Discussions](https://github.com/LiamSmyth/LKS_3DCTools/discussions)
- **Email:** [Your contact email]

---

## 🙏 Acknowledgments

- Built for [3DCoat](https://3dcoat.com/) by Andrew Shpagin
- Inspired by the 3DCoat community's need for better workflow automation
- Uses PySide6 for Qt interface

---

## ⭐ Show Your Support

If this tool helps your workflow, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting features
- 📣 Sharing with other 3DCoat users

---

**Made with ❤️ for the 3DCoat community**
