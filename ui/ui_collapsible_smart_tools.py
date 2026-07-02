"""
LKS UI - Other Tools Collapsible Section.

A collapsible section containing miscellaneous mesh operations:
- ID Colors, Split Masked, Remesh+Symm, Merge Parts

Usage:
    from ui.ui_collapsible_smart_tools import create_other_section
    section = create_other_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# OTHER TOOLS SECTION FACTORY
# =============================================================================

def create_other_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible other tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with misc tools
    """
    section = CollapsibleSection(
        title="✨ Smart Actions", collapsed=True, state_key="section_smart")
    layout = section.content_layout

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

    def toggle_mesh_vox() -> None:
        try:
            from ops.SculptObject_ToggleMeshVox import main as toggle_main
            from utils.scope_utils import Scope
            count: int = toggle_main(scope=Scope.CURRENT)
            if count > 0:
                log_success("Toggled selected object between mesh and voxels")
            else:
                log_error("No objects processed")
            refresh_tree()
        except Exception as e:
            log_error(f"Toggle mesh/vox failed: {e}")

    mesh_grid = ButtonGrid(columns=2)
    mesh_grid.add_button("ID Map (🌳)", id_colors,
                         "Fill subtree with ID colors for baking")
    mesh_grid.add_button("✂️ Split Masked", split_masked,
                         "Split frozen/masked area into new object")
    mesh_grid.add_button("Safe Symmetrize", remesh_resymm,
                         "Remesh and symmetrize selection safely")
    mesh_grid.add_button("Merge Parts", merge_preserve,
                         "Merge subtree preserving parts")
    mesh_grid.add_button("Mesh↔Vox", toggle_mesh_vox,
                         "Toggle selected object between surface and voxel modes")
    layout.addWidget(mesh_grid)

    return section


# Alias for backwards compatibility
create_smart_section = create_other_section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_other_section(*args, **kwargs):  # type: ignore
        return None
    create_smart_section = create_other_section
