"""
LKS UI - Proxy/Cache Tools Collapsible Section.

A collapsible section containing proxy/cache operations with:
- "Proxy mode:" label + dial-enum picker for selecting the reduction mode
- Set Proxied / Set Unproxied / Toggle Proxied scope rows (inline)
- Native cache operations (Cache Visible, Uncache, Clear All)

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
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
    from utils.ui.widgets import CollapsibleSection, ScopeButtonRow
    from utils.ui.widgets.badge_button import make_badge_button
    from utils.ui.widgets.markdown_file_resource import MarkdownFileResource
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


# Text resources for tooltips (module-local directory)
_HELP = MarkdownFileResource("data/tooltips/help_proxy.md", base_dir=__file__)


# =============================================================================
# PROXY SECTION FACTORY
# =============================================================================

def create_proxy_section(
    log_success: Callable[[str], None],
    log_error: Callable[[str], None],
    refresh_tree: Callable[[], None],
    log_info: Callable[[str], None] | None = None,
) -> "QWidget":
    """
    Create a collapsible proxy/cache tools section.

    Args:
        log_success: Callback for success messages
        log_error: Callback for error messages
        refresh_tree: Callback to refresh scene tree
        log_info: Callback for info/progress messages (falls back to log_success)

    Returns:
        CollapsibleSection widget with proxy tools
    """
    import coat
    from utils.Volume_proxy_utils import ProxyMode
    from lks_utils.gui_qt.widgets.q_dial_enum_picker import QDialEnumPicker
    from lks_utils.gui_qt.widgets.dial_enum_option import DialEnumOption

    # Resolve the info logger (falls back to success if not provided)
    _log_info: Callable[[str], None] = log_info if log_info is not None else log_success

    from utils.ui.progress import make_iteration_context

    section = CollapsibleSection(
        title="Proxy / Cache", icon_name="proxy", collapsed=True, state_key="section_proxy",
        help_text=_HELP.text,
    )
    # ── Nice display names for proxy modes ─────────────────────────────
    _PROXY_MODE_LABELS: dict[ProxyMode, str] = {
        ProxyMode.DECIMATE_16X: "Decimate 16x",
        ProxyMode.DECIMATE_8X: "Decimate 8x",
        ProxyMode.DECIMATE_4X: "Decimate 4x",
        ProxyMode.DECIMATE_2X: "Decimate 2x",
        ProxyMode.REDUCE_8X: "Reduce 8x",
        ProxyMode.REDUCE_4X: "Reduce 4x",
        ProxyMode.REDUCE_2X: "Reduce 2x",
    }

    # ── Dial enum picker for proxy mode ────────────────────────────────
    picker = QDialEnumPicker(
        options=[
            DialEnumOption(value=mode, label=_PROXY_MODE_LABELS[mode])
            for mode in ProxyMode
        ],
        current_index=0,
        width=150,
        height=22,
    )
    picker.setToolTip("Proxy reduction multiplier — scroll or click arrow to change")

    # ── Row 1: Proxy mode label + picker ───────────────────────────────
    mode_row = QWidget()
    mode_row_layout = QHBoxLayout(mode_row)
    mode_row_layout.setContentsMargins(0, 0, 0, 0)
    mode_row_layout.setSpacing(4)
    mode_label = QLabel("Proxy mode:")
    mode_label.setStyleSheet("color: #ddd; font-size: 11px;")
    mode_row_layout.addWidget(mode_label)
    mode_row_layout.addWidget(picker)
    mode_row_layout.addStretch()
    section.content_layout.addWidget(mode_row)

    # ── Proxy operation helpers ────────────────────────────────────────
    def _proxy_op(scope_name: str, action: str) -> None:
        """Apply a proxy action to objects in the given scope.

        action:  "set_proxied" | "set_unproxied" | "toggle"
        """
        try:
            from utils.scope_utils import Scope, resolve_scope
            from utils.Volume_proxy_utils import set_proxy_mode, toggle_caching

            proxy_mode: ProxyMode = picker.current_value()
            scope = getattr(Scope, scope_name)
            elements = resolve_scope(scope)

            if not elements:
                log_error("No objects in scope")
                return

            count: int = 0
            total: int = len(elements)
            action_verb: str = {
                "set_proxied": "Proxying", "set_unproxied": "Unproxying", "toggle": "Toggling",
            }[action]
            progress = make_iteration_context(action_verb, _log_info)
            for i, el in enumerate(elements):
                if not el.isSculptObject():
                    continue
                if progress.on_progress:
                    progress.on_progress(i, total, el.name())
                el.selectOne()
                set_proxy_mode(proxy_mode)

                if action == "toggle":
                    toggle_caching()
                    count += 1
                else:
                    currently_cached: bool = coat.is_proxy()
                    if action == "set_proxied" and not currently_cached:
                        toggle_caching()
                        count += 1
                    elif action == "set_unproxied" and currently_cached:
                        toggle_caching()
                        count += 1

            display_name: str = _PROXY_MODE_LABELS.get(proxy_mode, proxy_mode.name)
            action_verb: str = {
                "set_proxied": "Proxied",
                "set_unproxied": "Unproxied",
                "toggle": "Toggled",
            }[action]
            log_success(f"{action_verb} {display_name} on {count} objects")
            refresh_tree()
        except Exception as e:
            log_error(f"Proxy operation failed: {e}")

    # ── Row 2: Set Proxied / Set Unproxied / Toggle scope rows ────────
    _SCOPE_KEY_MAP: dict[str, str] = {
        "sel": "CURRENT", "tree": "TREE", "all": "ALL",
    }

    def _make_scope_row(action: str, verb: str) -> ScopeButtonRow:
        """Create a ScopeButtonRow for a proxy action."""
        row = ScopeButtonRow()
        for key in ("sel", "tree", "all"):
            scope_enum = _SCOPE_KEY_MAP[key]
            row.set_callback(key, lambda *, k=scope_enum: _proxy_op(k, action))
        row.set_tooltips(
            sel=f"{verb} proxy on selected",
            tree=f"{verb} proxy on subtree",
            all=f"{verb} proxy on all objects",
        )
        return row

    action_row = QWidget()
    action_row_layout = QHBoxLayout(action_row)
    action_row_layout.setContentsMargins(0, 0, 0, 0)
    action_row_layout.setSpacing(2)

    # Set Proxied
    p_label = QLabel("Set Proxied")
    p_label.setStyleSheet("color: #888; font-size: 11px; padding: 0 3px 0 0;")
    action_row_layout.addWidget(p_label)
    action_row_layout.addWidget(_make_scope_row("set_proxied", "Set proxied"))

    # Spacer between groups
    action_row_layout.addSpacing(6)

    # Set Unproxied
    u_label = QLabel("Set Unproxied")
    u_label.setStyleSheet("color: #888; font-size: 11px; padding: 0 3px 0 0;")
    action_row_layout.addWidget(u_label)
    action_row_layout.addWidget(_make_scope_row("set_unproxied", "Set unproxied"))

    # Spacer between groups
    action_row_layout.addSpacing(6)

    # Toggle
    t_label = QLabel("Toggle")
    t_label.setStyleSheet("color: #888; font-size: 11px; padding: 0 3px 0 0;")
    action_row_layout.addWidget(t_label)
    action_row_layout.addWidget(_make_scope_row("toggle", "Toggle"))

    action_row_layout.addStretch()
    section.content_layout.addWidget(action_row)

    # ── Cache buttons ──────────────────────────────────────────────────
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

    cache_row = QWidget()
    cache_row_layout = QHBoxLayout(cache_row)
    cache_row_layout.setContentsMargins(0, 0, 0, 0)
    cache_row_layout.setSpacing(4)

    btn_cache = make_badge_button("proxy", "Cache Visible", "Cache all visible objects (native)")
    btn_cache.clicked.connect(on_cache_visible)
    cache_row_layout.addWidget(btn_cache)

    btn_uncache = make_badge_button("proxy", "Uncache Visible", "Uncache all visible objects")
    btn_uncache.clicked.connect(on_uncache_visible)
    cache_row_layout.addWidget(btn_uncache)

    btn_clear = make_badge_button("clear", "Clear All Caches", "Clear all cached objects")
    btn_clear.clicked.connect(on_clear_caches)
    cache_row_layout.addWidget(btn_clear)

    cache_row_layout.addStretch()
    section.content_layout.addWidget(cache_row)

    section.content_layout.addStretch()

    return section


# =============================================================================
# STUB FOR NO QT
# =============================================================================

if not HAS_QT:
    def create_proxy_section(*args, **kwargs):  # type: ignore
        return None
