"""
Radial Menu Registry - Manage registration of multiple radial menus.

This module dynamically generates action scripts for each saved radial menu,
allowing users to register multiple radial menus that can be hotkey-mapped.

Architecture:
- Each saved menu in data/library/radial_menus/ gets an action script
- Action scripts are generated in actions/radial/ folder
- Each action script is registered as a menu item
- Menu items can be hotkey-mapped via 3DCoat preferences

Usage:
    from utils.radial_menu_registry import register_menu, unregister_menu, sync_all_menus
    
    # Register a single menu
    register_menu("my_menu.json", "My Menu")
    
    # Sync all menus in library
    sync_all_menus()
    
    # Unregister a menu
    unregister_menu("my_menu.json")
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
import re
import json

if TYPE_CHECKING:
    import coat


# =============================================================================
# PATHS
# =============================================================================

def _get_lks_root() -> Path:
    """Get root of LKS cModule."""
    return Path(__file__).parent.parent.resolve()


# Library folder where menu configs are saved
RADIAL_MENUS_LIBRARY_DIR: Path = _get_lks_root() / "data" / "library" / "radial_menus"

# Generated action scripts folder
RADIAL_ACTIONS_DIR: Path = _get_lks_root() / "actions" / "radial"

# Registry state file (tracks which menus are registered)
REGISTRY_STATE_FILE: Path = _get_lks_root() / "data" / "state" / "radial_menu_registry.json"


# =============================================================================
# MENU ID GENERATION
# =============================================================================

def sanitize_menu_name(menu_name: str) -> str:
    """
    Sanitize menu name for use in menu ID and filename.
    
    Converts "My Cool Menu!" -> "MyCoolMenu"
    
    Args:
        menu_name: Display name of menu
        
    Returns:
        Sanitized name (PascalCase, alphanumeric only)
    """
    # Remove file extension if present
    if menu_name.endswith(".json"):
        menu_name = menu_name[:-5]
    
    # Split on non-alphanumeric, capitalize each word, join
    words = re.findall(r"[a-zA-Z0-9]+", menu_name)
    return "".join(word.capitalize() for word in words)


def generate_menu_id(menu_name: str) -> str:
    """
    Generate unique menu ID for registration.
    
    Format: LKS_Radial_{SanitizedName}
    
    Args:
        menu_name: Display name or filename of menu
        
    Returns:
        Menu ID string for coat.ui.insertInMenu()
    """
    sanitized = sanitize_menu_name(menu_name)
    return f"LKS_Radial_{sanitized}"


def generate_action_script_name(menu_name: str) -> str:
    """
    Generate action script filename.
    
    Format: LKS_RadialMenu_{SanitizedName}.py
    
    Args:
        menu_name: Display name or filename of menu
        
    Returns:
        Action script filename
    """
    sanitized = sanitize_menu_name(menu_name)
    return f"LKS_RadialMenu_{sanitized}.py"


# =============================================================================
# ACTION SCRIPT GENERATION
# =============================================================================

ACTION_SCRIPT_TEMPLATE: str = '''"""
Show radial menu: {display_name}

