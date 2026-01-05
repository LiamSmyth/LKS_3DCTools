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
        # Hot reload all LKS modules
        from utils.hot_reload import reload_all
        reload_all()

        # Execute the action
        return func(*args, **kwargs)

    return wrapper  # type: ignore


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
        self.execute()

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
