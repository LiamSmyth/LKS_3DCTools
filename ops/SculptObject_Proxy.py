"""
SculptObject_Proxy Operator

Toggle proxy mode (decimation/reduction cache) on sculpt objects.
Proxy mode provides faster viewport performance while preserving full resolution.

Proxy system has two steps:
1. Set proxy mode ($Decimate16X, $Reduce8X, etc.) - configures HOW objects will be proxied
2. Apply caching ($ToggleCachingVolume) - actually proxies/unproxies objects

Supports multiple proxy modes:
- Decimate: 16X, 8X, 4X, 2X (destructive decimation-based, more accurate)
- Reduce: 8X, 4X, 2X (non-destructive reduction, faster)

Uses scope resolution to determine which elements to operate on.
"""
import coat
from utils.scene_api import SceneAPI, SelectionAPI
from utils.scope_utils import Scope, resolve_scope
from utils.Volume_proxy_utils import (
    set_proxy_mode, toggle_caching, ProxyMode, DEFAULT_PROXY_MODE
)
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _proxy_element(element: coat.SceneElement, proxy_mode: ProxyMode) -> bool:
    """
    Toggle proxy mode on a single element.

    Args:
        element: The SceneElement to proxy
        proxy_mode: The proxy mode to use

    Returns:
        True if element was processed, False if skipped
    """
    if not element.isSculptObject():
        return False

    # Select element for operation
    element.selectOne()

    # Set proxy mode first, then toggle caching
    set_proxy_mode(proxy_mode)
    toggle_caching()
    return True


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    proxy_mode: ProxyMode = DEFAULT_PROXY_MODE,
    preserve_selection: bool = True,
) -> int:
    """
    Toggle proxy mode on objects.

    Args:
        scope: Which objects to operate on
        proxy_mode: Mode of proxy to toggle (DECIMATE_16X, REDUCE_8X, etc.)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects processed
    """
    # Save selection for restoration
    saved_selection: list[coat.SceneElement] = []
    if preserve_selection:
        saved_selection = SelectionAPI.save_selection()

    # Validation for scope check should use a separate variable
    current: coat.SceneElement | None = SceneAPI.get_current_element()
    if scope in (Scope.CURRENT, Scope.TREE) and not current:
        show_error("No object selected", 2000)
        return 0

    # Resolve which elements to operate on
    elements: list[coat.SceneElement] = resolve_scope(scope)

    if not elements:
        show_error("No objects to process", 2000)
        return 0

    # Process each element
    count: int = 0
    for el in elements:
        if _proxy_element(el, proxy_mode):
            count += 1

    # Restore selection
    if preserve_selection and saved_selection:
        SelectionAPI.restore_selection(saved_selection)

    # Status message - extract friendly name from enum
    mode_name: str = proxy_mode.name.replace("_", " ").title()
    show_message(f"Toggled {mode_name} proxy on {count} objects", 2000)
    return count
