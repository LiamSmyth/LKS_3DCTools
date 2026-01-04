"""
LKS cModule - Main Extension

This is the main entry point for the LKS cModule. It provides:
1. A cExtension subclass with per-frame hooks for processing Qt events
2. A non-blocking Qt panel with dark theme for LKS tools
3. Dynamic scene tree display showing sculpt objects and their state

Usage:
    Run this script from 3DCoat's Scripts menu to show the LKS panel.
    The extension auto-registers on first import.
"""
import cPy.cCore
import coat

# Import stylesheet from ui module
from ui.styles import DARK_STYLESHEET


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

    def postprocess(self) -> None:
        """Called every frame after tools processing."""
        pass

    def onNew(self) -> None:
        """Called when a new scene is created."""
        print("[LKS] New scene created")
        if self._panel:
            self._panel.refresh_scene_tree()

    def onChangeRoom(self) -> None:
        """Called when the room changes."""
        if self._panel:
            self._panel.refresh_scene_tree()

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
# LKS PANEL (Qt-based Non-Blocking UI with Dark Theme)
# =============================================================================

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGroupBox, QFrame, QTreeWidget, QTreeWidgetItem, QSplitter,
        QSizePolicy
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QBrush, QIcon

    class LKSPanel(QWidget):
        """
        LKS Tools Panel - Non-blocking Qt panel with dark theme.

        Features:
        - Dark theme styling
        - Dynamic scene tree with visibility/ghost state
        - Quick action buttons for common operations
        """

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("LKS Tools")
            self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
            self.setMinimumSize(320, 500)
            self.resize(350, 600)

            # Apply dark theme
            self.setStyleSheet(DARK_STYLESHEET)

            self._setup_ui()

            # Auto-refresh timer for scene tree (every 2 seconds)
            self._refresh_timer = QTimer(self)
            self._refresh_timer.timeout.connect(self.refresh_scene_tree)
            self._refresh_timer.start(2000)

        def closeEvent(self, event) -> None:
            """Handle panel close - stop timer and deactivate extension."""
            print("[LKS] Panel closed - deactivating extension")
            self._refresh_timer.stop()

            # Clean up extension reference
            ext = LKSExtension.get_instance()
            if ext:
                ext._panel = None
                # Note: Can't fully unregister extension, but clear panel ref

            event.accept()

        def _setup_ui(self) -> None:
            """Set up the panel UI."""
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(8, 8, 8, 8)
            main_layout.setSpacing(8)

            # Header
            header = QLabel("LKS Tools")
            header.setStyleSheet(
                "font-weight: bold; font-size: 16px; color: #90caf9;")
            main_layout.addWidget(header)

            # Status label
            self._status_label = QLabel("Extension active")
            self._status_label.setStyleSheet("color: #81c784;")
            main_layout.addWidget(self._status_label)

            # Separator
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            main_layout.addWidget(line)

            # Create splitter for resizable sections
            splitter = QSplitter(Qt.Vertical)

            # Scene Tree Group
            scene_group = QGroupBox("Scene Tree")
            scene_layout = QVBoxLayout()
            scene_layout.setContentsMargins(4, 4, 4, 4)

            self._scene_tree = QTreeWidget()
            self._scene_tree.setHeaderLabels(["Name", "Vis", "Ghost", "Polys"])
            self._scene_tree.setAlternatingRowColors(True)
            self._scene_tree.setRootIsDecorated(True)
            self._scene_tree.setColumnWidth(0, 150)
            self._scene_tree.setColumnWidth(1, 35)
            self._scene_tree.setColumnWidth(2, 40)
            self._scene_tree.setColumnWidth(3, 60)
            scene_layout.addWidget(self._scene_tree)

            # Scene tree actions
            tree_btns = QHBoxLayout()
            btn_refresh = QPushButton("↻ Refresh")
            btn_refresh.setToolTip("Refresh scene tree")
            btn_refresh.clicked.connect(self.refresh_scene_tree)
            tree_btns.addWidget(btn_refresh)

            btn_select = QPushButton("Select")
            btn_select.setToolTip("Select highlighted item in 3DCoat")
            btn_select.clicked.connect(self._on_select_item)
            tree_btns.addWidget(btn_select)
            tree_btns.addStretch()
            scene_layout.addLayout(tree_btns)

            scene_group.setLayout(scene_layout)
            splitter.addWidget(scene_group)

            # Quick Actions Group
            actions_group = QGroupBox("Quick Actions")
            actions_layout = QVBoxLayout()
            actions_layout.setSpacing(6)

            # Decimate buttons row
            dec_label = QLabel("Decimate:")
            dec_label.setStyleSheet("font-weight: bold; color: #ffb74d;")
            actions_layout.addWidget(dec_label)

            dec_row = QHBoxLayout()
            btn_dec_50 = QPushButton("50% Sel")
            btn_dec_50.setToolTip("Decimate selected object to 50%")
            btn_dec_50.clicked.connect(self._on_decimate_50)
            dec_row.addWidget(btn_dec_50)

            btn_dec_tree = QPushButton("50% Tree")
            btn_dec_tree.setToolTip("Decimate subtree to 50%")
            btn_dec_tree.clicked.connect(self._on_decimate_tree)
            dec_row.addWidget(btn_dec_tree)

            btn_dec_16x = QPushButton("16x")
            btn_dec_16x.setToolTip("Quick 16x decimate proxy")
            btn_dec_16x.clicked.connect(self._on_decimate_16x)
            dec_row.addWidget(btn_dec_16x)
            actions_layout.addLayout(dec_row)

            # Ghost buttons row
            ghost_label = QLabel("Visibility:")
            ghost_label.setStyleSheet("font-weight: bold; color: #ffb74d;")
            actions_layout.addWidget(ghost_label)

            ghost_row = QHBoxLayout()
            btn_unghost = QPushButton("Unghost All")
            btn_unghost.setToolTip("Unghost all objects")
            btn_unghost.clicked.connect(self._on_unghost_all)
            ghost_row.addWidget(btn_unghost)

            btn_invert = QPushButton("Invert")
            btn_invert.setToolTip("Invert ghost state of all objects")
            btn_invert.clicked.connect(self._on_invert_ghost)
            ghost_row.addWidget(btn_invert)

            btn_isolate = QPushButton("Isolate")
            btn_isolate.setToolTip("Ghost all except selected")
            btn_isolate.clicked.connect(self._on_isolate)
            ghost_row.addWidget(btn_isolate)
            actions_layout.addLayout(ghost_row)

            # Mode conversion row
            mode_label = QLabel("Mode:")
            mode_label.setStyleSheet("font-weight: bold; color: #ffb74d;")
            actions_layout.addWidget(mode_label)

            mode_row = QHBoxLayout()
            btn_to_surface = QPushButton("→ Surface")
            btn_to_surface.setToolTip("Convert all to surface mode")
            btn_to_surface.clicked.connect(self._on_to_surface)
            mode_row.addWidget(btn_to_surface)

            btn_to_voxels = QPushButton("→ Voxels")
            btn_to_voxels.setToolTip("Convert all to voxel mode")
            btn_to_voxels.clicked.connect(self._on_to_voxels)
            mode_row.addWidget(btn_to_voxels)
            actions_layout.addLayout(mode_row)

            actions_group.setLayout(actions_layout)
            splitter.addWidget(actions_group)

            # Set splitter sizes (scene tree gets more space)
            splitter.setSizes([350, 200])

            main_layout.addWidget(splitter, 1)  # Stretch factor

            # Footer with close button
            footer_row = QHBoxLayout()
            footer_row.addStretch()
            btn_close = QPushButton("Close")
            btn_close.clicked.connect(self.hide)
            footer_row.addWidget(btn_close)
            main_layout.addLayout(footer_row)

            self.setLayout(main_layout)

            # Initial tree population
            self.refresh_scene_tree()

        def refresh_scene_tree(self) -> None:
            """Refresh the scene tree with current sculpt objects."""
            self._scene_tree.clear()

            try:
                from utils.scene_api import SceneAPI

                root = SceneAPI.get_sculpt_root()
                if not root:
                    item = QTreeWidgetItem(
                        self._scene_tree, ["(No scene)", "", "", ""])
                    return

                # Build tree recursively
                self._add_element_to_tree(root, self._scene_tree)
                self._scene_tree.expandAll()

            except Exception as e:
                item = QTreeWidgetItem(
                    self._scene_tree, [f"Error: {e}", "", "", ""])
                self._status_label.setText(f"Error: {e}")
                self._status_label.setStyleSheet("color: #ef5350;")

        def _add_element_to_tree(
            self,
            element: "coat.SceneElement",
            parent: "QTreeWidget | QTreeWidgetItem"
        ) -> None:
            """Add a scene element and its children to the tree."""
            try:
                name: str = element.name() if hasattr(element, 'name') else "Unknown"
                is_visible: bool = element.visible() if hasattr(element, 'visible') else True
                is_ghosted: bool = element.ghosted() if hasattr(element, 'ghosted') else False

                # Get polycount if it's a sculpt object
                polys: str = ""
                if element.isSculptObject():
                    vol = element.Volume()
                    if vol:
                        try:
                            polys = f"{vol.polyCount():,}"
                        except:
                            polys = "?"

                # Create tree item
                vis_text = "✓" if is_visible else "✗"
                ghost_text = "👻" if is_ghosted else ""

                item = QTreeWidgetItem([name, vis_text, ghost_text, polys])

                # Color coding
                if is_ghosted:
                    item.setForeground(0, QBrush(QColor("#888888")))
                elif not is_visible:
                    item.setForeground(0, QBrush(QColor("#666666")))
                elif element.isSculptObject():
                    item.setForeground(0, QBrush(QColor("#90caf9")))

                # Store element reference
                item.setData(0, Qt.UserRole, element)

                if isinstance(parent, QTreeWidget):
                    parent.addTopLevelItem(item)
                else:
                    parent.addChild(item)

                # Add children using correct 3DCoat API: childCount() + child(index)
                if hasattr(element, 'childCount') and hasattr(element, 'child'):
                    child_count: int = element.childCount()
                    for i in range(child_count):
                        child = element.child(i)
                        if child:
                            self._add_element_to_tree(child, item)

            except Exception as e:
                print(f"[LKS] Error adding element: {e}")

        def _on_select_item(self) -> None:
            """Select the highlighted tree item in 3DCoat."""
            current = self._scene_tree.currentItem()
            if current:
                element = current.data(0, Qt.UserRole)
                if element and hasattr(element, 'selectOne'):
                    element.selectOne()
                    self._set_status("Selected: " + current.text(0))

        def _set_status(self, text: str, is_error: bool = False) -> None:
            """Update status label."""
            self._status_label.setText(text)
            if is_error:
                self._status_label.setStyleSheet("color: #ef5350;")
            else:
                self._status_label.setStyleSheet("color: #81c784;")

        def _on_decimate_50(self) -> None:
            """Decimate selected object to 50%."""
            try:
                from ops.SculptObject_Decimate import main as decimate
                from utils.scope_utils import Scope
                decimate(scope=Scope.CURRENT, reduction_percent=50.0)
                self._set_status("Decimated selected to 50%")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_decimate_tree(self) -> None:
            """Decimate subtree to 50%."""
            try:
                from ops.SculptObject_Decimate import main as decimate
                from utils.scope_utils import Scope
                decimate(scope=Scope.TREE, reduction_percent=50.0)
                self._set_status("Decimated tree to 50%")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_decimate_16x(self) -> None:
            """Quick 16x decimate proxy."""
            try:
                from ops.SculptObject_Decimate import main as decimate, DecimateConfig
                from utils.scope_utils import Scope
                config = DecimateConfig(use_16x=True)
                decimate(scope=Scope.CURRENT, config=config)
                self._set_status("Decimated 16x")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_unghost_all(self) -> None:
            """Unghost all objects."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost
                from utils.scope_utils import Scope
                set_ghost(scope=Scope.ALL, ghost=False)
                self._set_status("Unghosted all objects")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_invert_ghost(self) -> None:
            """Invert ghost state of all objects."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
                from utils.scope_utils import Scope
                set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT)
                self._set_status("Inverted ghost states")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_isolate(self) -> None:
            """Ghost all except selected."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
                from utils.scope_utils import Scope
                set_ghost(scope=Scope.CURRENT, mode=GhostMode.ISOLATE)
                self._set_status("Isolated selected")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_to_surface(self) -> None:
            """Convert all to surface mode."""
            try:
                from ops.SculptObject_ModeConvert import main as convert
                from utils.scope_utils import Scope
                convert(scope=Scope.ALL, to_surface=True)
                self._set_status("Converted all to surface")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def _on_to_voxels(self) -> None:
            """Convert all to voxel mode."""
            try:
                from ops.SculptObject_ModeConvert import main as convert
                from utils.scope_utils import Scope
                convert(scope=Scope.ALL, to_surface=False)
                self._set_status("Converted all to voxels")
                self.refresh_scene_tree()
            except Exception as e:
                self._set_status(f"Error: {e}", is_error=True)

        def closeEvent(self, event) -> None:
            """Handle panel close - stop timer."""
            self._refresh_timer.stop()
            super().closeEvent(event)

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

        def refresh_scene_tree(self) -> None:
            pass


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
