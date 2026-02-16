# Code Generators

This module provides utilities for **dynamically generating Python action scripts**.

## Purpose

In the LKS addon, action scripts are the bridge between user actions (hotkeys, menu items) and operator functions. While most action scripts are manually written, some use cases benefit from programmatic generation:

1. **Radial Menus** - Generate action scripts for each user-created radial menu config
2. **Batch Actions** - Generate variants of operations (e.g., scale 2x, 4x, 8x, 16x)
3. **User Configurations** - Create scripts based on user settings or presets
4. **Dynamic Tools** - Register tools discovered at runtime

## Architecture

```
generators/
├── __init__.py              # Package exports
├── action_generator.py      # Core action script generator
└── README.md                # This file
```

## Usage

### Basic Example: Radial Menu Script

```python
from generators.action_generator import generate_radial_menu_script, write_action_script
from pathlib import Path

# Generate script content from template
script_content = generate_radial_menu_script(
    config_filename="sculpt_tools.json",
    display_name="Sculpt Tools"
)

# Write to disk
script_path = write_action_script(
    output_dir=Path("actions/radial"),
    script_name="LKS_RadialMenu_SculptTools.py",
    content=script_content
)
```

### Custom Template Example

```python
from generators.action_generator import generate_action_script, register_template

# Register custom template
register_template(
    "batch_scale",
    '''"""Scale by {factor}x"""
    from utils.action_base import action
    
    @action
    def main() -> None:
        from ops.SculptObject_Scale import main as scale_op
        from utils.scope_utils import Scope
        scale_op(scope=Scope.CURRENT, factor={factor})
    
    main()
    '''
)

# Generate scripts for multiple scales
for factor in [2, 4, 8, 16]:
    script = generate_action_script("batch_scale", factor=factor)
    write_action_script(
        Path("actions/scale"),
        f"Scale_{factor}x.py",
        script
    )
```

### Identifier Sanitization

```python
from generators.action_generator import sanitize_identifier

# PascalCase (default)
sanitize_identifier("My Cool Menu!", "PascalCase")  # "MyCoolMenu"

# snake_case
sanitize_identifier("My Cool Menu!", "snake_case")  # "my_cool_menu"

# kebab-case
sanitize_identifier("My Cool Menu!", "kebab-case")  # "my-cool-menu"
```

## Templates

### Built-in Templates

1. **`radial_menu`** - Radial menu loader
   - Loads config from `data/library/radial_menus/`
   - Shows menu via RadialMenuManager

2. **`simple_action`** - Simple operator invocation
   - Imports and calls operator
   - Configurable room, description

### Template Variables

Templates use Python's `.format()` syntax with `{placeholders}`:

```python
RADIAL_MENU_TEMPLATE = '''"""
Show radial menu: {display_name}
"""
from utils.action_base import action

@action
def main() -> None:
    config_path = "{config_path_relative}"
    # ... load and show
'''
```

### Custom Templates

Register your own templates for specialized use cases:

```python
register_template("my_template", template_string)
```

## Integration with Registry Systems

The `action_generator` is designed to be **reusable** - it doesn't know about radial menus specifically. Registry systems (like `radial_menu_registry.py`) use it to generate scripts:

```python
# In radial_menu_registry.py
from generators.action_generator import generate_radial_menu_script, write_action_script

def write_action_script(menu_filename: str, display_name: str) -> Path:
    # Generate using action_generator
    script_content = generate_radial_menu_script(
        config_filename=menu_filename,
        display_name=display_name,
    )
    
    # Write using action_generator
    return gen_write_script(
        output_dir=RADIAL_ACTIONS_DIR,
        script_name=generate_action_script_name(menu_filename),
        content=script_content,
    )
```

## Best Practices

### 1. Include Metadata Comments

Generated scripts should indicate they're auto-generated:

```python
"""
Brief description

Auto-generated: DO NOT EDIT - regenerate via action script system
"""
```

### 2. Use `@action` Decorator

Always use the `@action` decorator for hot-reload support:

```python
from utils.action_base import action

@action
def main() -> None:
    # Your code here
```

### 3. Error Handling

Include try-except blocks in templates for robustness:

```python
try:
    items = load_menu_config(config_path)
except Exception as e:
    print(f"[Error] Failed to load: {e}")
    return
```

### 4. Relative Paths

Use `Path(__file__)` for relative path resolution:

```python
config_path = Path(__file__).parent.parent / "data/library/file.json"
```

### 5. Template Validation

Validate template variables before generation:

```python
required_vars = ["display_name", "config_filename"]
for var in required_vars:
    if var not in template_vars:
        raise KeyError(f"Missing required variable: {var}")
```

## Future Extensions

Potential uses for the action_generator:

- **Preset Manager** - Generate scripts for user-saved presets
- **Batch Operations** - Create parameter variants (e.g., decimate 50%, 25%, 12.5%)
- **Workflow Automation** - Generate scripts from recorded action sequences
- **External Integration** - Generate scripts from external tool configs
- **AI-Generated Tools** - Create scripts from LLM-generated descriptions

## API Reference

See `action_generator.py` docstrings for full API documentation:

```python
# Core functions
generate_action_script(template, **vars) -> str
write_action_script(dir, name, content) -> Path
delete_action_script(dir, name) -> bool
sanitize_identifier(name, style) -> str
register_template(name, template_str) -> None

# Convenience wrappers
generate_radial_menu_script(filename, name) -> str
generate_simple_action_script(...) -> str
```

---

**Note:** This module is pure Python with no 3DCoat dependencies - it can be unit tested independently.
