---
applyTo: '**'
---

# 3DCoat Python API Reference

This document captures known 3DCoat API patterns, magic strings, and behaviors discovered through experimentation. Update this document whenever new API knowledge is discovered.

---

## Core Modules

### `coat` Module Structure

```python
import coat

coat.ui          # UI operations, commands, room switching
coat.Scene       # Scene access, object hierarchy
coat.settings    # Persistent application settings
coat.io          # File I/O, JSON, timing
coat.dialog      # Dialog creation
coat.utils       # Utility functions
```

---

## UI Operations (`coat.ui`)

### Commands

```python
# Execute a UI command
coat.ui.cmd("$CommandName")

# Execute with callback (for dialogs that need confirmation)
coat.ui.cmd("$CommandName", lambda: coat.ui.cmd("$DialogButton#1"))
```

### Setting Values

```python
# Boolean values
coat.ui.setBoolValue("$SettingPath", True)

# Integer values  
coat.ui.setIntValue("$SettingPath", 42)

# Float values
coat.ui.setFloatValue("$SettingPath", 1.5)

# Text fields
coat.ui.setEditBoxValue("$FieldPath", "text value")

# Get current boolean field value
value = coat.ui.getBoolField("$SettingPath")
```

### Room Management

```python
# Switch to a room
coat.ui.toRoom("Sculpt")    # Sculpt, Retopo, Paint, Tweak, UV, Render

# Get current room name
current = coat.ui.currentRoom()  # Returns string like "Sculpt"
```

### Messages

```python
# Show toast message (duration in milliseconds)
coat.ui.showInfoMessage("Message text", 2000)

# Hide a "don't show again" message
coat.ui.hideDontShowAgainMessage("MessageIdentifier")
```

### Options

```python
# Set option value
coat.ui.setOption("OptionName", value)

# Set file for file dialog
coat.ui.setFileForFileDialog("path/to/file.ext")

# Get ID translation
translated = coat.ui.getIdTranslation("TranslationKey")
```

---

## Scene Access (`coat.Scene`)

### Current Objects

```python
# Get current scene
scene = coat.Scene.current()

# Get current volume (sculpt object)
volume = coat.Scene.current().Volume()

# Get sculpt tree root
root = coat.Scene.sculptRoot()
```

### Scene Element Navigation

```python
# Get element name
name = element.name()

# Get parent element
parent = element.parent()

# Select this element only
element.selectOne()

# Transform element
element.transform_single(transform_matrix)
```

### Volume Operations

```python
# Get polycount
polycount = volume.getPolycount()

# Calculate world-space bounding box
bbox = volume.calcWorldSpaceAABB()

# Get associated scene element
scene_element = volume.inScene()
```

### Iteration

```python
# Iterate visible subtree with callback
# Callback receives scene element, returns False to continue
def process_element(element):
    volume = element.Volume()
    # ... do something
    return False  # Continue iteration

coat.Scene.sculptRoot().iterateVisibleSubtree(process_element)
```

### Paint Objects

```python
# Get paint object count
count = coat.Scene.PaintObjectsCount()

# Remove paint object by index
coat.Scene.RemovePaintObject(0)
```

---

## Settings Persistence (`coat.settings`)

```python
# Boolean settings
value = coat.settings.getBool("SettingName")
coat.settings.setBool("SettingName", True)

# String settings
value = coat.settings.getString("SettingName")
coat.settings.setString("SettingName", "value")

# Integer settings
value = coat.settings.getInt("SettingName")
coat.settings.setInt("SettingName", 42)
```

### Known Settings

```python
# UI behavior
"GreyOutBgInModalDialogs"    # Fade background in modal dialogs

# Export settings
"EmbedTexturesToFBX"         # Embed textures in FBX export
"SoftwarePreset"             # Target software (e.g., "Blender", "UnrealEngine")
"NormalsCalculationMethod"   # Normal calculation (e.g., "nm_AngleWeighed")
"NMAP_EXPORT_TYPE"           # Normal map format (e.g., "NM_MAYA", "NM_3DMAX")
"TriangulationMethod"        # Triangulation (e.g., "DelaunayTriangulation")
"TBNMethod"                  # TBN calculation (e.g., "MikkTSpace")
"ExportPreset"               # Export preset name
```

---

## File I/O (`coat.io`)

### JSON

