"""
Base class and decorator for LKS action scripts.

Provides automatic hot-reload and consistent behavior for all action scripts.

Usage (decorator - simplest):
    from utils.action_base import action

    @action
    def main():
        from ops.SculptObject_Decimate import main as op_main
        from utils.scope_utils import Scope
        op_main(scope=Scope.CURRENT, reduction_percent=50.0)

    main()

Usage (class - more features):
    from utils.action_base import Action

    class DecimateHalfSelected(Action):
        '''Decimate selected to 50%.'''
        room = "Sculpt"  # Optional room validation

        def execute(self) -> None:
            from ops.SculptObject_Decimate import main as op_main
            from utils.scope_utils import Scope
            op_main(scope=Scope.CURRENT, reduction_percent=50.0)

    DecimateHalfSelected().run()
"""
from __future__ import annotations

import functools
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


# =============================================================================
# DECORATOR (simplest approach)
# =============================================================================

def action(func: F) -> F:
    """
    Decorator that adds hot-reload before running an action.

    Usage:
        @action
        def main():
            from ops.SomeOperator import main as op_main
            op_main(...)

        main()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # CRITICAL: Force reload of hot_reload module itself first!
        # Otherwise we use the cached version which won't reload properly.
        import sys
        import importlib
        if "utils.hot_reload" in sys.modules:
            importlib.reload(sys.modules["utils.hot_reload"])

        # Now hot reload all LKS modules
        from utils.hot_reload import reload_all
        reload_all()

        # Execute the action
        try:
            return func(*args, **kwargs)
        finally:
            # Queue the calling module for cache clearing
            # The LKS extension's postprocess() will clear it next frame
            _queue_module_for_clearing()

    return wrapper  # type: ignore


def _queue_module_for_clearing() -> None:
    """
    Queue action script modules for deferred cache clearing.

    3DCoat imports scripts as Python modules. Python caches these in sys.modules,
    so subsequent menu clicks don't re-execute the file.

    We can't delete immediately because Python's import machinery is still on
    the call stack. Instead, we queue module names and the LKS extension's 
    postprocess() hook clears them on the next frame.
    """
    import sys

    # Initialize the queue if needed
    if not hasattr(sys, '_lks_modules_to_clear'):
        sys._lks_modules_to_clear = set()

    # Find and queue action script modules for clearing
    # They're imported as "cExtensions.LKS.actions.<ScriptName>"
    for name in list(sys.modules.keys()):
        if "cExtensions.LKS.actions." in name:
            sys._lks_modules_to_clear.add(name)


# =============================================================================
# BASE CLASS (more features)
# =============================================================================

class Action:
    """
    Base class for action scripts with automatic hot-reload.

    Subclass and override execute() to implement your action.

    Attributes:
        room: Optional room name. If set, validates we're in that room.
        silent_reload: If True (default), suppress reload output.

    Example:
        class MyAction(Action):
            room = "Sculpt"

            def execute(self) -> None:
                from ops.SomeOperator import main as op_main
                op_main(...)

        MyAction().run()
    """

    room: str | None = None
    silent_reload: bool = True

    def execute(self) -> None:
        """Override this to implement the action logic."""
        raise NotImplementedError("Subclasses must implement execute()")

    def run(self) -> None:
        """Run the action with hot-reload and optional room validation."""
        # Hot reload all LKS modules
        from utils.hot_reload import reload_all
        reload_all(silent=self.silent_reload)

        # Validate room if specified
        if self.room is not None:
            self._validate_room()

        # Execute the action
        try:
            self.execute()
        finally:
            # Queue for cache clearing (same as @action decorator)
            _queue_module_for_clearing()

    def _validate_room(self) -> None:
        """Validate we're in the expected room."""
        try:
            import coat
            current_room: str = coat.ui.currentRoom()
            if current_room != self.room:
                coat.ui.showInfoMessage(
                    f"This action requires {self.room} room (current: {current_room})",
                    3000
                )
                raise RuntimeError(
                    f"Wrong room: expected {self.room}, got {current_room}")
        except ImportError:
            pass  # Running outside 3DCoat (testing)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_action(func: Callable[[], None]) -> None:
    """
    Run a function as an action with hot-reload.

    Convenience function for one-liners:
        run_action(lambda: op_main(scope=Scope.CURRENT))
    """
    from utils.hot_reload import reload_all
    reload_all()
    func()
