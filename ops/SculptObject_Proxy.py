"""
SculptObject_Proxy Operator

Toggle proxy mode (decimation/reduction cache) on sculpt objects.
Proxy mode provides faster viewport performance while preserving full resolution.

Supports multiple proxy types:
- Decimate: 16X, 8X, 4X, 2X (destructive decimation-based)
- Reduce: 8X, 4X, 2X (non-destructive reduction)

Uses scope resolution to determine which elements to operate on.
"""
import coat
from utils.scene_api import SceneAPI
from utils.scope_utils import Scope, resolve_scope
from utils.Volume_proxy_utils import toggle_proxy, ProxyType, DEFAULT_PROXY_TYPE
from utils.coat_ui_utils import show_message, show_error


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _proxy_element(element: coat.SceneElement, proxy_type: ProxyType) -> bool:
    """
    Toggle proxy mode on a single element.

    Returns:
        True if element was processed, False if skipped
    """
    if not element.isSculptObject():
        return False

    # Select element for operation
    element.selectOne()
    toggle_proxy(proxy_type)
    return True


# =============================================================================
# MAIN OPERATOR
# =============================================================================

def main(
    scope: Scope = Scope.CURRENT,
    proxy_type: ProxyType = DEFAULT_PROXY_TYPE,
    preserve_selection: bool = True,
) -> int:
    """
    Toggle proxy mode on objects.

    Args:
        scope: Which objects to operate on
        proxy_type: Type of proxy to toggle (DECIMATE_16X, REDUCE_8X, etc.)
        preserve_selection: Whether to restore selection after operation

    Returns:
        Number of objects processed
    """
    # Save selection for restoration
    current: coat.SceneElement | None = None
    if preserve_selection:
        current = SceneAPI.get_current_element()

    # Validate for scope-dependent operations
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
        if _proxy_element(el, proxy_type):
            count += 1

    # Restore selection
    if preserve_selection and current:
        current.selectOne()

    # Status message - extract friendly name from enum
    type_name: str = proxy_type.name.replace("_", " ").title()
    show_message(f"Toggled {type_name} proxy on {count} objects", 2000)
    return count
