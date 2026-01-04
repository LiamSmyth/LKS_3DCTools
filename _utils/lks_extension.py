"""
LKS Extension - cExtension for IPC Communication.

This extension runs inside 3DCoat and provides the bridge between
the external panel app and 3DCoat's runtime.

It polls for commands and broadcasts scene state at regular intervals.
"""
from __future__ import annotations

import time
from typing import Optional, Type

import coat

from _utils.ipc_protocol import (
    cleanup_ipc,
    clear_shutdown,
    is_shutdown_requested,
    write_heartbeat,
)
from _utils.ipc_server import (
    broadcast_scene_state,
    process_pending_commands,
)


# =============================================================================
# RESOLVE cExtension BASE CLASS
# =============================================================================

# The cExtension class may be exposed differently depending on 3DCoat version.
# Try multiple paths to find it.

_cExtension_base: Optional[Type] = None

# Try 1: Direct attribute on coat module (as shown in coat.pyi)
if hasattr(coat, "cExtension"):
    _cExtension_base = coat.cExtension

# Try 2: Via cCore submodule (as shown in online docs)
if _cExtension_base is None:
    try:
        import cCore
        if hasattr(cCore, "cExtension"):
            _cExtension_base = cCore.cExtension
    except ImportError:
        pass

# Try 3: Via coat.cCore submodule
if _cExtension_base is None and hasattr(coat, "cCore"):
    cCore_module = getattr(coat, "cCore", None)
    if cCore_module and hasattr(cCore_module, "cExtension"):
        _cExtension_base = cCore_module.cExtension

# If we couldn't find cExtension, we cannot use per-frame hooks
# Fall back to a dummy base class
if _cExtension_base is None:
    # Log the issue
    try:
        coat.ui.showInfoMessage(
            "Warning: cExtension not found - using polling fallback", 5000)
    except Exception:
        pass

    class _DummyExtension:
        """Dummy base class when cExtension is not available."""

        def __init__(self) -> None:
            pass

    _cExtension_base = _DummyExtension

# Flag to know if we have real extension support
HAS_CEXTENSION: bool = _cExtension_base is not None and _cExtension_base.__name__ == "cExtension"


# =============================================================================
# EXTENSION CONFIGURATION
# =============================================================================

# How often to poll for commands (in frames)
POLL_INTERVAL_FRAMES: int = 5

# How often to broadcast scene state (in frames)
STATE_BROADCAST_INTERVAL_FRAMES: int = 10

# How often to write heartbeat (in frames)
HEARTBEAT_INTERVAL_FRAMES: int = 30


# =============================================================================
# EXTENSION SINGLETON
# =============================================================================

_extension_instance: Optional["LKSExtension"] = None


def get_extension() -> Optional["LKSExtension"]:
    """Get the current extension instance."""
    return _extension_instance


def is_extension_registered() -> bool:
    """Check if extension is currently registered."""
    return _extension_instance is not None


# =============================================================================
# EXTENSION CLASS
# =============================================================================

