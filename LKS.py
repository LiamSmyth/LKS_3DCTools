"""
LKS cModule - Main Extension

This is the main entry point for the LKS cModule. It provides:
1. A cExtension subclass with per-frame hooks for processing Qt events
2. A non-blocking Qt panel for LKS tools

Usage:
    Run this script from 3DCoat's Scripts menu to show the LKS panel.
    The extension auto-registers on first import.
"""
import cPy.cCore
import coat

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
        self._panel: "LKSPanel | None" = None
        LKSExtension._instance = self
        print("[LKS] Extension registered")

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

    def postprocess(self) -> None:
        """Called every frame after tools processing."""
        pass

    def onNew(self) -> None:
        """Called when a new scene is created."""
        print("[LKS] New scene created")

    def onChangeRoom(self) -> None:
        """Called when the room changes."""
        pass

    def onExit(self) -> None:
        """Called when 3DCoat exits."""
        print("[LKS] Extension shutting down")
        if self._panel:
            self._panel.close()

    def show_panel(self) -> None:
        """Show the LKS panel."""
        if self._panel is None:
            self._panel = LKSPanel()
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()

    @classmethod
    def get_instance(cls) -> "LKSExtension | None":
        """Get the singleton extension instance."""
        return cls._instance


# =============================================================================
# LKS PANEL (Qt-based Non-Blocking UI)
# =============================================================================

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGroupBox, QFrame
    )
    from PySide6.QtCore import Qt

    class LKSPanel(QWidget):
        """
        LKS Tools Panel - Non-blocking Qt panel for quick access to LKS tools.

        This is a stub implementation. Add your buttons and controls here.
        """

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("LKS Tools")
            self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
            self.setMinimumSize(250, 200)

            self._setup_ui()

        def _setup_ui(self) -> None:
            """Set up the panel UI."""
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(8)

            # Header
            header = QLabel("LKS Tools Panel")
            header.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(header)

            # Status label
            self._status_label = QLabel("Extension active")
            self._status_label.setStyleSheet("color: green;")
            layout.addWidget(self._status_label)

            # Separator
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            layout.addWidget(line)

            # Quick Actions group
            actions_group = QGroupBox("Quick Actions")
            actions_layout = QVBoxLayout()

            # Decimate buttons row
            dec_row = QHBoxLayout()
            btn_dec_50 = QPushButton("Dec 50%")
            btn_dec_50.setToolTip("Decimate selected object to 50%")
            btn_dec_50.clicked.connect(self._on_decimate_50)
            dec_row.addWidget(btn_dec_50)

            btn_dec_tree = QPushButton("Dec Tree")
            btn_dec_tree.setToolTip("Decimate subtree to 50%")
            btn_dec_tree.clicked.connect(self._on_decimate_tree)
            dec_row.addWidget(btn_dec_tree)
            actions_layout.addLayout(dec_row)

            # Ghost buttons row
            ghost_row = QHBoxLayout()
            btn_unghost = QPushButton("Unghost All")
            btn_unghost.setToolTip("Unghost all objects")
            btn_unghost.clicked.connect(self._on_unghost_all)
            ghost_row.addWidget(btn_unghost)

            btn_invert = QPushButton("Invert Ghost")
            btn_invert.setToolTip("Invert ghost state of all objects")
            btn_invert.clicked.connect(self._on_invert_ghost)
            ghost_row.addWidget(btn_invert)
            actions_layout.addLayout(ghost_row)

            actions_group.setLayout(actions_layout)
            layout.addWidget(actions_group)

            # Stretch to push content up
            layout.addStretch()

            # Footer with close button
            footer_row = QHBoxLayout()
            footer_row.addStretch()
            btn_close = QPushButton("Close")
            btn_close.clicked.connect(self.hide)
            footer_row.addWidget(btn_close)
            layout.addLayout(footer_row)

            self.setLayout(layout)

        def _on_decimate_50(self) -> None:
            """Decimate selected object to 50%."""
            try:
                from cModules.LKS._ops.SculptObject_Decimate import main as decimate
                from cModules.LKS._utils.scope_utils import Scope
                decimate(scope=Scope.CURRENT, reduction_percent=50.0)
                self._status_label.setText("Decimated selected to 50%")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")
                self._status_label.setStyleSheet("color: red;")

        def _on_decimate_tree(self) -> None:
            """Decimate subtree to 50%."""
            try:
                from cModules.LKS._ops.SculptObject_Decimate import main as decimate
                from cModules.LKS._utils.scope_utils import Scope
                decimate(scope=Scope.TREE, reduction_percent=50.0)
                self._status_label.setText("Decimated tree to 50%")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")
                self._status_label.setStyleSheet("color: red;")

        def _on_unghost_all(self) -> None:
            """Unghost all objects."""
            try:
                from cModules.LKS._ops.SculptObject_SetGhost import main as set_ghost
                from cModules.LKS._utils.scope_utils import Scope
                set_ghost(scope=Scope.ALL, ghost=False)
                self._status_label.setText("Unghosted all objects")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")
                self._status_label.setStyleSheet("color: red;")

        def _on_invert_ghost(self) -> None:
            """Invert ghost state of all objects."""
            try:
                from cModules.LKS._ops.SculptObject_SetGhost import main as set_ghost, GhostMode
                from cModules.LKS._utils.scope_utils import Scope
                set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT)
                self._status_label.setText("Inverted ghost states")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")
                self._status_label.setStyleSheet("color: red;")

    PANEL_AVAILABLE = True

except ImportError as e:
    print(f"[LKS] PySide6 not available, panel disabled: {e}")
    PANEL_AVAILABLE = False

    class LKSPanel:  # type: ignore
        """Stub panel when PySide6 is not available."""

        def __init__(self) -> None:
            print("[LKS] Panel not available - PySide6 required")

        def show(self) -> None:
            coat.ui.showInfoMessage("LKS Panel requires PySide6", 3000)


# =============================================================================
# EXTENSION REGISTRATION & ENTRY POINT
# =============================================================================

# Auto-register extension on import
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
_ensure_extension()
show_panel()
