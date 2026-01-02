"""
Layer Management Utilities

Provides utilities for managing sculpt layers in 3DCoat.

Standard Layer Contract (from design):
- Layer 0: Sculpt detail (100% Depth, 0% Color)
- Layer 1: Color/material (0% Depth, 100% Color)

Known Gotchas:
- Decimate and other operations auto-create layers
- Layer order is not guaranteed after operations
- Duplicate names are allowed
- Layer indices can shift

Verified API (from coat.pyi - all on coat.Scene):
- getLayer(name, addIfNotExists=True) -> int
- getLayerName(LayerID) -> str
- setLayerName(LayerID, name)
- getCurrentLayer() -> int
- setCurrentLayer(LayerID)
- setActiveLayer(LayerID)
- removeLayer(LayerID)
- removeEmptyLayers()
- layerIsEmpty(layerID) -> bool
- layerVisible(LayerID) -> bool
- setLayerVisibility(LayerID, Visible)
- setLayerColorOpacity(LayerID, Opacity: float)
- setLayerDepthOpacity(LayerID, Opacity: float)
- setLayerGlossOpacity(LayerID, Opacity: float)
- setLayerMetalnessOpacity(LayerID, Opacity: float)
- mergeVisibleLayers()
- mergeLayerDown(LayerID)
"""
import coat


# =============================================================================
# CONSTANTS
# =============================================================================

# Standard layer names
LAYER_SCULPT: str = "Sculpt"  # Layer 0 - depth only
LAYER_COLOR: str = "Color"    # Layer 1 - color only

# Opacity values
OPACITY_FULL: float = 1.0
OPACITY_NONE: float = 0.0


def ensure_standard_layers() -> None:
    """
    Ensure the scene has exactly two layers with correct settings:
    - Layer 0 (Sculpt): 100% Depth, 0% Color  
    - Layer 1 (Color): 0% Depth, 100% Color

    Strategy:
    1. Remove empty layers first
    2. Merge all visible layers down to consolidate
    3. Rename the base layer to "Sculpt" and configure it
    4. Create "Color" layer on top and configure it
    5. Activate the Sculpt layer
    """
    # Step 1: Remove any empty layers
    coat.Scene.removeEmptyLayers()

    # Step 2: Merge all visible layers to consolidate
    coat.Scene.mergeVisibleLayers()

    # Step 3: After merge, we should have one layer at index 0
    # Rename it to "Sculpt" and configure as depth-only
    base_layer_name: str = coat.Scene.getLayerName(0)
    if base_layer_name != LAYER_SCULPT:
        coat.Scene.setLayerName(0, LAYER_SCULPT)

    # Configure Layer 0 (Sculpt) - depth only
    coat.Scene.setLayerDepthOpacity(0, OPACITY_FULL)
    coat.Scene.setLayerColorOpacity(0, OPACITY_NONE)
    coat.Scene.setLayerGlossOpacity(0, OPACITY_NONE)
    coat.Scene.setLayerMetalnessOpacity(0, OPACITY_NONE)

    # Step 4: Get or create the Color layer
    # Use addIfNotExists=True to create if needed
    color_layer: int = coat.Scene.getLayer(LAYER_COLOR, True)

    # Configure Layer 1 (Color) - color only
    coat.Scene.setLayerDepthOpacity(color_layer, OPACITY_NONE)
    coat.Scene.setLayerColorOpacity(color_layer, OPACITY_FULL)
    coat.Scene.setLayerGlossOpacity(color_layer, OPACITY_FULL)
    coat.Scene.setLayerMetalnessOpacity(color_layer, OPACITY_FULL)

    # Step 5: Activate the sculpt layer
    coat.Scene.setActiveLayer(0)
    coat.Scene.setCurrentLayer(0)


def activate_sculpt_layer() -> None:
    """Activate Layer 0 (Sculpt layer) for sculpting."""
    sculpt_layer: int = coat.Scene.getLayer(LAYER_SCULPT, True)
    coat.Scene.setActiveLayer(sculpt_layer)
    coat.Scene.setCurrentLayer(sculpt_layer)


def activate_color_layer() -> None:
    """Activate Layer 1 (Color layer) for painting."""
    color_layer: int = coat.Scene.getLayer(LAYER_COLOR, True)
    coat.Scene.setActiveLayer(color_layer)
    coat.Scene.setCurrentLayer(color_layer)


def cleanup_after_destructive_op() -> None:
    """
    Clean up layer state after a destructive operation (decimate, etc).

    Many operations create unwanted layers. This:
    1. Removes empty layers
    2. Ensures standard layers exist with correct settings
    3. Activates the sculpt layer
    """
    # Remove empty layers that were created
    coat.Scene.removeEmptyLayers()

    # Ensure we're back to standard state
    ensure_standard_layers()


def get_current_layer_name() -> str:
    """Get the name of the currently active layer."""
    layer_id: int = coat.Scene.getCurrentLayer()
    return coat.Scene.getLayerName(layer_id)


def set_layer_depth_only(layer_name: str) -> None:
    """Configure a layer for depth-only (sculpting)."""
    layer_id: int = coat.Scene.getLayer(layer_name, False)
    if layer_id >= 0:
        coat.Scene.setLayerDepthOpacity(layer_id, OPACITY_FULL)
        coat.Scene.setLayerColorOpacity(layer_id, OPACITY_NONE)
        coat.Scene.setLayerGlossOpacity(layer_id, OPACITY_NONE)
        coat.Scene.setLayerMetalnessOpacity(layer_id, OPACITY_NONE)


def set_layer_color_only(layer_name: str) -> None:
    """Configure a layer for color-only (painting)."""
    layer_id: int = coat.Scene.getLayer(layer_name, False)
    if layer_id >= 0:
        coat.Scene.setLayerDepthOpacity(layer_id, OPACITY_NONE)
        coat.Scene.setLayerColorOpacity(layer_id, OPACITY_FULL)
        coat.Scene.setLayerGlossOpacity(layer_id, OPACITY_FULL)
        coat.Scene.setLayerMetalnessOpacity(layer_id, OPACITY_FULL)


def remove_layer_by_name(layer_name: str) -> bool:
    """
    Remove a layer by name.

    Returns True if layer was found and removed.
    """
    layer_id: int = coat.Scene.getLayer(layer_name, False)
    if layer_id >= 0:
        coat.Scene.removeLayer(layer_id)
        return True
    return False


def merge_all_visible() -> None:
    """Merge all visible layers into one."""
    coat.Scene.mergeVisibleLayers()