class LKSExtension(_cExtension_base):  # type: ignore[misc]
    """
    LKS IPC Extension.

    Runs per-frame hooks to:
    - Poll commands.json and execute commands
    - Broadcast scene state to external panel
    - Write heartbeat for liveness detection
    - Handle graceful shutdown
    """

    def __init__(self) -> None:
        """Initialize the extension."""
        global _extension_instance

        super().__init__()

        self._frame_counter: int = 0
        self._is_active: bool = True
        self._last_command_time: float = 0.0
        self._commands_processed: int = 0

        # Clean up any stale IPC files from previous session
        cleanup_ipc()
        clear_shutdown()

        # Store reference
        _extension_instance = self

        # Try to start the extension handler if available
        # This may be necessary to activate the per-frame hooks
        if hasattr(self, 'extensionHandler') and self.extensionHandler is not None:
            try:
                self.extensionHandler.Start()
                coat.ui.showInfoMessage("LKS Extension: Handler started", 2000)
            except Exception as e:
                coat.ui.showInfoMessage(
                    f"LKS Extension: Handler start failed: {e}", 3000)
        else:
            coat.ui.showInfoMessage(
                "LKS Extension: No handler (normal instantiation)", 2000)

    def preprocess(self) -> None:
        """
        Called every frame before tool processing.

        This is where we do our IPC work.
        """
        if not self._is_active:
            return

        self._frame_counter += 1

        # Check for shutdown request
        if self._frame_counter % POLL_INTERVAL_FRAMES == 0:
            if is_shutdown_requested():
                self._shutdown()
                return

        # Poll for commands
        if self._frame_counter % POLL_INTERVAL_FRAMES == 0:
            try:
                count: int = process_pending_commands()
                if count > 0:
                    self._commands_processed += count
                    self._last_command_time = time.time()
            except Exception as e:
                # Don't crash on IPC errors
                pass

        # Broadcast scene state
        if self._frame_counter % STATE_BROADCAST_INTERVAL_FRAMES == 0:
            try:
                broadcast_scene_state()
            except Exception:
                pass

        # Write heartbeat
        if self._frame_counter % HEARTBEAT_INTERVAL_FRAMES == 0:
            try:
                write_heartbeat()
            except Exception:
                pass

    def postprocess(self) -> None:
        """Called every frame after tool processing."""
        pass  # Not used

    def afterUI(self) -> None:
        """Called after UI rendering."""
        pass  # Not used

    def onNew(self) -> None:
        """Called when a new scene is created."""
        # Broadcast updated scene state
        try:
            broadcast_scene_state()
        except Exception:
            pass

    def onChangeTool(self) -> None:
        """Called when the active tool changes."""
        pass  # Could broadcast tool change if needed

    def onChangeRoom(self) -> None:
        """Called when the room changes."""
        # Broadcast updated scene state with new room
        try:
            broadcast_scene_state()
        except Exception:
            pass

    def onMessage(self, msg: str) -> None:
        """
        Called when a message is sent via cExtension.Message().

        This allows other scripts to communicate with the extension.
        """
        if msg == "shutdown":
            self._shutdown()
        elif msg == "broadcast":
            broadcast_scene_state()
        elif msg == "status":
            coat.ui.showInfoMessage(
                f"LKS Extension: Active, {self._commands_processed} commands processed",
                2000
            )

    def _shutdown(self) -> None:
        """Perform graceful shutdown."""
        global _extension_instance

        self._is_active = False
        cleanup_ipc()
        clear_shutdown()
        _extension_instance = None

        coat.ui.showInfoMessage("LKS Extension: Stopped", 2000)


# =============================================================================
# REGISTRATION HELPERS
# =============================================================================

# Extension name used for registration and messaging
EXTENSION_NAME: str = "LKSExtension"


def register_extension() -> LKSExtension:
    """
    Register the extension with 3DCoat's extension system.

    Uses coat.ui.addExtension() to properly register with the framework,
    which should enable the per-frame hooks (preprocess, etc).

    Returns the extension instance.
    """
    global _extension_instance

    if _extension_instance is not None:
        return _extension_instance

    if not HAS_CEXTENSION:
        coat.ui.showInfoMessage(
            "Warning: cExtension not available - limited functionality", 3000
        )
        return LKSExtension()

    # Check if already registered with 3DCoat
    already_registered: bool = False
    try:
        already_registered = coat.ui.checkIfExtensionPresent(EXTENSION_NAME)
    except Exception:
        pass

    # Create the extension instance
    ext: LKSExtension = LKSExtension()

    # Try to register with 3DCoat's extension system
    # Using empty room and section for a background extension
    if not already_registered:
        try:
            # Try registering as a background extension (empty room/section)
            coat.ui.addExtension("", "", ext)
            coat.ui.showInfoMessage(
                f"LKS Extension: Registered via addExtension", 2000)
        except Exception as e:
            # Registration failed, but the instance still exists
            coat.ui.showInfoMessage(
                f"LKS Extension: addExtension failed ({e}), using fallback", 3000)
    else:
        coat.ui.showInfoMessage(f"LKS Extension: Already registered", 2000)

    return ext


def unregister_extension() -> None:
    """Request extension shutdown."""
    if _extension_instance is not None:
        _extension_instance._shutdown()


def send_message(msg: str) -> None:
    """Send a message to the extension."""
    if HAS_CEXTENSION and hasattr(_cExtension_base, "Message"):
        _cExtension_base.Message("LKSExtension", msg)
    else:
        # Fallback: directly call the extension instance
        ext: Optional[LKSExtension] = get_extension()
        if ext is not None:
            ext.onMessage(msg)
