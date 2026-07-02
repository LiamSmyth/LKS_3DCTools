"""
Action Script Generator - Generate Python action scripts dynamically.

Provides utilities for generating action scripts with various templates,
useful for creating hotkey-mappable actions programmatically.

Usage:
    from generators.action_generator import generate_action_script, write_action_script
    
    # Generate script content
    script_content = generate_action_script(
        template="radial_menu",
        config_path="data/library/radial_menus/my_menu.json",
        display_name="My Menu"
    )
    
    # Write to disk
    script_path = write_action_script(
        output_dir=Path("actions/radial"),
        script_name="LKS_RadialMenu_MyMenu.py",
        content=script_content
    )
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import re


# =============================================================================
# IDENTIFIER SANITIZATION
# =============================================================================

def sanitize_identifier(name: str, style: str = "PascalCase") -> str:
    """
    Sanitize a name for use as Python identifier or filename.

    Args:
        name: Input name (can contain spaces, special chars, etc.)
        style: Output style - "PascalCase", "snake_case", or "kebab-case"

    Returns:
        Sanitized identifier

    Examples:
        >>> sanitize_identifier("My Cool Menu!", "PascalCase")
        'MyCoolMenu'
        >>> sanitize_identifier("My Cool Menu!", "snake_case")
        'my_cool_menu'
        >>> sanitize_identifier("My Cool Menu!", "kebab-case")
        'my-cool-menu'
    """
    # Remove file extension if present
    if name.endswith(".json"):
        name = name[:-5]

    # Split on non-alphanumeric characters
    words = re.findall(r"[a-zA-Z0-9]+", name)

    if not words:
        raise ValueError(f"No valid characters in name: {name}")

    if style == "PascalCase":
        return "".join(word.capitalize() for word in words)
    elif style == "snake_case":
        return "_".join(word.lower() for word in words)
    elif style == "kebab-case":
        return "-".join(word.lower() for word in words)
    else:
        raise ValueError(f"Unknown style: {style}")


# =============================================================================
# SCRIPT TEMPLATES
# =============================================================================

RADIAL_MENU_TEMPLATE: str = '''"""
Show radial menu: {display_name}

Room: All
Action: Display radial menu with configured actions
Auto-generated: DO NOT EDIT - regenerate via action script system

NOTE: Uses dev_mode setting to conditionally reload modules.
When dev_mode=False, skips reload_all() for instant radial menu response.
"""
import sys
import time as _time

_MODULE_BODY_START: float = _time.monotonic()


def main() -> None:
    """Show radial menu: {display_name}"""
    _t0: float = _time.monotonic()
    _dispatch_ms: float = (_t0 - _MODULE_BODY_START) * 1000
    print(f"[RadialMenu] Module body→main: {{_dispatch_ms:.0f}}ms")

    # Conditionally reload modules in dev mode
    from utils.lks_settings import get_settings
    if get_settings().dev_mode:
        from utils.hot_reload import reload_all
        reload_all()

    from pathlib import Path
    from utils.ui.widgets import get_manager
    from utils.radial_menu_config import load_menu_config
    
    # Load menu config from library
    config_path = Path(__file__).parent.parent / "{config_path_relative}"
    
    try:
        items = load_menu_config(config_path)
    except Exception as e:
        print(f"[RadialMenu] Failed to load menu config: {{e}}")
        return
    
    if not items:
        print(f"[RadialMenu] No menu items in config: {config_filename}")
        return
    
    # Show menu at cursor position
    manager = get_manager()
    manager.show_menu(items, action_id="{action_id}")

    # Queue this module for cache clearing (so next press re-executes)
    if not hasattr(sys, '_lks_modules_to_clear'):
        sys._lks_modules_to_clear = set()
    sys._lks_modules_to_clear.add(__name__)


main()
'''

SIMPLE_ACTION_TEMPLATE: str = '''"""
{description}

