"""
LKS cModule - Main Extension and Panel

This is the main entry point for the LKS cModule. It provides:
1. A cExtension subclass with per-frame hooks for processing Qt events
2. A non-blocking Qt panel with dark theme for LKS tools
3. Dynamic scene tree display showing sculpt objects and their state
4. Activity log for operation feedback

The UI is modular:
- ui/ui_main.py            - Main panel (tabs, log, footer)
- ui/ui_tab_*.py           - Tab content factories
- ui/ui_collapsible_*.py   - Collapsible section factories

Usage:
    Run this script from 3DCoat's Scripts menu to show the LKS panel.
    The extension auto-registers on first import.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cPy.cCore
import coat

if TYPE_CHECKING:
    from ui.ui_main import LKSMainPanel


# =============================================================================
# LOGGING HELPER
# =============================================================================

def _log_ext(message: str) -> None:
    """Log an extension event to both the console and the invocation logger."""
    print(f"[LKS] {message}")
    try:
        from utils.invocation_logger import get_invocation_logger
        logger = get_invocation_logger()
        logger.log_info(f"[LKS] {message}")
    except ImportError:
        pass


# =============================================================================
# LKS EXTENSION (Per-Frame Hooks)
# =============================================================================


class LKSExtension(cPy.cCore.cExtension):
    """
    LKS Extension providing per-frame hooks.

    This extension processes Qt events every frame to keep the UI responsive
    while 3DCoat is running.
    """

    _instance: "LKSExtension | None" = None

    def __init__(self) -> None:
        cPy.cCore.cExtension.__init__(self)
        self._frame_count: int = 0
        self._panel: "LKSMainPanel | None" = None
        self._saved_geometry: tuple[int, int, int, int] | None = None
        LKSExtension._instance = self
        _log_ext("Extension registered")

    def onStartup(self) -> None:
        """Called once after 3DCoat fully initializes. Ensures deps before panel launch."""
        _log_ext("onStartup - initializing")
        self._ensure_dependencies()
        self.show_panel()

    def _ensure_dependencies(self) -> None:
        """Install lks_utils runtime dependencies using 3DCoat's pip API."""
        _deps: list[str] = ["ftfy"]
        for _dep in _deps:
            try:
                __import__(_dep)
            except ImportError:
                _log_ext(f"Installing dependency: {_dep}...")
                try:
                    coat.io.pipInstall(_dep)
                    _log_ext(f"  Installed {_dep} successfully")
                except Exception as e:
                    _log_ext(f"  WARNING: Failed to install {_dep}: {e}")

    def preprocess(self) -> None:
        """Called every frame before tools processing. Process Qt events here."""
        self._frame_count += 1

        # Process Qt events to keep UI responsive
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()
        except ImportError:
            pass  # Qt not available

        # Refresh outliner tree every N frames (throttled)
        if self._frame_count % 30 == 0 and self._panel:
            self._panel.refresh_tree()

    def postprocess(self) -> None:
        """Called every frame after tools processing."""
        # Clear any action script modules that were queued for removal
        # This allows action scripts to be re-executed on subsequent menu clicks
        import sys
        if hasattr(sys, '_lks_modules_to_clear') and sys._lks_modules_to_clear:
            from utils.fast_reimport import FastReimportFinder
            from utils.lks_settings import get_settings

            finder: FastReimportFinder = FastReimportFinder.get_instance()
            dev_mode: bool = get_settings().dev_mode

            for module_name in list(sys._lks_modules_to_clear):
                if module_name in sys.modules:
                    if not dev_mode:
                        # Cache compiled code for instant reimport next press
                        cached: bool = finder.cache_module(module_name)
                        label: str = "cached+cleared" if cached else "cleared"
                    else:
                        # Dev mode: uncache so code changes are picked up
                        finder.uncache_module(module_name)
                        label = "cleared (dev)"
                    del sys.modules[module_name]
                    _log_ext(f"{label}: {module_name}")
            sys._lks_modules_to_clear.clear()

    def onNew(self) -> None:
        """Called when a new scene is created."""
        _log_ext("New scene created")
        if self._panel:
            self._panel.refresh_tree()

    def onChangeRoom(self) -> None:
        """Called when the room changes."""
        if self._panel:
            self._panel.refresh_tree()

    def onExit(self) -> None:
        """Called when 3DCoat exits. Clean up panel and Qt resources."""
        _log_ext("Extension shutting down")
        if self._panel:
            self._panel.close()
            self._panel = None
        # Quit Qt app if we own it
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()
        except ImportError:
            pass

    def show_panel(self) -> None:
        """Show the LKS panel. Restores saved geometry from hot-reload if available."""
        try:
            if self._panel is None:
                _log_ext("Creating panel...")
                from ui.ui_main import LKSMainPanel
                self._panel = LKSMainPanel()

                # Restore saved geometry from hot-reload
                if self._saved_geometry:
                    x, y, w, h = self._saved_geometry
                    self._panel.setGeometry(x, y, w, h)
                    self._saved_geometry = None
                    _log_ext(f"Panel geometry restored: {x},{y} {w}x{h}")
                else:
                    _log_ext("Panel created successfully")
            else:
                _log_ext("Panel already exists, showing...")

            # Ensure visibility
            self._panel.setVisible(True)
            self._panel.show()
            self._panel.raise_()
            self._panel.activateWindow()

            # Force repaint
            self._panel.update()

            # Debug: Print panel geometry
            geom = self._panel.geometry()
            _log_ext(
                f"Panel geometry: x={geom.x()}, y={geom.y()}, w={geom.width()}, h={geom.height()}")
            _log_ext(f"Panel visible: {self._panel.isVisible()}")
            _log_ext("Panel shown")
        except Exception as e:
            import traceback
            _log_ext(f"Error showing panel: {e}")
            traceback.print_exc()

    def reinitialize(self) -> None:
        """
        Reset extension Python state for hot-reload.

        The C++ cExtension registration cannot be destroyed, but we can
        clear all Python-side state so the extension behaves as if freshly
        created. Saves the panel's window geometry so the new panel appears
        in the same position.
        """
        import gc

        # Save geometry before destroying the panel
        if self._panel:
            try:
                geom = self._panel.geometry()
                self._saved_geometry = (geom.x(), geom.y(), geom.width(), geom.height())
                self._panel.hide()
                self._panel.close()
                self._panel.deleteLater()
            except Exception:
                self._saved_geometry = None
            self._panel = None

        # Reset counters and state
        self._frame_count = 0

        # Force garbage collection to release any Qt references
        gc.collect()

        # Update the class-level singleton reference
        LKSExtension._instance = self

        _log_ext("Extension reinitialized (Python state reset)")

    @classmethod
    def get_instance(cls) -> "LKSExtension | None":
        """Get the singleton extension instance."""
        return cls._instance


# =============================================================================
# EXTENSION REGISTRATION & ENTRY POINT
# =============================================================================

_extension: LKSExtension | None = None


def _ensure_extension() -> LKSExtension:
    """Ensure the extension is registered."""
    global _extension
    if _extension is None:
        _extension = LKSExtension()
    return _extension


def show_panel() -> None:
    """Show the LKS panel. Entry point when script is run."""
    ext = _ensure_extension()
    ext.show_panel()


# Register extension and show panel when script is executed
_log_ext("Registering extension...")
_ensure_extension()
_log_ext("Calling show_panel()...")
show_panel()
_log_ext("LKS.py execution complete")
