"""
SculptObject_ToggleMeshVox Operator

Toggle sculpt objects between surface (mesh) and voxel modes
while preserving approximately the same polycount.

Process:
- Surface → Voxels: Resample, convert, resample to original count
- Voxels → Surface: Convert directly

Uses scope resolution to determine which elements to process.
"""
from __future__ import annotations

import coat
from utils.scene_api import SceneAPI, SelectionAPI
from utils.scope_utils import Scope, resolve_scope
from utils.object_utils import ObjectUtils
from utils.Volume_resample_utils import resample_to_target
from utils.Volume_mode_utils import convert_to_surface
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(scope: Scope = Scope.CURRENT) -> int:
    """
    Toggle sculpt objects between mesh and voxel modes.

    Args:
        scope: Which objects to operate on

    Returns:
        Number of objects processed
    """
    elements: list[coat.SceneElement] = resolve_scope(scope)

    if not elements:
        show_error("No objects to process", 2000)
        return 0

    count: int = 0

    for element in elements:
        if not element.isSculptObject():
            continue

        element.selectOne()
        vol: coat.Volume = element.Volume()
        initial_polycount: int = vol.getPolycount()
        object_name: str = element.name()

        if vol.isSurface():
            # Surface → Voxels
            print(f"Converting {object_name} to Voxels...")
            resample_to_target(initial_polycount, initial_polycount)
            vol.toVoxels()
            resample_to_target(vol.getPolycount(), initial_polycount)
            mode_str: str = "Voxels"
        else:
            # Voxels → Surface
            print(f"Converting {object_name} to Surface...")
            convert_to_surface(vol)
            mode_str = "Surface"

        new_polycount: int = vol.getPolycount()
        print(f"{object_name}: {initial_polycount:,} → {new_polycount:,} ({mode_str})")
        count += 1

    if count == 1:
        show_message(f"Converted to {mode_str}: {new_polycount:,} polys", 3000)
    else:
        show_message(f"Toggled mode on {count} objects", 3000)

    return count
