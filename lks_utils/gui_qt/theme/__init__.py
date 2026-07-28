"""Slim bundled stub for lks_utils.gui_qt.theme (LKS release)."""
from __future__ import annotations

from typing import Any
import importlib

_LAZY_EXPORTS: dict[str, str] = {
    'ThemeAwareMixin': 'lks_utils.gui_qt.theme.theme_aware_mixin',
}

__all__ = ['ThemeAwareMixin']

def __getattr__(name: str) -> Any:
    mod_path = _LAZY_EXPORTS.get(name)
    if mod_path is None:
        raise AttributeError(f"module 'lks_utils.gui_qt.theme' "
            f"has no attribute {name!r}")
    mod = importlib.import_module(mod_path)
    value = getattr(mod, name)
    globals()[name] = value
    return value
