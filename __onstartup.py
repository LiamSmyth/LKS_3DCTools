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

# Add vendor/ to sys.path for lks_utils imports
_VENDOR: Path = _LKS_ROOT / "vendor"
if _VENDOR.exists() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))
    print(f"[LKS] Added vendor path: {_VENDOR}")

# =============================================================================
# DEPENDENCY INSTALL — lks_utils needs ftfy at import time
# =============================================================================
# ftfy is imported by lks_utils.text.normalization at module level.
# It must be installed before ANY lks_utils import chain fires later.
# 3DCoat's coat.io.pipInstall uses internal pip, not sys.executable.

try:
    import coat
    try:
        __import__("ftfy")
    except ImportError:
        print("[LKS] Installing dependency: ftfy...")
        try:
            coat.io.pipInstall("ftfy")
            print("[LKS]   Installed ftfy successfully")
        except Exception as _dep_e:
            print(f"[LKS]   WARNING: Failed to install ftfy: {_dep_e}")
except ImportError:
    pass  # coat not available (not running in 3DCoat)

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
# MENU ITEM REGISTRATION (DISABLED - use panel buttons instead)
# =============================================================================
# Menu registration is now manual via the LKS panel:
# - "📋 Menu" button: Register action scripts
# - "🗑️ Clear" button: Remove stale menu entries (requires restart)
#
# To re-enable auto-registration, uncomment the block below.

# try:
#     import coat
#     from utils.coat_menu_utils import initialize_lks_menu, get_actions_dir
#
#     # Auto-discover and register all action scripts
#     registered, skipped = initialize_lks_menu()
#
#     actions_dir = get_actions_dir()
#     print(f"[LKS] Scanned actions directory: {actions_dir}")
#     print(
#         f"[LKS] Registered {registered} action scripts ({skipped} already registered)")
#     print("[LKS] Assign hotkeys via Edit → Preferences → Hotkeys → search 'LKS'")
#
# except Exception as e:
#     import traceback
#     print(f"[LKS] Error registering menu items: {e}")
#     traceback.print_exc()

print("[LKS] Startup complete. Use panel buttons for menu registration.")

# =============================================================================
# FAST REIMPORT - Install MetaPathFinder for instant action script re-invocation
# =============================================================================

try:
    from utils.fast_reimport import FastReimportFinder
    FastReimportFinder.get_instance()
except Exception as e:
    print(f"[LKS] Warning: FastReimportFinder not installed: {e}")
