"""
Code Generators - Generate Python action scripts dynamically.

This package provides utilities for generating action scripts programmatically,
useful for registering dynamic menus, tools, and other hotkey-mappable actions.
"""

from .action_generator import (
    generate_action_script,
    write_action_script,
    delete_action_script,
    sanitize_identifier,
)

__all__ = [
    "generate_action_script",
    "write_action_script",
    "delete_action_script",
    "sanitize_identifier",
]