```python
# Save object to JSON file
coat.io.toJson(obj, "path/to/file.json")

# Load object from JSON file
coat.io.fromJsonFile(obj, "path/to/file.json")
```

### File Operations

```python
# Check if file exists
exists = coat.io.fileExists("path/to/file")

# Get supported mesh formats string
formats = coat.io.supportedMeshesFormats()

# Execute external command
coat.io.exec("command")

# Show Python console (for debugging)
coat.io.showPythonConsole()
```

### Timing

```python
# Wait n frames (CRITICAL for async operations)
coat.io.step(4)
```

**Timing guidance:**
- Room switches: `coat.io.step(4)` minimum
- After dialog commands: `coat.io.step(2)` 
- Complex operations: `coat.io.step(4-8)` depending on complexity

---

## Dialogs (`coat.dialog`)

### Dialog Builder Pattern

```python
# Create and show dialog
result = coat.dialog() \
    .ok() \
    .cancel() \
    .text("DialogTextKey") \
    .caption("DialogCaptionKey") \
    .params(settings_object) \
    .dontShowAgainCheckbox() \
    .show()

# Result: 1 = OK, 2 = Cancel (varies by button order)
```

---

## Utilities (`coat.utils`)

```python
# Get enum value by name
value = coat.utils.getEnumValue("ENUM_NAME", "value_name")

# Get enum value by index
value = coat.utils.getEnumValueByIndex("ENUM_NAME", index)
```

---

## Geometry Types

### Bounding Box (`coat.boundbox`)

```python
bbox = coat.boundbox()
bbox.SetEmpty()
bbox.AddBounds(other_bbox)
center = bbox.GetCenter()
diagonal = bbox.GetDiagonal()
```

### Transform Matrix (`coat.mat4`)

```python
# Create translation matrix
transform = coat.mat4.Translation(vector)
transform = coat.mat4.Translation(-center)  # Negative for centering
```

---

## Magic String Patterns

### Command Naming

```
$CommandName              # Standard command
$CommandName#N            # Numbered variant
$COMBOBOX_value          # Combobox selection
$DialogButton#1          # Dialog OK button
$DialogButton#2          # Dialog Cancel button
```

### Setting Paths

```
$SettingName                           # Simple setting
$Category::SettingName                 # Namespaced setting
$Category::SettingName[Type]           # Per-type setting
```

### Known Commands

```python
# Dialog buttons
CMD_DIALOG_OK = "$DialogButton#1"
CMD_DIALOG_CANCEL = "$DialogButton#2"

# Sculpt operations
CMD_DECIMATE_TO_RETOPO = "$DecimateToRetopo"
CMD_DECIMATE_ALL_TO_RETOPO = "$DecimateAllToRetopo"

# Retopo operations
CMD_CLEAR_RETOPO = "$ClearTM"
CMD_SNAP_TO_NORMAL = "$SnapToNearestAlongNormal"
CMD_APPLY_SMOOTH = "$ApplyTSm"

# Baking
CMD_BAKE_NORMAL_FLAT_DISP = "$MergeForDPNM_flatdisp"

# Export
CMD_EXPORT_OBJECT = "$EXPORTOBJECT"
CMD_BLENDER_EXPORT = "$Blender"

# Autopo
CMD_AUTOPO = "$AutoRetopo"
CMD_AUTOPO_IMPORT_BACK = "$RetopoBuildMR"  # Import as multiresolution
```

### Brush Settings

```python
# Per-brush-type settings pattern
f"$BrushConstructor::AutoSubdivide[{brush_type}]"
f"$BrushConstructor::DetailsLevel[{brush_type}]"
f"$BrushConstructor::RemoveStretching[{brush_type}]"

# Global settings
"$RemoveStretching"  # Global remove stretching toggle
"$UseNamesCorrespondence"  # Use name correspondence for baking
```

### Texture Size Combobox

```python
# Format: $COMBOBOX_TEXTURE_SIZE_X + resolution
f"$COMBOBOX_TEXTURE_SIZE_X{resolution}"  # e.g., "$COMBOBOX_TEXTURE_SIZE_X2048"
f"$COMBOBOX_TEXTURE_SIZE_Y{resolution}"
```

### Export Options

