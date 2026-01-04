"""
LKS Utilities Package

Shared utilities for LKS 3DCoat addon scripts.

Module Organization:
- scene_api.py: Thin wrappers around 3DCoat scene iteration (SceneAPI, SelectionAPI)
- scope_utils.py: Scope enum and resolution (CURRENT/TREE/OTHER/ALL)
- SceneElement_visibility_utils.py: Pure functions for visibility/ghost manipulation
- Scene_layer_utils.py: Layer management utilities
- coat_ui_utils.py: UI command abstractions (magic strings hidden here)
- object_utils.py: Object validation and manipulation
- Volume_*_utils.py: Volume mesh operations (raw args pattern)
- Scene_cleanup_utils.py: Scene cleanup after mesh operations
- lks_settings.py: Persistent settings cache
- brush_settings_utils.py: Brush configuration utilities
- autopo_utils.py: Autopo workflow automation
- SceneElement_boolean_utils.py: Live boolean operations
- Scene_tiling_utils.py: Tiling grid setup
"""

# Settings
from _utils.lks_settings import get_settings, save_settings

# Scene API - Primary interface for context/iteration
from _utils.scene_api import (
    SceneAPI,
    SelectionAPI,
    apply_to_elements,
    filter_elements,
    filter_sculpt_objects,
    deduplicate_elements,
)

# Scope utilities - Scope resolution
from _utils.scope_utils import (
    Scope,
    resolve_scope,
    apply_to_scope,
    # Deprecated but kept for compatibility
    get_selected_elements,
    restore_selection,
    get_elements_by_scope,
    collect_tree_elements,
)

# Visibility utilities - Pure functions for visibility/ghost
from _utils.SceneElement_visibility_utils import (
    set_visibility,
    hide_elements,
    show_elements,
    set_ghost,
    ghost_elements,
    unghost_elements,
    invert_visibility_on_elements,
    invert_ghost_on_elements,
    hide_except,
    ghost_except,
)

# Layer utilities
from _utils.Scene_layer_utils import (
    LAYER_SCULPT,
    LAYER_COLOR,
    ensure_standard_layers,
    activate_sculpt_layer,
    activate_color_layer,
    cleanup_after_destructive_op,
    get_current_layer_name,
)

# UI utilities
from _utils.coat_ui_utils import (
    # Constants
    CMD_DIALOG_OK,
    CMD_DIALOG_CANCEL,
    ROOM_SCULPT,
    ROOM_RETOPO,
    ROOM_PAINT,
    # Functions
    confirm_dialog,
    cancel_dialog,
    command_with_confirm,
    switch_to_room,
    ensure_sculpt_room,
    ensure_retopo_room,
    ensure_paint_room,
    show_message,
    show_error,
    wait_frames,
)

# Object utilities
from _utils.object_utils import (
    ObjectUtils,
    scale_element,
    scale_element_with_select,
    scale_elements,
)

# Volume utilities - Decimate (raw args pattern)
from _utils.Volume_decimate_utils import (
    execute_decimate,
    decimate_by_percent,
    decimate_to_target,
    decimate_to_half,
    decimate_16x,
)

# Volume utilities - Resample (raw args pattern)
from _utils.Volume_resample_utils import (
    execute_resample,
    resample_to_half,
    resample_to_target,
)

# Volume utilities - Subdivide (raw args pattern)
from _utils.Volume_subdivide_utils import (
    subdivide_once,
    make_symmetrical,
)

# Volume utilities - Mode Convert (raw args pattern)
from _utils.Volume_mode_utils import (
    convert_to_surface,
    convert_to_voxels,
    ensure_surface_mode,
    resample_and_voxelize,
)

# Volume utilities - Density Matching (raw args pattern)
from _utils.Volume_density_utils import (
    calculate_target_polycount_by_scale,
    resample_to_match_density,
    smart_match_density,
)

# Scene utilities - Cleanup
from _utils.Scene_cleanup_utils import (
    cleanup_after_mesh_operation,
)

# Scene iteration utilities (legacy, prefer SceneAPI)
from _utils.scene_iteration_utils import SceneIterationUtils

# Brush settings utilities
from _utils.brush_settings_utils import BrushSettingsUtils