Room: {room}
Action: {action_description}
Auto-generated: DO NOT EDIT - regenerate via action script system
"""
from utils.action_base import action


@action
def main() -> None:
    """{action_description}"""
    {import_statements}
    
    {main_code}


main()
'''

# Registry of available templates
TEMPLATES: Dict[str, str] = {
    "radial_menu": RADIAL_MENU_TEMPLATE,
    "simple_action": SIMPLE_ACTION_TEMPLATE,
}


# =============================================================================
# SCRIPT GENERATION
# =============================================================================

def generate_action_script(
    template: str,
    **template_vars: Any
) -> str:
    """
    Generate action script content from template.

    Args:
        template: Template name ("radial_menu", "simple_action", etc.)
        **template_vars: Variables to substitute in template

    Returns:
        Generated Python script content

    Raises:
        ValueError: If template not found
        KeyError: If required template variable missing

    Examples:
        # Radial menu
        script = generate_action_script(
            "radial_menu",
            display_name="My Menu",
            config_path_relative="data/library/radial_menus/my_menu.json",
            config_filename="my_menu.json"
        )

        # Simple action
        script = generate_action_script(
            "simple_action",
            description="Scale object by 2x",
            room="Sculpt",
            action_description="Scale selected object by factor of 2.0",
            import_statements="from ops.SculptObject_Scale import main as op_scale",
            main_code="op_scale(scope=Scope.CURRENT, factor=2.0)"
        )
    """
    if template not in TEMPLATES:
        raise ValueError(
            f"Unknown template: {template}. Available: {list(TEMPLATES.keys())}")

    template_str = TEMPLATES[template]

    try:
        return template_str.format(**template_vars)
    except KeyError as e:
        raise KeyError(
            f"Missing required template variable: {e}. "
            f"Provided: {list(template_vars.keys())}"
        ) from e


def register_template(name: str, template_str: str) -> None:
    """
    Register a custom template for script generation.

    Args:
        name: Template identifier
        template_str: Python script template with {placeholders}

    Example:
        register_template(
            "custom_tool",
            '\"\"\"Tool: {tool_name}\"\"\"\\n'
            'from utils.action_base import action\\n'
            '@action\\n'
            'def main() -> None:\\n'
            '    from ops import {operator_module}\\n'
            '    {operator_module}.main({args})\\n'
            'main()'
        )
    """
    TEMPLATES[name] = template_str


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def write_action_script(
    output_dir: Path,
    script_name: str,
    content: str,
    overwrite: bool = True
) -> Path:
    """
    Write action script to disk.

    Args:
        output_dir: Directory to write script to
        script_name: Script filename (e.g., "LKS_RadialMenu_MyMenu.py")
        content: Python script content
        overwrite: Whether to overwrite existing file

    Returns:
        Path to written script

    Raises:
        FileExistsError: If file exists and overwrite=False
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build full path
    script_path = output_dir / script_name

    # Check for existing file
    if script_path.exists() and not overwrite:
        raise FileExistsError(f"Script already exists: {script_path}")

    # Write content
    script_path.write_text(content, encoding="utf-8")

    print(f"[ActionGenerator] Generated: {script_path}")
    return script_path


def delete_action_script(
    output_dir: Path,
    script_name: str
) -> bool:
    """
    Delete an action script.

    Args:
        output_dir: Directory containing script
        script_name: Script filename

    Returns:
        True if deleted, False if not found
    """
    script_path = output_dir / script_name

    if script_path.exists():
        script_path.unlink()
        print(f"[ActionGenerator] Deleted: {script_path}")
        return True
    else:
        print(f"[ActionGenerator] Not found: {script_path}")
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_radial_menu_script(
    config_filename: str,
    display_name: str,
    config_path_relative: str = None,
    action_id: str | None = None,
) -> str:
    """
    Generate a radial menu action script.

    Convenience wrapper for the most common use case.

    Args:
        config_filename: Name of config file (e.g., "my_menu.json")
        display_name: Human-readable menu name
        config_path_relative: Relative path from script to config (auto-calculated if None)
        action_id: Menu/action identifier used in 3DCoat hotkeys

    Returns:
        Generated script content
    """
    if config_path_relative is None:
        # From actions/radial/script.py: .parent.parent = actions/
        # Need ../data/ to get from actions/ to data/ (up to LKS root, then down to data/)
        config_path_relative = f"../data/library/radial_menus/{config_filename}"

    if action_id is None:
        action_id = f"LKS_Radial_{sanitize_identifier(config_filename, style='PascalCase')}"

    return generate_action_script(
        "radial_menu",
        display_name=display_name,
        config_path_relative=config_path_relative,
        config_filename=config_filename,
        action_id=action_id,
    )


def generate_simple_action_script(
    description: str,
    room: str,
    action_description: str,
    import_statements: str,
    main_code: str
) -> str:
    """
    Generate a simple action script.

    Convenience wrapper for simple operator invocations.

    Args:
        description: Script docstring header
        room: 3DCoat room requirement
        action_description: Brief action description
        import_statements: Import lines (without 'from utils.action_base import action')
        main_code: Code to execute in main()

    Returns:
        Generated script content
    """
    return generate_action_script(
        "simple_action",
        description=description,
        room=room,
        action_description=action_description,
        import_statements=import_statements,
        main_code=main_code,
    )
