"""
Radial Menu Configuration Loader - Parse JSON config and build menu tree.

Loads menu configuration from JSON file and converts to RadialMenuItem tree.
Supports both direct action paths and module.function references.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Callable, Any

try:
    from utils.ui.widgets.radial_menu import RadialMenuItem
    HAS_RADIAL_MENU = True
except ImportError:
    HAS_RADIAL_MENU = False


# =============================================================================
# CONFIG PATHS
# =============================================================================

# Default config file location
_DATA_DIR: Path = Path(__file__).parent.parent / "data"
DEFAULT_CONFIG_PATH: Path = _DATA_DIR / "radial_menu_config.json"


# =============================================================================
# ACTION RESOLUTION
# =============================================================================

def _resolve_action_path(action_path: str, action_args: dict[str, Any] | None = None) -> Callable[[], None]:
    """
    Resolve action path string to callable function.

    Supports three formats:
    1. "$CommandName" - 3DCoat UI command (recommended for leaf nodes)
    2. "actions/ScriptName.py" - Execute action script file
    3. "ops.SculptObject_Decimate.main" - Import and call module function
       (auto-prefixed with "cModules.LKS." for cModule compatibility)

    Args:
        action_path: Path to action (UI command, script file, or module.function)
        action_args: Optional keyword arguments to pass to function (ignored for UI commands)

    Returns:
        Callable that executes the action
    """
    if action_path.startswith("$"):
        # 3DCoat UI command - execute directly via coat.ui.cmd
        command_name = action_path

        def ui_command_wrapper():
            try:
                import coat
                print(f"[RadialMenu] Executing 3DCoat command: {command_name}")
                coat.ui.cmd(command_name)
            except Exception as e:
                print(f"[RadialMenu] Failed to execute {command_name}: {e}")

        return ui_command_wrapper

    elif action_path.startswith("actions/") and action_path.endswith(".py"):
        # Action script file - execute via coat
        script_path = action_path

        def action_script_wrapper():
            try:
                import coat
                # Get full path from cModule root
                import cPy.cCore
                install_folder: str = cPy.cCore.cExtension.getCoatInstallForder()
                full_path: str = f"{install_folder}/UserPrefs/StdScripts/cModules/LKS/{script_path}"
                coat.ui.cmd(f"$execute:{full_path}")
            except Exception as e:
                print(f"[RadialMenu] Failed to execute {script_path}: {e}")

        return action_script_wrapper

    else:
        # Module.function path - import and call directly
        # Auto-prefix with cModules.LKS if not already prefixed
        if not action_path.startswith("cModules."):
            action_path = f"cModules.LKS.{action_path}"

        parts = action_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid action path: {action_path} (must be 'module.function')")

        module_path, function_name = parts

        def module_function_wrapper():
            try:
                # Dynamic import
                import importlib
                module = importlib.import_module(module_path)
                func = getattr(module, function_name)

                # Call with args if provided
                if action_args:
                    # Convert string scope to enum if present
                    if "scope" in action_args and isinstance(action_args["scope"], str):
                        from cModules.LKS.utils.scope_utils import Scope
                        action_args["scope"] = Scope[action_args["scope"]]
                    func(**action_args)
                else:
                    func()
            except Exception as e:
                print(f"[RadialMenu] Failed to execute {action_path}: {e}")

        return module_function_wrapper


# =============================================================================
# CONFIG LOADING
# =============================================================================

def _parse_menu_item(item_data: dict[str, Any]) -> RadialMenuItem:
    """
    Parse single menu item from JSON data.

    Args:
        item_data: Dictionary from JSON config

    Returns:
        RadialMenuItem instance
    """
    label: str = item_data["label"]
    icon: str | None = item_data.get("icon")
    angle: float | None = item_data.get("angle")
    description: str | None = item_data.get("description")  # For tooltips/docs
    action_path: str | None = item_data.get("action")
    action_args: dict[str, Any] | None = item_data.get("action_args")
    children_data: list[dict] | None = item_data.get("children")

    # Resolve action if present
    action: Callable[[], None] | None = None
    if action_path:
        action = _resolve_action_path(action_path, action_args)
    else:
        # No action - use dummy for branch nodes
        def dummy_action() -> None:
            print(
                f"[RadialMenu] Branch node '{label}' has no action (this is normal)")
        action = dummy_action

    # Parse children recursively
    children: list[RadialMenuItem] | None = None
    if children_data:
        children = [_parse_menu_item(child) for child in children_data]

    return RadialMenuItem(
        label=label,
        action=action,
        icon=icon,
        children=children,
        angle=angle,
    )


def load_menu_config(config_path: str | Path | None = None) -> list[RadialMenuItem]:
    """
    Load menu configuration from JSON file.

    Args:
        config_path: Path to config file (None = use default)

    Returns:
        List of root-level menu items

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Radial menu config not found: {config_path}")

    # Load JSON
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # Validate version (optional)
    version = config_data.get("version", "1.0")
    if version != "1.0":
        print(
            f"[RadialMenuConfig] Warning: Unknown config version {version}, proceeding anyway")

    # Parse items
    items_data = config_data.get("items", [])
    if not items_data:
        raise ValueError("Config must contain at least one item")

    items = [_parse_menu_item(item) for item in items_data]

    return items


def get_default_menu_items() -> list[RadialMenuItem]:
    """
    Get default menu items from config file.

    Returns:
        List of menu items, or empty list if config load fails
    """
    print(f"[RadialMenuConfig] Loading from: {DEFAULT_CONFIG_PATH}")
    try:
        items = load_menu_config()
        print(
            f"[RadialMenuConfig] Successfully loaded {len(items)} root items")
        return items
    except Exception as e:
        import traceback
        print(f"[RadialMenuConfig] Failed to load default config: {e}")
        traceback.print_exc()
        return []
