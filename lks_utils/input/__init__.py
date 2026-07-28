"""Slim bundled stub for lks_utils.input (LKS release)."""
from __future__ import annotations

from typing import Any
import importlib

_LAZY_EXPORTS: dict[str, str] = {
    'Action': 'lks_utils.input.action',
    'Binding': 'lks_utils.input.binding',
    'GestureKind': 'lks_utils.input.binding',
    'InputBindings': 'lks_utils.input.bindings_registry',
    'KeyBinding': 'lks_utils.input.binding',
    'MouseBinding': 'lks_utils.input.binding',
    'MouseButton': 'lks_utils.input.binding',
    'WheelBinding': 'lks_utils.input.binding',
    'get_default_bindings': 'lks_utils.input.bindings_registry',
    'load_per_app_overrides': 'lks_utils.input.per_app_override',
    'save_per_app_overrides': 'lks_utils.input.per_app_override',
}

__all__ = ['Action', 'Binding', 'GestureKind', 'InputBindings', 'KeyBinding', 'MouseBinding', 'MouseButton', 'WheelBinding', 'get_default_bindings', 'load_per_app_overrides', 'save_per_app_overrides']

def __getattr__(name: str) -> Any:
    mod_path = _LAZY_EXPORTS.get(name)
    if mod_path is None:
        raise AttributeError(f"module 'lks_utils.input' "
            f"has no attribute {name!r}")
    mod = importlib.import_module(mod_path)
    value = getattr(mod, name)
    globals()[name] = value
    return value