```python
"$ExportOpt::ExportMeshName"      # Mesh export path field
"$ExportOpt::ExportTextures"      # Export textures checkbox
"$ExportOpt::ExportGeometry"      # Export geometry checkbox
"$ExportOpt::PathForTextures"     # Textures folder path
```

---

## Scripted Panels (`coat.scripted_panel`)

### Panel Definition

```python
class MyPanel(coat.scripted_panel):
    caption = "Panel Title"      # Window title
    docking = "right"            # "left", "right", "floating"
    min_width = 250              # Minimum width in pixels
    min_height = 400             # Minimum height in pixels
    
    def __init__(self):
        # Properties become UI controls
        self.checkbox_prop = True
        self.slider_prop = 50
        self.text_prop = "default"
    
    def ui(self):
        """Return list of UI element definitions."""
        return [...]
    
    def SomeMethod(self):
        """Called when button clicked."""
        pass

# Instantiate to create panel
MyPanel()
```

### UI Definition Syntax

```python
return [
    # Section headers
    "#Section Header Text",
    
    # Properties (auto-detect control type)
    "bool_property",              # Checkbox
    "int_property,[0,100]",       # Slider with range
    "float_property,[0.0,1.0]",   # Float slider
    "text_property",              # Text field
    
    # Dropdowns
    "enum_prop,[#Option1|#Option2|#Option3]",
    
    # Separators
    "---",
    
    # Buttons (calls self.MethodName())
    "MethodName",
    
    # Column layouts
    "[2 1]",        # Next items: 2 units, 1 unit wide
    "[1 1 1]",      # Three equal columns
    "[[] 6]",       # Flexible left, 6 units right
    
    # Group radio buttons
    "option1, group1",
    "option2, group1",
    
    # File/folder pickers
    "file_path,save:*.fbx",           # Save file dialog
    "folder_path,folder",              # Folder picker
    "mesh_path,save:" + coat.io.supportedMeshesFormats(),
    
    # Special icons
    "#{maticon arrow_forward}",        # Material icon
]
```

---

## Common Patterns

### Auto-Confirm Dialog

```python
def command_with_confirm(command: str) -> None:
    """Execute command and auto-confirm dialog."""
    coat.ui.cmd(command, lambda: coat.ui.cmd("$DialogButton#1"))
```

### Room Switching with Wait

```python
def switch_to_room(room: str, wait_frames: int = 4) -> None:
    """Switch to room and wait for transition."""
    if coat.ui.currentRoom() != room:
        coat.ui.toRoom(room)
        coat.io.step(wait_frames)
```

### Iterate All Volumes

```python
def get_all_volumes() -> list:
    """Get all visible volumes in scene."""
    volumes = []
    coat.Scene.sculptRoot().iterateVisibleSubtree(
        lambda e: volumes.append(e.Volume()) or False
    )
    return volumes
```

### Settings Dialog Pattern

```python
class MySettings:
    def __init__(self):
        self.option1 = True
        self.option2 = 50

settings = MySettings()
if coat.io.fileExists("path/to/settings.json"):
    coat.io.fromJsonFile(settings, "path/to/settings.json")

result = coat.dialog() \
    .ok().cancel() \
    .text("Configure options") \
    .caption("Settings") \
    .params(settings) \
    .show()

if result == 1:
    coat.io.toJson(settings, "path/to/settings.json")
    # Proceed with operation
```

---

## Discovered Behaviors and Quirks

### Timing Requirements

- **Room switches are async:** Always use `coat.io.step(4)` after `coat.ui.toRoom()`
- **Dialog callbacks execute later:** Commands in callbacks may need their own timing
- **Baking operations are slow:** Use `coat.io.step(4-8)` after bake commands

### Dialog Button Numbering

- `$DialogButton#1` is typically OK/Confirm
- `$DialogButton#2` is typically Cancel
- Numbering may vary by dialog

### Settings Not Applied

- Some per-brush-type settings require the global setting to also be enabled
- Example: `$BrushConstructor::RemoveStretching[type]` needs `$RemoveStretching` enabled too

### Iteration Callbacks

- Return `False` to continue iteration
- Return `True` to stop iteration
- Callback receives scene element, use `.Volume()` to get volume

---

## Adding to This Document

When you discover new API patterns:

1. Test the pattern to confirm it works
2. Document the function signature and parameters
3. Add usage examples
4. Note any timing requirements
5. Document any quirks or unexpected behaviors
