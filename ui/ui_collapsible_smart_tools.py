"""
LKS UI - Other Tools Collapsible Section.

A collapsible section containing miscellaneous mesh operations:
- ID Colors, Smart Split, Remesh+Symm, Merge Parts

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
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QSizePolicy
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    from utils.ui.widgets.sub_header import create_sub_header
    from utils.ui.widgets.badge_button import _make_icon_from_svg
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.menu_action_tooltip import action_menu_tooltip

    _SPLIT_ICON: QIcon = _make_icon_from_svg("split")
    _ADD_ICON: QIcon = _make_icon_from_svg("add")
    _MODE_CONVERT_ICON: QIcon = _make_icon_from_svg("mode_convert")

    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_HELP = MarkdownFileResource("data/tooltips/help_smart.md", base_dir=__file__)


# =============================================================================
# OTHER TOOLS SECTION FACTORY
# =============================================================================

def create_other_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create a collapsible other tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget with misc tools
    """
    section = CollapsibleSection(
        title="Smart Actions", icon_name="smart", collapsed=True, state_key="section_smart",
        help_text=_HELP.text,
    )
    layout = section.content_layout

    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    def id_colors() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_IdColors import main as id_colors_op
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Filling ID colors", _log_info, log_success)
            id_colors_op(scope=Scope.TREE, progress_callback=ctx.on_progress)
            log_success("Applied ID colors")
            refresh_tree()
        except Exception as e:
            log_error(f"ID colors failed: {e}")

    def split_masked() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_SmartSplit import main as split_main
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Splitting", _log_info, log_success)
            count: int = split_main(scope=Scope.CURRENT, close_holes=True,
                                    progress_callback=ctx.on_progress)
            if count > 0:
                log_success(f"Smart split - {count} new objects")
            else:
                log_error("No objects created from split")
            refresh_tree()
        except Exception as e:
            log_error(f"Smart split failed: {e}")

    def remesh_resymm() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_RemeshResymm import main as remesh_main
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Remeshing+symm", _log_info, log_success)
            count: int = remesh_main(scope=Scope.CURRENT,
                                     progress_callback=ctx.on_progress)
            if count > 0:
                log_success(f"Remeshed + symmetrized {count} object(s)")
            else:
                log_error("No objects processed")
            refresh_tree()
        except Exception as e:
            log_error(f"Remesh+symm failed: {e}")

    def merge_preserve() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_MergePreserveParts import main as merge_main
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Merging", _log_info, log_success)
            count: int = merge_main(scope=Scope.TREE,
                                    progress_callback=ctx.on_progress)
            if count > 0:
                log_success(f"Merged {count} objects preserving parts")
            else:
                log_error("No objects merged")
            refresh_tree()
        except Exception as e:
            log_error(f"Merge failed: {e}")

    def toggle_mesh_vox() -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_ToggleMeshVox import main as toggle_main
            from utils.scope_utils import Scope
            ctx = make_iteration_context("Toggling mesh/vox", _log_info, log_success)
            count: int = toggle_main(scope=Scope.CURRENT,
                                     progress_callback=ctx.on_progress)
            if count > 0:
                log_success("Toggled selected object between mesh and voxels")
            else:
                log_error("No objects processed")
            refresh_tree()
        except Exception as e:
            log_error(f"Toggle mesh/vox failed: {e}")

    mesh_grid = ButtonGrid(columns=2)
    mesh_grid.add_button(
        "ID Map (Tree)",
        id_colors,
        action_menu_tooltip(
            "Fill subtree with ID colors for baking",
            "SculptObject_IdColors_FromParts.py",
        ),
    )
    mesh_grid.add_button(
        "Smart Split",
        split_masked,
        action_menu_tooltip(
            "Voxel mode: splits hidden area into new objects. Surface mode: splits masked/frozen area and closes holes.",
            "SculptObject_SmartSplit_Selected.py",
        ),
        icon=_SPLIT_ICON,
    )
    mesh_grid.add_button(
        "Safe Symmetrize",
        remesh_resymm,
        action_menu_tooltip(
            "Remesh and symmetrize selection safely",
            "SculptObject_RemeshResymm_Safe_Selected.py",
        ),
    )
    mesh_grid.add_button(
        "Merge Parts",
        merge_preserve,
        action_menu_tooltip(
            "Merge subtree preserving parts",
            "SculptObject_Merge_PreserveParts_Subtree.py",
        ),
        icon=_ADD_ICON,
    )
    mesh_grid.add_button(
        "Mesh↔Vox",
        toggle_mesh_vox,
        action_menu_tooltip(
            "Toggle selected object between surface and voxel modes",
            "SculptObject_ToggleMeshVox_Selected.py",
        ),
        icon=_MODE_CONVERT_ICON,
    )
    mesh_grid.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    layout.addWidget(mesh_grid)
    layout.addStretch()

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
