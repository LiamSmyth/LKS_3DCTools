"""
LKS UI - Proxy/Cache Tools Collapsible Section.

A collapsible section containing proxy/cache operations with:
- Two rows of proxy mode radio buttons: Decimate (16x/8x/4x) and Reduce (8x/4x/2x)
- Toggle proxy scope buttons (Sel/Tree/All)
- Native cache operations (Cache Visible, Uncache, Clear)

Only one radio button can be selected across both rows (global mode).

Usage:
    from ui.ui_collapsible_proxy_tools import create_proxy_section
    section = create_proxy_section(log_success, log_error, refresh_tree)
    layout.addWidget(section)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QRadioButton, QButtonGroup
    from utils.ui.widgets import CollapsibleSection, ButtonGrid
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# =============================================================================
# PROXY SECTION FACTORY
# =============================================================================

def create_proxy_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
) -> "QWidget":
    """
    Create a collapsible proxy/cache tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree

    Returns:
        CollapsibleSection widget with proxy tools
    """
    import coat

    section = CollapsibleSection(
        title="⚡ Proxy / Cache", color="#80deea", collapsed=True)
    layout = section.content_layout

    # --- Proxy Mode Radio Buttons (shared button group for mutual exclusivity) ---
    proxy_mode_group = QButtonGroup()

    # Map button IDs to ProxyMode enum values
    # IDs: 0=Dec16x, 1=Dec8x, 2=Dec4x, 3=Red8x, 4=Red4x, 5=Red2x
    proxy_mode_ids: dict[int, str] = {
        0: "DECIMATE_16X",
        1: "DECIMATE_8X",
        2: "DECIMATE_4X",
        3: "REDUCE_8X",
        4: "REDUCE_4X",
        5: "REDUCE_2X",
    }

    # Row 1: "Decimate:" [16x] [8x] [4x]
    dec_row = QHBoxLayout()
    dec_row.setContentsMargins(0, 0, 0, 0)
    dec_row.setSpacing(4)

    dec_label = QLabel("Decimate:")
    dec_label.setMinimumWidth(60)
    dec_row.addWidget(dec_label)

    radio_16x = QRadioButton("16x")
    radio_16x.setChecked(True)
    proxy_mode_group.addButton(radio_16x, 0)
    dec_row.addWidget(radio_16x)

    radio_8x = QRadioButton("8x")
    proxy_mode_group.addButton(radio_8x, 1)
    dec_row.addWidget(radio_8x)

    radio_4x = QRadioButton("4x")
    proxy_mode_group.addButton(radio_4x, 2)
    dec_row.addWidget(radio_4x)

    dec_row.addStretch()

    dec_container = QWidget()
    dec_container.setLayout(dec_row)
    dec_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(dec_container)

    # Row 2: "Reduce:" [8x] [4x] [2x]
    red_row = QHBoxLayout()
    red_row.setContentsMargins(0, 0, 0, 0)
    red_row.setSpacing(4)

    red_label = QLabel("Reduce:")
    red_label.setMinimumWidth(60)
    red_row.addWidget(red_label)

    red_radio_8x = QRadioButton("8x")
    proxy_mode_group.addButton(red_radio_8x, 3)
    red_row.addWidget(red_radio_8x)

    red_radio_4x = QRadioButton("4x")
    proxy_mode_group.addButton(red_radio_4x, 4)
    red_row.addWidget(red_radio_4x)

    red_radio_2x = QRadioButton("2x")
    proxy_mode_group.addButton(red_radio_2x, 5)
    red_row.addWidget(red_radio_2x)

    red_row.addStretch()

    red_container = QWidget()
    red_container.setLayout(red_row)
    red_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(red_container)

    # --- Toggle Proxy Scope Buttons ---
    def toggle_proxy(scope_name: str) -> None:
        try:
            mode_id: int = proxy_mode_group.checkedId()

            from ops.SculptObject_Proxy import main as proxy_op
            from utils.Volume_proxy_utils import ProxyMode
            from utils.scope_utils import Scope

            scope = getattr(Scope, scope_name)
            mode_name: str = proxy_mode_ids.get(mode_id, "DECIMATE_16X")
            proxy_mode = getattr(ProxyMode, mode_name)
            count: int = proxy_op(scope=scope, proxy_mode=proxy_mode)
            display_name: str = mode_name.replace("_", " ").title()
            log_success(f"Toggled {display_name} proxy on {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Proxy toggle failed: {e}")

    toggle_row = QHBoxLayout()
    toggle_row.setContentsMargins(0, 0, 0, 0)
    toggle_label = QLabel("Toggle:")
    toggle_label.setMinimumWidth(60)
    toggle_row.addWidget(toggle_label)

    toggle_grid = ButtonGrid(columns=3)
    toggle_grid.add_button("Sel", lambda: toggle_proxy(
        "CURRENT"), "Toggle proxy on selection")
    toggle_grid.add_button("Tree", lambda: toggle_proxy(
        "TREE"), "Toggle proxy on subtree")
    toggle_grid.add_button("All", lambda: toggle_proxy(
        "ALL"), "Toggle proxy on all")
    toggle_row.addWidget(toggle_grid)

    toggle_container = QWidget()
    toggle_container.setLayout(toggle_row)
    toggle_container.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(toggle_container)

    def on_cache_visible() -> None:
        try:
            coat.ui.cmd("$CacheVisible")
            log_success("Cached visible objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Cache visible failed: {e}")

    def on_uncache_visible() -> None:
        try:
            coat.ui.cmd("$UnCacheVisible")
            log_success("Uncached visible objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Uncache visible failed: {e}")

    def on_clear_caches() -> None:
        try:
            coat.ui.cmd("$ClearAllCache")
            log_success("Cleared all caches")
            refresh_tree()
        except Exception as e:
            log_error(f"Clear caches failed: {e}")

    batch_grid = ButtonGrid(columns=2)
    batch_grid.add_button("Cache Visible", on_cache_visible,
                          "Cache all visible objects (native)")
    batch_grid.add_button(
        "Uncache Visible", on_uncache_visible, "Uncache all visible objects")
    layout.addWidget(batch_grid)

    clear_grid = ButtonGrid(columns=1)
    clear_grid.add_button("Clear All Caches",
                          on_clear_caches, "Clear all cached objects")
    layout.addWidget(clear_grid)

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_proxy_section(*args, **kwargs):  # type: ignore
        return None
