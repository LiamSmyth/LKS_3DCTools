#!/usr/bin/env python
"""
Standalone test runner for the hotkey editor.

Run from the LKS root directory:
    python utils/hotkey_editor/run_standalone.py
    python utils/hotkey_editor/run_standalone.py "C:/path/to/Options_Hotkeys.xml"
"""
from __future__ import annotations

import sys
from pathlib import Path

# Setup import paths to avoid loading utils/__init__.py
_SCRIPT_DIR = Path(__file__).parent
_UTILS_DIR = _SCRIPT_DIR.parent  
_LKS_ROOT = _UTILS_DIR.parent

# Insert LKS root AFTER hotkey_editor package so relative imports work
# But we need to make utils.hotkey_editor and utils.hotkey_utils importable
# without triggering utils/__init__.py

# Monkey-patch: create a fake utils module that only contains what we need
import types
fake_utils = types.ModuleType("utils")
fake_utils.__path__ = [str(_UTILS_DIR)]
sys.modules["utils"] = fake_utils

# Now we can import the hotkey_editor package using relative paths
# since we've set up utils without its __init__.py side effects


def main():
    """Run the hotkey editor standalone."""
    # Import after path setup
    from utils.hotkey_editor.qt_imports import HAS_QT
    
    if not HAS_QT:
        print("ERROR: PySide6 is required. Install with: pip install PySide6")
        return 1
    
    from PySide6.QtWidgets import QApplication
    from utils.hotkey_editor.main_window import HotkeyEditorWindow
    from utils.hotkey_editor.hotkey_imports import discover_hotkeys_path
    
    app = QApplication(sys.argv)
    
    # Parse path argument
    hotkeys_path: Path | None = None
    if len(sys.argv) > 1:
        hotkeys_path = Path(sys.argv[1])
    else:
        hotkeys_path = discover_hotkeys_path()
    
    if hotkeys_path:
        print(f"Loading: {hotkeys_path}")
    else:
        print("No hotkeys file specified or found. Opening empty editor.")
    
    window = HotkeyEditorWindow(hotkeys_path)
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
