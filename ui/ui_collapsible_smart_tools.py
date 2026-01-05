"""
LKS UI - Smart Actions Collapsible Section.

A collapsible section containing smart mesh operations:
- Mesh Operations (ID Colors, Split Masked, Remesh+Symm, Merge Parts)
- VoxBool Operations (Subtract, Intersect, Union)

Usage:
    from ui.ui_collapsible_smart_tools import create_smart_section
    section = create_smart_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from ui.ui_widget_sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# SMART ACTIONS SECTION FACTORY
# =============================================================================

def create_smart_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible smart actions section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with smart tools
    """
    section = CollapsibleSection(
        title="🧠 Smart Actions", color="#fff176", collapsed=True)
    layout = section.content_layout

    # --- Mesh Operations ---
    layout.addWidget(create_sub_header("Mesh Operations"))

    def id_colors() -> None:
        try:
            from ops.SculptObject_IdColors import main as id_colors_op
            from utils.scope_utils import Scope
            id_colors_op(scope=Scope.TREE)
            log_success("Applied ID colors")
            refresh_tree()
        except Exception as e:
            log_error(f"ID colors failed: {e}")

    def split_masked() -> None:
        try:
            from ops.SculptObject_SplitMasked import main as split_main
            from utils.scope_utils import Scope
            count: int = split_main(scope=Scope.CURRENT, close_holes=True)
            if count > 0:
                log_success(f"Split masked - {count} new objects")
            else:
                log_error("No objects created from split")
            refresh_tree()
        except Exception as e:
            log_error(f"Split failed: {e}")

    def remesh_resymm() -> None:
        try:
            from ops.SculptObject_RemeshResymm import main as remesh_main
            from utils.scope_utils import Scope
            count: int = remesh_main(scope=Scope.CURRENT)
            if count > 0:
                log_success(f"Remeshed + symmetrized {count} object(s)")
            else:
                log_error("No objects processed")
            refresh_tree()
        except Exception as e:
            log_error(f"Remesh+symm failed: {e}")

    def merge_preserve() -> None:
        try:
            from ops.SculptObject_MergePreserveParts import main as merge_main
            from utils.scope_utils import Scope
            count: int = merge_main(scope=Scope.TREE)
            if count > 0:
                log_success(f"Merged {count} objects preserving parts")
            else:
                log_error("No objects merged")
            refresh_tree()
        except Exception as e:
            log_error(f"Merge failed: {e}")

    mesh_grid = ButtonGrid(columns=2)
    mesh_grid.add_button("ID Colors", id_colors, "Fill with ID colors")
    mesh_grid.add_button("Split Masked", split_masked, "Split frozen/masked")
    mesh_grid.add_button("Remesh+Symm", remesh_resymm, "Remesh and symmetrize")
    mesh_grid.add_button("Merge Parts", merge_preserve,
                         "Merge preserving parts")
    layout.addWidget(mesh_grid)

    # --- VoxBool Operations ---
    layout.addWidget(create_sub_header("VoxBool (Create Child)"))

    def voxbool_subtract() -> None:
        try:
            from ops.SculptObject_VoxBool import subtract
            child = subtract()
            if child:
                log_success(f"Created subtract: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create subtract child")
        except Exception as e:
            log_error(f"VoxBool subtract failed: {e}")

    def voxbool_intersect() -> None:
        try:
            from ops.SculptObject_VoxBool import intersect
            child = intersect()
            if child:
                log_success(f"Created intersect: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create intersect child")
        except Exception as e:
            log_error(f"VoxBool intersect failed: {e}")

    def voxbool_union() -> None:
        try:
            from ops.SculptObject_VoxBool import union
            child = union()
            if child:
                log_success(f"Created union: {child.name()}")
                refresh_tree()
            else:
                log_error("Failed to create union child")
        except Exception as e:
            log_error(f"VoxBool union failed: {e}")

    voxbool_grid = ButtonGrid(columns=3)
    voxbool_grid.add_button("Subtract", voxbool_subtract,
                            "Create subtract boolean child")
    voxbool_grid.add_button("Intersect", voxbool_intersect,
                            "Create intersect boolean child")
    voxbool_grid.add_button("Union", voxbool_union,
                            "Create union boolean child")
    layout.addWidget(voxbool_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_smart_section(*args, **kwargs):  # type: ignore
        return None
