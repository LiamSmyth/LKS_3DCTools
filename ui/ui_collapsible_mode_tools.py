"""
LKS UI - Mode Conversion Tools Section.

Collapsible section for converting between surface and voxel modes.

Usage:
    from ui.ui_collapsible_mode_tools import create_mode_section
    section = create_mode_section(log_success, log_error, refresh_tree)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget
    from utils.ui.widgets import CollapsibleSection, ScopeButtonRow, add_tooltip
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    from utils.menu_action_tooltip import action_menu_tooltip
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_LABEL_WIDTH: int = 90
_TT_TO_SURFACE = MarkdownFileResource("data/tooltips/mode_convert_to_surface.md", base_dir=__file__)
_TT_TO_VOXELS = MarkdownFileResource("data/tooltips/mode_convert_to_voxels.md", base_dir=__file__)
_HELP = MarkdownFileResource("data/tooltips/help_mode.md", base_dir=__file__)


def create_mode_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create mode conversion section with label + scope buttons pattern.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh the outliner tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget
    """
    section = CollapsibleSection(
        title="Mode Convert", icon_name="mode_convert", collapsed=True, state_key="section_mode",
        help_text=_HELP.text,
    )
    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    def on_convert(scope_name: str, to_voxels: bool) -> None:
        try:
            from utils.hot_reload import reload_if_dev; reload_if_dev()
            from ops.SculptObject_ModeConvert import main as op_mode, ConvertMode
            from utils.scope_utils import Scope
            scope = getattr(Scope, scope_name)
            mode = ConvertMode.TO_VOXELS if to_voxels else ConvertMode.TO_SURFACE
            action = "Voxelizing" if to_voxels else "Converting"
            ctx = make_iteration_context(action, _log_info, log_success)
            op_mode(scope=scope, mode=mode,
                    progress_callback=ctx.on_progress)
            mode_str = "voxels" if to_voxels else "surface"
            log_success(f"Converted {scope_name.lower()} to {mode_str}")
            refresh_tree()
        except Exception as e:
            log_error(f"Mode convert failed: {e}")

    # --- Single row: To Surface | To Voxels ---

    surf_label = QLabel("To Surface:")
    surf_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(surf_label, _TT_TO_SURFACE)
    surf_scope_row = ScopeButtonRow()
    surf_scope_row.set_callback("sel", lambda: on_convert("CURRENT", False))
    surf_scope_row.set_callback("tree", lambda: on_convert("TREE", False))
    surf_scope_row.set_callback("all", lambda: on_convert("ALL", False))
    surf_scope_row.set_tooltips(
        sel="Convert selected to surface",
        tree="Convert subtree to surface",
        all=action_menu_tooltip(
            "Convert all to surface",
            "SculptObject_ToSurface_All.py",
        ),
    )

    vox_label = QLabel("To Voxels:")
    vox_label.setFixedWidth(_LABEL_WIDTH)
    add_tooltip(vox_label, _TT_TO_VOXELS)
    vox_scope_row = ScopeButtonRow()
    vox_scope_row.set_callback("sel", lambda: on_convert("CURRENT", True))
    vox_scope_row.set_callback("tree", lambda: on_convert("TREE", True))
    vox_scope_row.set_callback("all", lambda: on_convert("ALL", True))
    vox_scope_row.set_tooltips(
        sel="Convert selected to voxels",
        tree="Convert subtree to voxels",
        all=action_menu_tooltip(
            "Convert all to voxels",
            "SculptObject_ToVoxel_All.py",
        ),
    )

    # Separator between the two groups
    sep = QLabel("")
    sep.setFixedWidth(12)

    mode_row = QWidget()
    mode_row_layout = QHBoxLayout(mode_row)
    mode_row_layout.setContentsMargins(0, 0, 0, 0)
    mode_row_layout.setSpacing(4)
    mode_row_layout.addWidget(surf_label)
    mode_row_layout.addWidget(surf_scope_row)
    mode_row_layout.addWidget(sep)
    mode_row_layout.addWidget(vox_label)
    mode_row_layout.addWidget(vox_scope_row)
    mode_row_layout.addStretch()
    section.content_layout.addWidget(mode_row)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_mode_section(*args, **kwargs):  # type: ignore
        return None
