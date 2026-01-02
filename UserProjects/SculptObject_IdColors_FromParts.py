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

# Minimum color value to avoid pure black
MIN_COLOR: int = 0


def fill_element_with_random_color(element: coat.SceneElement) -> None:
    """Fill a single element with a random RGB color."""
    element.selectOne()
    element.setVisibility(True)

    # Generate random color
    r: float = random.uniform(MIN_COLOR, 255)
    g: float = random.uniform(MIN_COLOR, 255)
    b: float = random.uniform(MIN_COLOR, 255)

    coat.Volume.color(r, g, b)
    coat.ui.cmd(CMD_FILL_LAYER)

    element.setVisibility(False)


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

    # Switch to IDMap layer
    layer_id: int = coat.Scene.getLayer("IDMap")
    coat.Scene.setActiveLayer(layer_id)
    coat.Scene.setLayerDepthOpacity(layer_id, 0)

    # Get scene root
    scene_root: coat.SceneElement | None = SceneAPI.get_sculpt_root()
    if not scene_root:
        show_error("No sculpt root found", 2000)
        return

    # Disable all visibility first
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()
    for el in all_elements:
        el.setVisibility(False)

    # Fill root element
    fill_element_with_random_color(active_element)

    # Fill all children in subtree
    subtree: list[coat.SceneElement] = SceneAPI.collect_subtree(active_element)
    for el in subtree:
        if el != active_element:
            fill_element_with_random_color(el)

    # Re-enable all visibility
    for el in all_elements:
        el.setVisibility(True)

    # Restore original selection and layer
    active_element.selectOne()
    coat.Scene.setActiveLayer(coat.Scene.getLayer("Layer 0"))
    coat.ui.setSliderValue(SETTING_PEN_DEPTH, original_pen_depth)

    show_message(f"Filled {len(subtree)} objects with ID colors", 2000)


main()
