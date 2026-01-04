"""
SculptObject_IdColors Operator

Fill sculpt objects with random ID colors for texture baking.
Each object gets a unique random color on the IDMap layer.

Uses ghost isolation pattern to ensure fill only affects one object at a time.
"""
import coat
import random
from _utils.scene_api import SceneAPI
from _utils.scope_utils import Scope, resolve_scope
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

# =============================================================================
# CONFIGURATION DEFAULTS
# =============================================================================

DEFAULT_LAYER_NAME: str = "IDMap"
DEFAULT_MIN_COLOR: int = 0


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _fill_element_with_random_color(
    element: coat.SceneElement,
    min_color: int = DEFAULT_MIN_COLOR
) -> None:
    """Fill a single element with a random RGB color using ghost isolation."""
    # Unghost this element, fill, re-ghost
    element.setGhost(False)

    # Generate random color
    r: float = random.uniform(min_color, 255)
    g: float = random.uniform(min_color, 255)
    b: float = random.uniform(min_color, 255)

    coat.Volume.color(r, g, b)
    coat.ui.cmd(CMD_FILL_LAYER)

    # Re-ghost so next element can be filled in isolation
    element.setGhost(True)


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.TREE,
    layer_name: str = DEFAULT_LAYER_NAME,
    min_color: int = DEFAULT_MIN_COLOR,
    restore_layer: bool = True,
) -> int:
    """
    Fill objects with random ID colors.

    Args:
        scope: Which objects to fill (TREE = selected + children, ALL = everything)
        layer_name: Name of the layer to create/use for ID colors
        min_color: Minimum RGB value (0-255) to avoid pure black
        restore_layer: Whether to restore Layer 0 as active after operation

    Returns:
        Number of objects filled
    """
    # Get current element for reference (needed for TREE scope and selection restore)
    active_element: coat.SceneElement | None = SceneAPI.get_current_element()

    if not active_element and scope == Scope.TREE:
        show_error("No object selected", 2000)
        return 0

    # Resolve which elements to operate on
    elements: list[coat.SceneElement] = resolve_scope(scope)

    if not elements:
        show_error("No objects to process", 2000)
        return 0

    # Save original pen depth
    original_pen_depth: float = coat.ui.getSliderValue(SETTING_PEN_DEPTH)

    # Set pen depth to 0 for color-only filling
    coat.ui.setSliderValue(SETTING_PEN_DEPTH, 0)

    # Switch to IDMap layer (creates if not exists)
    layer_id: int = coat.Scene.getLayer(layer_name, True)
    coat.Scene.setActiveLayer(layer_id)
    coat.Scene.setLayerDepthOpacity(layer_id, 0)

    # Collect ALL scene elements for ghost management
    all_elements: list[coat.SceneElement] = SceneAPI.collect_all_sculpt_objects()

    # Cache ghost states for restoration
    ghost_cache: dict[int, bool] = cache_ghost_states(all_elements)

    # Ghost everything in the scene
    ghost_elements(all_elements)

    # Fill each element (unghost one at a time)
    count: int = 0
    for el in elements:
        if el.isSculptObject():
            _fill_element_with_random_color(el, min_color)
            count += 1

    # Restore original ghost states
    restore_ghost_states(all_elements, ghost_cache)

    # Restore original selection
    if active_element:
        active_element.selectOne()

    # Restore layer and pen depth
    if restore_layer:
        coat.Scene.setActiveLayer(coat.Scene.getLayer("Layer 0", True))
    coat.ui.setSliderValue(SETTING_PEN_DEPTH, original_pen_depth)

    show_message(f"Filled {count} objects with ID colors", 2000)
    return count