Room: All
Action: Display radial menu with configured actions
Auto-generated: DO NOT EDIT - regenerate via radial_menu_registry
"""
from utils.action_base import action


@action
def main() -> None:
    """Show radial menu: {display_name}"""
    from pathlib import Path
    from utils.ui.widgets import get_manager
    from utils.radial_menu_config import load_menu_config
    
    # Load menu config from library
    config_path = Path(__file__).parent.parent / "data" / "library" / "radial_menus" / "{config_filename}"
    
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
    manager.show_menu(items)


main()
'''


def generate_action_script(menu_filename: str, display_name: str) -> str:
    """
    Generate action script content for a radial menu.
    
    Args:
        menu_filename: Filename of menu config in library (e.g., "my_menu.json")
        display_name: Human-readable name for menu
        
    Returns:
        Python script content
    """
    return ACTION_SCRIPT_TEMPLATE.format(
        display_name=display_name,
        config_filename=menu_filename,
    )


def write_action_script(menu_filename: str, display_name: str) -> Path:
    """
    Write action script to disk.
    
    Args:
        menu_filename: Filename of menu config in library
        display_name: Human-readable name for menu
        
    Returns:
        Path to written action script
    """
    # Ensure radial actions folder exists
    RADIAL_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate script content
    script_content = generate_action_script(menu_filename, display_name)
    
    # Write to file
    script_name = generate_action_script_name(menu_filename)
    script_path = RADIAL_ACTIONS_DIR / script_name
    script_path.write_text(script_content, encoding="utf-8")
    
    print(f"[RadialRegistry] Generated action script: {script_path}")
    return script_path


def delete_action_script(menu_filename: str) -> bool:
    """
    Delete generated action script.
    
    Args:
        menu_filename: Filename of menu config in library
        
    Returns:
        True if script was deleted, False if not found
    """
    script_name = generate_action_script_name(menu_filename)
    script_path = RADIAL_ACTIONS_DIR / script_name
    
    if script_path.exists():
        script_path.unlink()
        print(f"[RadialRegistry] Deleted action script: {script_path}")
        return True
    else:
        print(f"[RadialRegistry] Action script not found: {script_path}")
        return False


# =============================================================================
# REGISTRY STATE MANAGEMENT
# =============================================================================

def load_registry_state() -> dict[str, str]:
    """
    Load registry state from disk.
    
    State format: {menu_filename: display_name}
    
    Returns:
        Dictionary mapping menu filenames to display names
    """
    if not REGISTRY_STATE_FILE.exists():
        return {}
    
    try:
        with open(REGISTRY_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[RadialRegistry] Failed to load registry state: {e}")
        return {}


def save_registry_state(state: dict[str, str]) -> None:
    """
    Save registry state to disk.
    
    Args:
        state: Dictionary mapping menu filenames to display names
    """
    REGISTRY_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(REGISTRY_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[RadialRegistry] Failed to save registry state: {e}")


# =============================================================================
# MENU REGISTRATION
# =============================================================================

def register_menu(menu_filename: str, display_name: str) -> bool:
    """
    Register a radial menu as a hotkey-mappable action.
    
    Steps:
    1. Generate action script in actions/radial/
    2. Register menu item via coat.ui.insertInMenu()
    3. Update registry state
    
    Args:
        menu_filename: Filename in library (e.g., "my_menu.json")
        display_name: Human-readable name for menu
        
    Returns:
        True if registered, False if already registered
    """
    import coat
    from utils.coat_menu_utils import register_action
    
    # Check if already registered
    state = load_registry_state()
    if menu_filename in state:
        print(f"[RadialRegistry] Menu already registered: {menu_filename}")
        return False
    
    # Generate action script
    script_path = write_action_script(menu_filename, display_name)
    
    # Generate menu ID
    menu_id = generate_menu_id(menu_filename)
    
    # Register with 3DCoat
    register_action(
        menu_id=menu_id,
        display_name=f"Radial: {display_name}",
        script_path=script_path,
        menu_name="Scripts",
    )
    
    # Update registry state
    state[menu_filename] = display_name
    save_registry_state(state)
    
    print(f"[RadialRegistry] Registered menu: {display_name} (ID: {menu_id})")
    return True


def unregister_menu(menu_filename: str) -> bool:
    """
    Unregister a radial menu.
    
    Steps:
    1. Delete action script
    2. Update registry state
    3. (Menu item XML persists until 3DCoat restart - manual cleanup required)
    
    Args:
        menu_filename: Filename in library
        
    Returns:
        True if unregistered, False if not registered
    """
    # Check if registered
    state = load_registry_state()
    if menu_filename not in state:
        print(f"[RadialRegistry] Menu not registered: {menu_filename}")
        return False
    
    # Delete action script
    delete_action_script(menu_filename)
    
    # Update registry state
    del state[menu_filename]
    save_registry_state(state)
    
    print(f"[RadialRegistry] Unregistered menu: {menu_filename}")
    print("[RadialRegistry] Note: Menu item XML persists until 3DCoat restart")
    return True


def is_menu_registered(menu_filename: str) -> bool:
    """
    Check if a menu is currently registered.
    
    Args:
        menu_filename: Filename in library
        
    Returns:
        True if registered
    """
    state = load_registry_state()
    return menu_filename in state


def get_registered_menus() -> dict[str, str]:
    """
    Get all registered menus.
    
    Returns:
        Dictionary mapping menu filenames to display names
    """
    return load_registry_state()


# =============================================================================
# BULK OPERATIONS
# =============================================================================

def sync_all_menus() -> tuple[int, int, int]:
    """
    Sync all menus in library with registration state.
    
    - Registers menus that exist in library but not in registry
    - Unregisters menus that exist in registry but not in library
    - Updates action scripts for registered menus
    
    Returns:
        Tuple of (registered_count, unregistered_count, updated_count)
    """
    # Load current state
    state = load_registry_state()
    
    # Get all menus in library
    if not RADIAL_MENUS_LIBRARY_DIR.exists():
        RADIAL_MENUS_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    
    library_menus = {
        f.name for f in RADIAL_MENUS_LIBRARY_DIR.glob("*.json")
        if f.name != "README.md"
    }
    
    registered_count = 0
    unregistered_count = 0
    updated_count = 0
    
    # Unregister menus no longer in library
    for menu_filename in list(state.keys()):
        if menu_filename not in library_menus:
            unregister_menu(menu_filename)
            unregistered_count += 1
    
    # Register/update menus in library
    for menu_filename in library_menus:
        if menu_filename in state:
            # Already registered - regenerate action script
            display_name = state[menu_filename]
            write_action_script(menu_filename, display_name)
            updated_count += 1
        else:
            # Not registered - extract display name from config
            config_path = RADIAL_MENUS_LIBRARY_DIR / menu_filename
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                display_name = config_data.get("name", menu_filename[:-5])
            except Exception:
                display_name = menu_filename[:-5]
            
            register_menu(menu_filename, display_name)
            registered_count += 1
    
    print(f"[RadialRegistry] Sync complete: {registered_count} registered, "
          f"{unregistered_count} unregistered, {updated_count} updated")
    
    return registered_count, unregistered_count, updated_count


def cleanup_orphaned_scripts() -> int:
    """
    Delete action scripts that aren't in registry state.
    
    Returns:
        Number of scripts deleted
    """
    if not RADIAL_ACTIONS_DIR.exists():
        return 0
    
    state = load_registry_state()
    registered_scripts = {
        generate_action_script_name(menu_filename)
        for menu_filename in state.keys()
    }
    
    deleted_count = 0
    for script_path in RADIAL_ACTIONS_DIR.glob("*.py"):
        if script_path.name not in registered_scripts:
            script_path.unlink()
            print(f"[RadialRegistry] Deleted orphaned script: {script_path.name}")
            deleted_count += 1
    
    return deleted_count
