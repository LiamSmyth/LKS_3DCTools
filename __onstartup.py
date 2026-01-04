"""
LKS cModule startup initialization.

This file is executed when 3DCoat starts and the LKS cModule is loaded.
It:
1. Adds LKS module path to sys.path for relative imports
2. Initializes Qt/PySide6 for non-blocking UI panels
3. Registers action scripts as menu items for hotkey assignment
"""
import sys
import os
from pathlib import Path

# =============================================================================
# PATH SETUP - Enable relative imports (from utils., from ops.)
# =============================================================================

# Get the LKS module root directory
_LKS_ROOT: Path = Path(__file__).parent.resolve()

# Add to sys.path if not already present (enables 'from utils.' imports)
if str(_LKS_ROOT) not in sys.path:
    sys.path.insert(0, str(_LKS_ROOT))
    print(f"[LKS] Added to sys.path: {_LKS_ROOT}")

# =============================================================================
# QT INITIALIZATION
# =============================================================================

app = None  # Global QApplication reference

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    # CRITICAL: Use desktop OpenGL to avoid conflicts with 3DCoat's rendering
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)

    # Create QApplication with no-opengl flag if not already created
    if not QApplication.instance():
        app = QApplication(["-no-opengl"])
        print("[LKS] Qt initialized successfully")
    else:
        app = QApplication.instance()
        print("[LKS] Qt already initialized")

except ImportError as e:
    print(f"[LKS] Warning: PySide6 not available: {e}")
    print("[LKS] Qt UI features will be disabled")
except Exception as e:
    print(f"[LKS] Error initializing Qt: {e}")

# =============================================================================
# MENU ITEM REGISTRATION (for user-assignable hotkeys)
# =============================================================================

try:
    import coat

    # Path to actions folder (use forward slashes for 3DCoat)
    _ACTIONS_PATH: str = str(_LKS_ROOT / "actions").replace("\\", "/")

    def _register_action(action_id: str, script_name: str, translation: str) -> None:
        """Register an action script as a menu item."""
        script_path: str = f"{_ACTIONS_PATH}/{script_name}"
        coat.ui.addTranslation(action_id, translation)
        if not coat.ui.checkIfMenuItemInserted(action_id):
            coat.ui.insertInMenu("SCRIPTS", action_id, script_path)

    # Register key action scripts for hotkey assignment
    # Users can assign hotkeys via Edit → Preferences → Hotkeys → search "LKS"
    _register_action("LKS_Decimate_Half_Selected",
                     "SculptObject_Decimate_Half_Selected.py", "LKS: Decimate Selected 50%")
    _register_action("LKS_Decimate_Half_Subtree",
                     "SculptObject_Decimate_Half_Subtree.py", "LKS: Decimate Subtree 50%")
    _register_action("LKS_ProxyToggle_Decimate16X",
                     "SculptObject_ProxyToggle_Decimate16X_Selected.py", "LKS: Proxy Toggle Decimate 16X")
    _register_action("LKS_Ghost_Toggle_Subtree",
                     "SculptObject_Ghost_Toggle_Subtree.py", "LKS: Ghost Toggle Subtree")
    _register_action("LKS_Ghost_Invert_All",
                     "SculptObject_Ghost_Invert_All.py", "LKS: Ghost Invert All")
    _register_action("LKS_Ghost_Isolate_Selected",
                     "SculptObject_Ghost_Isolate_Selected.py", "LKS: Ghost Isolate Selected")
    _register_action("LKS_Unghost_All",
                     "SculptObject_Unghost_All.py", "LKS: Unghost All")
    _register_action("LKS_Visibility_Toggle_Subtree",
                     "SculptObject_Visibility_Toggle_Subtree.py", "LKS: Visibility Toggle Subtree")
    _register_action("LKS_Scale_Down100x",
                     "SculptObject_Scale_Down100x_Selected.py", "LKS: Scale Down 100x")
    _register_action("LKS_Scale_Up100x",
                     "SculptObject_Scale_Up100x_Selected.py", "LKS: Scale Up 100x")
    _register_action("LKS_ToSurface_All",
                     "SculptObject_ToSurface_All.py", "LKS: Convert All to Surface")
    _register_action(
        "LKS_ToVoxel_All", "SculptObject_ToVoxel_All.py", "LKS: Convert All to Voxel")
    _register_action("LKS_Subdivide_Double_Subtree",
                     "SculptObject_Subdivide_Double_Subtree.py", "LKS: Subdivide Double Subtree")
    _register_action("LKS_Resample_Half_Subtree",
                     "SculptObject_Resample_Half_Subtree.py", "LKS: Resample Half Subtree")
    _register_action("LKS_RemeshResymm_Selected",
                     "SculptObject_RemeshResymm_Safe_Selected.py", "LKS: Remesh+Resymm Selected")
    _register_action("LKS_IdColors_FromParts",
                     "SculptObject_IdColors_FromParts.py", "LKS: ID Colors from Parts")
    _register_action("LKS_Autopo_Run", "Autopo_Run.py", "LKS: Autopo Run")
    _register_action("LKS_Autopo_ToSculpt",
                     "Autopo_ToSculpt.py", "LKS: Autopo to Sculpt")
    _register_action("LKS_Brush_IncrementDetails",
                     "Brush_IncrementDetailsLevel.py", "LKS: Brush Increment Details")
    _register_action("LKS_Brush_DecrementDetails",
                     "Brush_DecrementDetailsLevel.py", "LKS: Brush Decrement Details")

    print(f"[LKS] Registered {20} action scripts to SCRIPTS menu")
    print("[LKS] Assign hotkeys via Edit → Preferences → Hotkeys → search 'LKS'")

except Exception as e:
    print(f"[LKS] Error registering menu items: {e}")
