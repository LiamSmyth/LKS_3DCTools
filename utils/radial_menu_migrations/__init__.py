"""
Radial menu schema migrations.

Public API for normalizing versions and upgrading on-disk menu configs.
"""
from __future__ import annotations

from utils.radial_menu_migrations.runner import migrate_config, migrate_file
from utils.radial_menu_migrations.versions import CURRENT_VERSION, normalize_version

__all__: list[str] = [
    "CURRENT_VERSION",
    "migrate_config",
    "migrate_file",
    "normalize_version",
]
