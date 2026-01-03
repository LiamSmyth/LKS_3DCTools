"""
Fill each part in the subtree with a random ID color.

Useful for generating ID maps for texture baking. Each object in the
subtree gets a unique random color.

Room: Sculpt
Action: Fill each subtree object with unique random color
"""
import coat
import random
from _utils.scene_api import SceneAPI
from _utils.coat_ui_utils import (
    CMD_FILL_LAYER,
    SETTING_PEN_DEPTH,
    show_message,
    show_error,
)
from _utils.SceneElement_visibility_utils import (
    cache_ghost_states,
    restore_ghost_states,
    ghost_elements,
)

# Minimum color value to avoid pure black
MIN_COLOR: int = 0


def fill_element_with_random_color(element: coat.SceneElement) -> None:
    """Fill a single element with a random RGB color using ghost isolation."""
    # Unghost this element, fill, re-ghost
    element.setGhost(False)

    # Generate random color
    r: float = random.uniform(MIN_COLOR, 255)
    g: float = random.uniform(MIN_COLOR, 255)
    b: float = random.uniform(MIN_COLOR, 255)

    coat.Volume.color(r, g, b)
    coat.ui.cmd(CMD_FILL_LAYER)

    # Re-ghost so next element can be filled in isolation
    element.setGhost(True)


def main() -> None:
    """Fill each subtree element with a unique random color."""
    active_element: coat.SceneElement | None = SceneAPI.get_current_element()

    if not active_element:
        show_error("No object selected", 2000)
        return

    # Save original pen depth
    original_pen_depth: float = coat.ui.getSliderValue(SETTING_PEN_DEPTH)

    # Set pen depth to 0 for color-only filling
    coat.ui.setSliderValue(SETTING_PEN_DEPTH, 0)

    # Switch to IDMap layer (creates if not exists)
    layer_id: int = coat.Scene.getLayer("IDMap", True)
    coat.Scene.setActiveLayer(layer_id)
    coat.Scene.setLayerDepthOpacity(layer_id, 0)

    # Collect ALL scene elements and subtree
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(active_element)

    # Cache ghost states for restoration
    ghost_cache: dict[int, bool] = cache_ghost_states(all_elements)

    # Ghost everything in the scene
    ghost_elements(all_elements)

    # Fill each element in subtree (unghost one at a time)
    for el in subtree:
        fill_element_with_random_color(el)

    # Restore original ghost states
    restore_ghost_states(all_elements, ghost_cache)

    # Restore original selection and layer
    active_element.selectOne()
    coat.Scene.setActiveLayer(coat.Scene.getLayer("Layer 0", True))
    coat.ui.setSliderValue(SETTING_PEN_DEPTH, original_pen_depth)

    show_message(f"Filled {len(subtree)} objects with ID colors", 2000)


main()
