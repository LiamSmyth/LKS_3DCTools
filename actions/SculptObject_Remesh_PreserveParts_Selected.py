"""
Remesh a surface object while preserving its parts.

Decomposes the object into parts, resamples each part to increase detail,
then merges back together. This preserves the topology of separate parts.

Room: Sculpt
Action: Decompose, resample each part, merge back
"""
import coat
from utils.scene_api import SceneAPI
from utils.Volume_resample_utils import execute_resample
from utils.Volume_mode_utils import ensure_surface_mode
from utils.coat_ui_utils import (
    CMD_DIALOG_OK,
    CMD_DECOMPOSE,
    CMD_TO_GLOBAL_SPACE,
    wait_frames,
    show_message,
    show_error,
)

# Resample ratio to preserve details during remesh
REMESH_RATIO: float = 4.0


def remesh_element(element: coat.SceneElement) -> None:
    """Remesh a single element by resampling to higher detail."""
    element.selectOne()

    if not element.isSculptObject():
        return

    vol: coat.Volume = element.Volume()
    ensure_surface_mode(vol)

    current_polycount: int = vol.getPolycount()
    target_polycount: int = int(current_polycount * REMESH_RATIO)

    execute_resample(
        target_polycount=target_polycount,
        scale=REMESH_RATIO,
    )

    print(
        f"Resampled '{element.name()}': {current_polycount:,} -> {target_polycount:,}")


def main() -> None:
    """Remesh object preserving parts via decompose and merge."""
    current: coat.SceneElement | None = SceneAPI.get_current_element()

    if not current:
        show_error("No object selected", 2000)
        return

    if not current.isSculptObject():
        show_error("Selected element is not a sculpt object", 2000)
        return

    print(f"Starting remesh with preserve parts: {current.name()}")

    # Decompose object into parts
    def decompose_confirm() -> None:
        coat.ui.cmd(CMD_DIALOG_OK)

    coat.ui.cmd(CMD_DECOMPOSE, decompose_confirm)
    wait_frames(4)

    # Remesh each part in subtree
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(current)
    for el in subtree:
        if el.isSculptObject():
            remesh_element(el)

    # Select root and convert to voxels then back to surface
    current.selectOne()
    vol: coat.Volume = current.Volume()
    ensure_surface_mode(vol)

    vol.toVoxels()
    vol.toSurface()

    # Merge subtree back together
    current.mergeSubtree()

    # Reset to global space
    coat.ui.cmd(CMD_TO_GLOBAL_SPACE)

    show_message(f"Remeshed with parts preserved: {len(subtree)} parts", 2000)


main()
