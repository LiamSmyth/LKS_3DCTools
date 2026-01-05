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
        LKSExtension._instance = self
        print("[LKS] Extension registered")

    def onStartup(self) -> None:
        """Called once after 3DCoat fully initializes. Auto-show the panel."""
        print("[LKS] onStartup - auto-launching panel")
        self.show_panel()

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
        pass

    def onNew(self) -> None:
        """Called when a new scene is created."""
        print("[LKS] New scene created")
        if self._panel:
            self._panel.refresh_tree()

    def onChangeRoom(self) -> None:
        """Called when the room changes."""
        if self._panel:
            self._panel.refresh_tree()

    def onExit(self) -> None:
        """Called when 3DCoat exits. Clean up panel and Qt resources."""
        print("[LKS] Extension shutting down")
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
        """Show the LKS panel."""
        try:
            if self._panel is None:
                print("[LKS] Creating panel...")
                from ui.ui_main import LKSMainPanel
                self._panel = LKSMainPanel()
                print("[LKS] Panel created successfully")

            # Ensure visibility
            self._panel.setVisible(True)
            self._panel.show()
            self._panel.raise_()
            self._panel.activateWindow()

            # Force repaint
            self._panel.update()

            # Debug: Print panel geometry
            geom = self._panel.geometry()
            print(
                f"[LKS] Panel geometry: x={geom.x()}, y={geom.y()}, w={geom.width()}, h={geom.height()}")
            print(f"[LKS] Panel visible: {self._panel.isVisible()}")
            print("[LKS] Panel shown")
        except Exception as e:
            import traceback
            print(f"[LKS] Error showing panel: {e}")
            traceback.print_exc()

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
print("[LKS] Registering extension...")
_ensure_extension()
print("[LKS] Calling show_panel()...")
show_panel()
print("[LKS] LKS.py execution complete")
