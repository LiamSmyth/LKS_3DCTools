"""
LKS cModule - Main Extension and Panel

This is the main entry point for the LKS cModule. It provides:
1. A cExtension subclass with per-frame hooks for processing Qt events
2. A non-blocking Qt panel with dark theme for LKS tools
3. Dynamic scene tree display showing sculpt objects and their state
4. Activity log for operation feedback

Button Labeling Convention:
- Use section headers to indicate the action category
- Use sub-headers for variants (e.g., "Reduction %")
- Button text shows only the differentiator (scope or value)
- Example: Header "Decimate", sub-header "Reduction %", buttons "25", "50", "80"
- Scope buttons: "Cur", "Tree", "All", "Other"

Usage:
    Run this script from 3DCoat's Scripts menu to show the LKS panel.
    The extension auto-registers on first import.
"""
from __future__ import annotations

import cPy.cCore
import coat

# Import stylesheet and widgets from ui module
from ui.styles import DARK_STYLESHEET
from ui.widgets import ActivityLog, SectionHeader, CollapsibleSection, ButtonGrid


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
        QSizePolicy, QScrollArea, QSlider
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QBrush

    class LKSPanel(QWidget):
        """
        LKS Tools Panel - Non-blocking Qt panel with dark theme.

        Features:
        - Dark theme styling
        - Dynamic scene tree with visibility/ghost state
        - Quick action buttons for common operations
        - Collapsible sections for organization
        - Activity log for feedback
        """

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("LKS Tools")
            self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
            self.setMinimumSize(340, 600)
            self.resize(360, 800)

            # Apply dark theme
            self.setStyleSheet(DARK_STYLESHEET)

            self._setup_ui()

            # Auto-refresh timer for scene tree (every 2 seconds)
            self._refresh_timer = QTimer(self)
            self._refresh_timer.timeout.connect(self.refresh_scene_tree)
            self._refresh_timer.start(2000)

        def closeEvent(self, event) -> None:
            """Handle panel close - stop timer."""
            print("[LKS] Panel closed")
            self._refresh_timer.stop()

            # Clean up extension reference
            ext = LKSExtension.get_instance()
            if ext:
                ext._panel = None

            event.accept()

        def _setup_ui(self) -> None:
            """Set up the panel UI."""
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(6, 6, 6, 6)
            main_layout.setSpacing(4)

            # Header
            header = QLabel("LKS Tools")
            header.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #90caf9; padding: 2px;")
            main_layout.addWidget(header)

            # Status label
            self._status_label = QLabel("Extension active")
            self._status_label.setStyleSheet(
                "color: #81c784; font-size: 10px;")
            main_layout.addWidget(self._status_label)

            # Separator
            main_layout.addWidget(self._create_separator())

            # Create scroll area for main content
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(0, 0, 4, 0)
            scroll_layout.setSpacing(4)

            # ========== SCENE TREE SECTION ==========
            scene_section = CollapsibleSection(
                title="Scene Tree", color="#90caf9")
            self._setup_scene_tree(scene_section.content_layout)
            scroll_layout.addWidget(scene_section)

            # ========== DECIMATE SECTION ==========
            dec_section = CollapsibleSection(title="Decimate", color="#ffb74d")
            self._setup_decimate_section(dec_section.content_layout)
            scroll_layout.addWidget(dec_section)

            # ========== RESAMPLE SECTION ==========
            resample_section = CollapsibleSection(
                title="Resample", color="#ffb74d")
            self._setup_resample_section(resample_section.content_layout)
            scroll_layout.addWidget(resample_section)

            # ========== MODE SECTION ==========
            mode_section = CollapsibleSection(
                title="Mode Conversion", color="#ffb74d")
            self._setup_mode_section(mode_section.content_layout)
            scroll_layout.addWidget(mode_section)

            # ========== SCALE SECTION ==========
            scale_section = CollapsibleSection(title="Scale", color="#ffb74d")
            self._setup_scale_section(scale_section.content_layout)
            scroll_layout.addWidget(scale_section)

            # ========== VISIBILITY SECTION ==========
            vis_section = CollapsibleSection(
                title="Visibility", color="#ffb74d")
            self._setup_visibility_section(vis_section.content_layout)
            scroll_layout.addWidget(vis_section)

            # ========== GHOST SECTION ==========
            ghost_section = CollapsibleSection(title="Ghost", color="#ffb74d")
            self._setup_ghost_section(ghost_section.content_layout)
            scroll_layout.addWidget(ghost_section)

            # ========== SMART ACTIONS SECTION ==========
            smart_section = CollapsibleSection(
                title="Smart Actions", color="#ce93d8", collapsed=True)
            self._setup_smart_section(smart_section.content_layout)
            scroll_layout.addWidget(smart_section)

            # ========== AUTOPO SECTION ==========
            autopo_section = CollapsibleSection(
                title="Autopo", color="#ce93d8", collapsed=True)
            self._setup_autopo_section(autopo_section.content_layout)
            scroll_layout.addWidget(autopo_section)

            # ========== DYNAMIC SUBDIV SECTION ==========
            subdiv_section = CollapsibleSection(
                title="Dynamic Subdiv", color="#ce93d8", collapsed=True)
            self._setup_subdiv_section(subdiv_section.content_layout)
            scroll_layout.addWidget(subdiv_section)

            # ========== LAYERS SECTION ==========
            layers_section = CollapsibleSection(
                title="Layers", color="#80cbc4", collapsed=True)
            self._setup_layers_section(layers_section.content_layout)
            scroll_layout.addWidget(layers_section)

            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            main_layout.addWidget(scroll, 1)  # Stretch

            # ========== ACTIVITY LOG ==========
            main_layout.addWidget(self._create_separator())
            log_header = SectionHeader(text="Activity Log", color="#90caf9")
            main_layout.addWidget(log_header)
            self._activity_log = ActivityLog()
            main_layout.addWidget(self._activity_log)
            self._activity_log.log_info("LKS panel initialized")

            # ========== FOOTER ==========
            footer = QHBoxLayout()
            btn_reload = QPushButton("↻ Reload")
            btn_reload.setToolTip("Reload all LKS modules (dev)")
            btn_reload.clicked.connect(self._on_dev_reload)
            footer.addWidget(btn_reload)
            footer.addStretch()
            btn_close = QPushButton("Close")
            btn_close.clicked.connect(self.hide)
            footer.addWidget(btn_close)
            main_layout.addLayout(footer)

            self.setLayout(main_layout)

            # Initial tree population
            self.refresh_scene_tree()

        def _create_separator(self) -> QFrame:
            """Create a horizontal separator line."""
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("QFrame { color: #444; }")
            return line

        def _create_sub_header(self, text: str) -> QLabel:
            """Create a sub-section header label."""
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #888; font-size: 9px; font-weight: bold;")
            return lbl

        # =====================================================================
        # SCENE TREE SECTION
        # =====================================================================

        def _setup_scene_tree(self, layout: QVBoxLayout) -> None:
            """Set up the scene tree section."""
            self._scene_tree = QTreeWidget()
            self._scene_tree.setHeaderLabels(["Name", "V", "G", "Polys"])
            self._scene_tree.setAlternatingRowColors(True)
            self._scene_tree.setRootIsDecorated(True)
            self._scene_tree.setColumnWidth(0, 140)
            self._scene_tree.setColumnWidth(1, 25)
            self._scene_tree.setColumnWidth(2, 25)
            self._scene_tree.setColumnWidth(3, 55)
            self._scene_tree.setMaximumHeight(180)
            layout.addWidget(self._scene_tree)

            # Buttons
            grid = ButtonGrid(columns=3)
            grid.add_button("↻ Refresh", self.refresh_scene_tree,
                            "Refresh scene tree")
            grid.add_button("Select", self._on_select_item,
                            "Select item in 3DCoat")
            layout.addWidget(grid)

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

                self._add_element_to_tree(root, self._scene_tree)
                self._scene_tree.expandAll()

            except Exception as e:
                item = QTreeWidgetItem(
                    self._scene_tree, [f"Error: {e}", "", "", ""])

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

                item.setData(0, Qt.UserRole, element)

                if isinstance(parent, QTreeWidget):
                    parent.addTopLevelItem(item)
                else:
                    parent.addChild(item)

                # Add children
                if hasattr(element, 'childCount') and hasattr(element, 'child'):
                    for i in range(element.childCount()):
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
                    self._log_success(f"Selected: {current.text(0)}")

        # =====================================================================
        # DECIMATE SECTION
        # =====================================================================

        def _setup_decimate_section(self, layout: QVBoxLayout) -> None:
            """Set up the decimate section."""
            # Reduction % sub-header with preset buttons
            layout.addWidget(self._create_sub_header("Quick Presets"))
            presets = ButtonGrid(columns=4)
            presets.add_button(
                "25%", lambda: self._decimate(25), "Decimate to 25%")
            presets.add_button(
                "50%", lambda: self._decimate(50), "Decimate to 50%")
            presets.add_button(
                "75%", lambda: self._decimate(75), "Decimate to 75%")
            presets.add_button(
                "Proxy", self._on_proxy_toggle, "Toggle proxy mode")
            layout.addWidget(presets)

            # Scope sub-header
            layout.addWidget(self._create_sub_header("Scope (50%)"))
            scope = ButtonGrid(columns=3)
            scope.add_button("Cur", lambda: self._decimate_scope(
                "CURRENT"), "Decimate selected")
            scope.add_button("Tree", lambda: self._decimate_scope(
                "TREE"), "Decimate subtree")
            scope.add_button(
                "All", lambda: self._decimate_scope("ALL"), "Decimate all")
            layout.addWidget(scope)

        def _decimate(self, percent: int) -> None:
            """Decimate current selection to percent."""
            try:
                from ops.SculptObject_Decimate import main as decimate
                from utils.scope_utils import Scope
                decimate(scope=Scope.CURRENT, reduction_percent=float(percent))
                self._log_success(f"Decimated to {percent}%")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Decimate failed: {e}")

        def _decimate_scope(self, scope_name: str) -> None:
            """Decimate with scope."""
            try:
                from ops.SculptObject_Decimate import main as decimate
                from utils.scope_utils import Scope
                scope = getattr(Scope, scope_name)
                decimate(scope=scope, reduction_percent=50.0)
                self._log_success(f"Decimated {scope_name.lower()} to 50%")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Decimate failed: {e}")

        def _on_proxy_toggle(self) -> None:
            """Toggle proxy mode."""
            try:
                from ops.SculptObject_Proxy import main as proxy
                from utils.scope_utils import Scope
                from utils.Volume_proxy_utils import ProxyType
                proxy(scope=Scope.CURRENT, proxy_type=ProxyType.DECIMATE_16X)
                self._log_success("Toggled proxy")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Proxy toggle failed: {e}")

        # =====================================================================
        # RESAMPLE SECTION
        # =====================================================================

        def _setup_resample_section(self, layout: QVBoxLayout) -> None:
            """Set up the resample section."""
            layout.addWidget(self._create_sub_header("Half (0.5x)"))
            half = ButtonGrid(columns=3)
            half.add_button("Cur", lambda: self._resample_scope(
                "CURRENT", 0.5), "Resample to half")
            half.add_button("Tree", lambda: self._resample_scope(
                "TREE", 0.5), "Resample subtree")
            half.add_button("All", lambda: self._resample_scope(
                "ALL", 0.5), "Resample all")
            layout.addWidget(half)

            layout.addWidget(self._create_sub_header(
                "Double (2x) / Subdivide"))
            double = ButtonGrid(columns=2)
            double.add_button("Double", lambda: self._resample_scope(
                "CURRENT", 2.0), "Resample to 2x")
            double.add_button(
                "Subdivide", self._on_subdivide, "Subdivide mesh")
            layout.addWidget(double)

        def _resample_scope(self, scope_name: str, scale: float) -> None:
            """Resample with scope and scale."""
            try:
                from ops.SculptObject_Resample import main as resample
                from utils.scope_utils import Scope
                scope = getattr(Scope, scope_name)
                resample(scope=scope, scale=scale)
                self._log_success(
                    f"Resampled {scope_name.lower()} to {scale}x")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Resample failed: {e}")

        def _on_subdivide(self) -> None:
            """Subdivide current object."""
            try:
                from utils.Volume_subdivide_utils import subdivide_once
                subdivide_once()
                self._log_success("Subdivided")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Subdivide failed: {e}")

        # =====================================================================
        # MODE SECTION
        # =====================================================================

        def _setup_mode_section(self, layout: QVBoxLayout) -> None:
            """Set up the mode conversion section."""
            layout.addWidget(self._create_sub_header("To Surface"))
            surface = ButtonGrid(columns=3)
            surface.add_button("Cur", lambda: self._convert_mode(
                "CURRENT", True), "Convert to surface")
            surface.add_button("Tree", lambda: self._convert_mode(
                "TREE", True), "Convert subtree")
            surface.add_button("All", lambda: self._convert_mode(
                "ALL", True), "Convert all")
            layout.addWidget(surface)

            layout.addWidget(self._create_sub_header("To Voxels"))
            voxels = ButtonGrid(columns=3)
            voxels.add_button("Cur", lambda: self._convert_mode(
                "CURRENT", False), "Convert to voxels")
            voxels.add_button("Tree", lambda: self._convert_mode(
                "TREE", False), "Convert subtree")
            voxels.add_button("All", lambda: self._convert_mode(
                "ALL", False), "Convert all")
            layout.addWidget(voxels)

        def _convert_mode(self, scope_name: str, to_surface: bool) -> None:
            """Convert mode with scope."""
            try:
                from ops.SculptObject_ModeConvert import main as convert
                from utils.scope_utils import Scope
                scope = getattr(Scope, scope_name)
                convert(scope=scope, to_surface=to_surface)
                mode_str = "surface" if to_surface else "voxels"
                self._log_success(
                    f"Converted {scope_name.lower()} to {mode_str}")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Mode convert failed: {e}")

        # =====================================================================
        # SCALE SECTION
        # =====================================================================

        def _setup_scale_section(self, layout: QVBoxLayout) -> None:
            """Set up the scale section."""
            layout.addWidget(self._create_sub_header("Scale Down (÷100)"))
            down = ButtonGrid(columns=3)
            down.add_button("Cur", lambda: self._scale(
                "CURRENT", 0.01), "Scale down 100x")
            down.add_button("Tree", lambda: self._scale(
                "TREE", 0.01), "Scale subtree")
            down.add_button("All", lambda: self._scale(
                "ALL", 0.01), "Scale all")
            layout.addWidget(down)

            layout.addWidget(self._create_sub_header("Scale Up (×100)"))
            up = ButtonGrid(columns=3)
            up.add_button("Cur", lambda: self._scale(
                "CURRENT", 100.0), "Scale up 100x")
            up.add_button("Tree", lambda: self._scale(
                "TREE", 100.0), "Scale subtree")
            up.add_button("All", lambda: self._scale(
                "ALL", 100.0), "Scale all")
            layout.addWidget(up)

        def _scale(self, scope_name: str, factor: float) -> None:
            """Scale with scope."""
            try:
                from ops.SculptObject_Scale import main as scale
                from utils.scope_utils import Scope
                scope = getattr(Scope, scope_name)
                scale(scope=scope, scale_factor=factor)
                self._log_success(f"Scaled {scope_name.lower()}")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Scale failed: {e}")

        # =====================================================================
        # VISIBILITY SECTION
        # =====================================================================

        def _setup_visibility_section(self, layout: QVBoxLayout) -> None:
            """Set up the visibility section."""
            layout.addWidget(self._create_sub_header("Hide"))
            hide = ButtonGrid(columns=4)
            hide.add_button("Cur", lambda: self._visibility(
                "CURRENT", False), "Hide selected")
            hide.add_button("Tree", lambda: self._visibility(
                "TREE", False), "Hide subtree")
            hide.add_button("Other", lambda: self._visibility(
                "OTHER", False), "Hide others")
            hide.add_button("All", lambda: self._visibility(
                "ALL", False), "Hide all")
            layout.addWidget(hide)

            layout.addWidget(self._create_sub_header("Show"))
            show = ButtonGrid(columns=4)
            show.add_button("Cur", lambda: self._visibility(
                "CURRENT", True), "Show selected")
            show.add_button("Tree", lambda: self._visibility(
                "TREE", True), "Show subtree")
            show.add_button("Other", lambda: self._visibility(
                "OTHER", True), "Show others")
            show.add_button("All", lambda: self._visibility(
                "ALL", True), "Show all")
            layout.addWidget(show)

            invert = ButtonGrid(columns=1)
            invert.add_button("Invert Visibility",
                              self._invert_visibility, "Invert all visibility")
            layout.addWidget(invert)

        def _visibility(self, scope_name: str, visible: bool) -> None:
            """Set visibility with scope."""
            try:
                from utils.scene_api import SceneAPI
                from utils.SceneElement_visibility_utils import set_visibility
                from utils.scope_utils import Scope, resolve_scope

                scope = getattr(Scope, scope_name)
                elements = resolve_scope(scope)
                count = set_visibility(elements, visible)
                action = "Shown" if visible else "Hidden"
                self._log_success(f"{action} {count} objects")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Visibility failed: {e}")

        def _invert_visibility(self) -> None:
            """Invert visibility on all."""
            try:
                from utils.scene_api import SceneAPI
                from utils.SceneElement_visibility_utils import invert_visibility_on_elements
                elements = SceneAPI.collect_all_sculpt_objects()
                count = invert_visibility_on_elements(elements)
                self._log_success(f"Inverted {count}")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Invert failed: {e}")

        # =====================================================================
        # GHOST SECTION
        # =====================================================================

        def _setup_ghost_section(self, layout: QVBoxLayout) -> None:
            """Set up the ghost section."""
            layout.addWidget(self._create_sub_header("Ghost"))
            ghost = ButtonGrid(columns=4)
            ghost.add_button("Cur", lambda: self._ghost(
                "CURRENT", True), "Ghost selected")
            ghost.add_button("Tree", lambda: self._ghost(
                "TREE", True), "Ghost subtree")
            ghost.add_button("Other", lambda: self._ghost(
                "OTHER", True), "Ghost others")
            ghost.add_button("All", lambda: self._ghost(
                "ALL", True), "Ghost all")
            layout.addWidget(ghost)

            layout.addWidget(self._create_sub_header("Unghost"))
            unghost = ButtonGrid(columns=4)
            unghost.add_button("Cur", lambda: self._ghost(
                "CURRENT", False), "Unghost selected")
            unghost.add_button("Tree", lambda: self._ghost(
                "TREE", False), "Unghost subtree")
            unghost.add_button("Other", lambda: self._ghost(
                "OTHER", False), "Unghost others")
            unghost.add_button("All", lambda: self._ghost(
                "ALL", False), "Unghost all")
            layout.addWidget(unghost)

            special = ButtonGrid(columns=2)
            special.add_button(
                "Invert Ghost", self._invert_ghost, "Invert ghost states")
            special.add_button("Isolate", self._isolate,
                               "Ghost all except selected")
            layout.addWidget(special)

        def _ghost(self, scope_name: str, ghosted: bool) -> None:
            """Set ghost with scope."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost
                from utils.scope_utils import Scope
                scope = getattr(Scope, scope_name)
                set_ghost(scope=scope, ghost=ghosted)
                action = "Ghosted" if ghosted else "Unghosted"
                self._log_success(f"{action} {scope_name.lower()}")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Ghost failed: {e}")

        def _invert_ghost(self) -> None:
            """Invert ghost on all."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
                from utils.scope_utils import Scope
                set_ghost(scope=Scope.ALL, mode=GhostMode.INVERT)
                self._log_success("Inverted ghost states")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Invert ghost failed: {e}")

        def _isolate(self) -> None:
            """Ghost all except selected."""
            try:
                from ops.SculptObject_SetGhost import main as set_ghost, GhostMode
                from utils.scope_utils import Scope
                set_ghost(scope=Scope.CURRENT, mode=GhostMode.ISOLATE)
                self._log_success("Isolated selected")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Isolate failed: {e}")

        # =====================================================================
        # SMART ACTIONS SECTION
        # =====================================================================

        def _setup_smart_section(self, layout: QVBoxLayout) -> None:
            """Set up the smart actions section."""
            layout.addWidget(self._create_sub_header("Uniform Density"))
            uniform = ButtonGrid(columns=2)
            uniform.add_button(
                "Resample Tree", self._uniform_resample_tree, "Match density via resample")
            uniform.add_button(
                "Smart Tree", self._uniform_smart_tree, "Smart density match")
            layout.addWidget(uniform)

            layout.addWidget(self._create_sub_header("Other"))
            other = ButtonGrid(columns=2)
            other.add_button("ID Colors", self._id_colors,
                             "Fill with ID colors")
            other.add_button("Split Masked", self._split_masked,
                             "Split frozen/masked")
            other.add_button("Remesh+Symm", self._remesh_resymm,
                             "Remesh and symmetrize")
            other.add_button("Merge Parts", self._merge_preserve,
                             "Merge preserving parts")
            layout.addWidget(other)

        def _uniform_resample_tree(self) -> None:
            """Uniform resample subtree."""
            try:
                from utils.scene_api import SceneAPI
                from utils.Volume_density_utils import resample_to_match_density
                current = SceneAPI.get_current_element()
                if not current:
                    self._log_error("No selection")
                    return
                subtree = SceneAPI.collect_subtree(current)
                ref_vol = current.Volume()
                count = 0
                for el in subtree:
                    if el != current and el.isSculptObject():
                        resample_to_match_density(el, ref_vol)
                        count += 1
                self._log_success(f"Resampled {count} to match density")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Uniform resample failed: {e}")

        def _uniform_smart_tree(self) -> None:
            """Smart uniform density on subtree."""
            try:
                from utils.scene_api import SceneAPI
                from utils.Volume_density_utils import smart_match_density
                current = SceneAPI.get_current_element()
                if not current:
                    self._log_error("No selection")
                    return
                subtree = SceneAPI.collect_subtree(current)
                ref_vol = current.Volume()
                count = 0
                for el in subtree:
                    if el != current and el.isSculptObject():
                        smart_match_density(el, ref_vol)
                        count += 1
                self._log_success(f"Smart matched {count}")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Smart density failed: {e}")

        def _id_colors(self) -> None:
            """Fill subtree with ID colors."""
            try:
                from ops.SculptObject_IdColors import main as id_colors
                from utils.scope_utils import Scope
                id_colors(scope=Scope.TREE)
                self._log_success("Applied ID colors")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"ID colors failed: {e}")

        def _split_masked(self) -> None:
            """Split masked/frozen area."""
            try:
                coat.ui.cmd("$SplitByMask")
                self._log_success("Split masked")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Split failed: {e}")

        def _remesh_resymm(self) -> None:
            """Remesh and symmetrize."""
            try:
                from utils.Volume_resample_utils import execute_resample
                from utils.Volume_subdivide_utils import make_symmetrical
                from utils.scene_api import SceneAPI
                current = SceneAPI.get_current_element()
                if current and current.isSculptObject():
                    vol = current.Volume()
                    target = int(vol.polyCount() * 0.5)
                    execute_resample(target_polycount=target, scale=0.5)
                    make_symmetrical()
                    self._log_success("Remeshed + symmetrized")
                    self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Remesh+symm failed: {e}")

        def _merge_preserve(self) -> None:
            """Merge preserving parts."""
            try:
                coat.ui.cmd("$MergeVisibleAsLayer")
                self._log_success("Merged preserving parts")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Merge failed: {e}")

        # =====================================================================
        # AUTOPO SECTION
        # =====================================================================

        def _setup_autopo_section(self, layout: QVBoxLayout) -> None:
            """Set up the autopo section."""
            layout.addWidget(self._create_sub_header("Run Autopo"))
            run = ButtonGrid(columns=3)
            run.add_button("Run", self._autopo_run, "Run autopo with settings")
            run.add_button("→ Sculpt", self._autopo_to_sculpt,
                           "Autopo then import to sculpt")
            run.add_button("→ Multires", self._autopo_to_multires,
                           "Autopo then import as multires")
            layout.addWidget(run)

        def _autopo_run(self) -> None:
            """Run autopo."""
            try:
                from utils.autopo_utils import execute_autopo, AutopoParams
                from utils.lks_settings import get_autopo_settings
                settings = get_autopo_settings()
                params = AutopoParams(
                    target_polycount=settings.autopo_polycount,
                    capture_details=settings.autopo_capture_details,
                    auto_density=settings.autopo_auto_density,
                    hardsurface=settings.autopo_hardsurface,
                )
                execute_autopo(params)
                self._log_success("Autopo complete")
            except Exception as e:
                self._log_error(f"Autopo failed: {e}")

        def _autopo_to_sculpt(self) -> None:
            """Autopo then import to sculpt."""
            try:
                from utils.autopo_utils import autopo_to_sculpt
                autopo_to_sculpt()
                self._log_success("Autopo → Sculpt complete")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Autopo to sculpt failed: {e}")

        def _autopo_to_multires(self) -> None:
            """Autopo then import as multires."""
            try:
                from utils.autopo_utils import autopo_to_multiresolution
                autopo_to_multiresolution()
                self._log_success("Autopo → Multires complete")
                self.refresh_scene_tree()
            except Exception as e:
                self._log_error(f"Autopo to multires failed: {e}")

        # =====================================================================
        # DYNAMIC SUBDIV SECTION
        # =====================================================================

        def _setup_subdiv_section(self, layout: QVBoxLayout) -> None:
            """Set up the dynamic subdivision section."""
            layout.addWidget(self._create_sub_header("Details Level"))
            level = ButtonGrid(columns=3)
            level.add_button("−", self._decrement_level, "Decrement level")
            level.add_button("+", self._increment_level, "Increment level")
            level.add_button(
                "Apply All", self._apply_brush_settings, "Apply to all brushes")
            layout.addWidget(level)

        def _increment_level(self) -> None:
            """Increment details level."""
            try:
                from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
                from utils.lks_settings import get_brush_settings, save_brush_settings
                settings = get_brush_settings()
                new_level = min(8.0, settings.details_level + 1.0)
                settings.details_level = int(new_level)
                settings.auto_subdivide = True
                save_brush_settings()
                apply_auto_subdivide_all(True)
                apply_details_level_all(new_level)
                self._log_success(f"Details level: {new_level}")
            except Exception as e:
                self._log_error(f"Increment failed: {e}")

        def _decrement_level(self) -> None:
            """Decrement details level."""
            try:
                from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all
                from utils.lks_settings import get_brush_settings, save_brush_settings
                settings = get_brush_settings()
                new_level = max(0.0, settings.details_level - 1.0)
                settings.details_level = int(new_level)
                settings.auto_subdivide = True
                save_brush_settings()
                apply_auto_subdivide_all(True)
                apply_details_level_all(new_level)
                self._log_success(f"Details level: {new_level}")
            except Exception as e:
                self._log_error(f"Decrement failed: {e}")

        def _apply_brush_settings(self) -> None:
            """Apply brush settings to all brushes."""
            try:
                from utils.brush_settings_utils import apply_auto_subdivide_all, apply_details_level_all, apply_remove_stretching_all
                from utils.lks_settings import get_brush_settings
                settings = get_brush_settings()
                apply_auto_subdivide_all(settings.auto_subdivide)
                apply_details_level_all(float(settings.details_level))
                apply_remove_stretching_all(settings.remove_stretching)
                self._log_success("Applied to all brushes")
            except Exception as e:
                self._log_error(f"Apply failed: {e}")

        # =====================================================================
        # LAYERS SECTION
        # =====================================================================

        def _setup_layers_section(self, layout: QVBoxLayout) -> None:
            """Set up the layers section."""
            layers = ButtonGrid(columns=2)
            layers.add_button("Setup Layers", self._setup_layers,
                              "Create Sculpt/Color layers")
            layers.add_button(
                "Clean Layers", self._clean_layers, "Remove empty layers")
            layout.addWidget(layers)

        def _setup_layers(self) -> None:
            """Setup standard layers."""
            try:
                from utils.Scene_layer_utils import ensure_standard_layers
                ensure_standard_layers()
                self._log_success("Layers setup complete")
            except Exception as e:
                self._log_error(f"Layer setup failed: {e}")

        def _clean_layers(self) -> None:
            """Clean up empty layers."""
            try:
                from utils.Scene_cleanup_utils import cleanup_after_mesh_operation
                cleanup_after_mesh_operation()
                self._log_success("Cleaned empty layers")
            except Exception as e:
                self._log_error(f"Layer cleanup failed: {e}")

        # =====================================================================
        # LOGGING & STATUS HELPERS
        # =====================================================================

        def _set_status(self, text: str, is_error: bool = False) -> None:
            """Update status label and log."""
            self._status_label.setText(text)
            if is_error:
                self._status_label.setStyleSheet(
                    "color: #ef5350; font-size: 10px;")
                self._activity_log.log_error(text)
            else:
                self._status_label.setStyleSheet(
                    "color: #81c784; font-size: 10px;")
                self._activity_log.log_success(text)

        def _log_success(self, text: str) -> None:
            """Log success message."""
            self._status_label.setText(text)
            self._status_label.setStyleSheet(
                "color: #81c784; font-size: 10px;")
            self._activity_log.log_success(text)

        def _log_error(self, text: str) -> None:
            """Log error message."""
            self._status_label.setText(text)
            self._status_label.setStyleSheet(
                "color: #ef5350; font-size: 10px;")
            self._activity_log.log_error(text)

        def _on_dev_reload(self) -> None:
            """Developer: Close panel and reload all LKS modules."""
            self._activity_log.log_warn("Reloading LKS modules...")
            self._refresh_timer.stop()

            try:
                from utils.registration_utils import reload_modules, LKS_MODULES
                reloaded, failed = reload_modules(LKS_MODULES)
                self._activity_log.log_success(
                    f"Reloaded {reloaded} modules, {failed} failed")
            except Exception as e:
                self._activity_log.log_error(f"Reload failed: {e}")

            self.close()

            try:
                from pathlib import Path
                lks_script: str = str(
                    Path(__file__).parent / "LKS.py").replace("\\", "/")
                coat.io.step(2)
                coat.io.executeScript(lks_script)
            except Exception as e:
                print(f"[LKS] Failed to relaunch: {e}")

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
