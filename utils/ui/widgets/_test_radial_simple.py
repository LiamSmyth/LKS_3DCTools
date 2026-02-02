"""
Simple standalone test for radial menu - verifies basic functionality.

This script tests the radial menu in a minimal Qt environment to catch
issues before testing in 3DCoat.

Usage:
    python _test_radial_simple.py
"""
from __future__ import annotations
from utils.ui.widgets import RadialMenuItem, get_manager
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import sys
from pathlib import Path

# Add LKS to path for imports
lks_root = Path(__file__).parent.parent
sys.path.insert(0, str(lks_root))


def test_simple_menu():
    """Test radial menu with simple items (no config)."""
    print("[Test] Creating simple radial menu...")

    # Create simple test items
    items = [
        RadialMenuItem(
            label="Action 1",
            action=lambda: print("Action 1 invoked!"),
            icon="1️⃣",
            angle=0  # Up
        ),
        RadialMenuItem(
            label="Action 2",
            action=lambda: print("Action 2 invoked!"),
            icon="2️⃣",
            angle=90  # Right
        ),
        RadialMenuItem(
            label="Action 3",
            action=lambda: print("Action 3 invoked!"),
            icon="3️⃣",
            angle=180  # Down
        ),
        RadialMenuItem(
            label="Action 4",
            action=lambda: print("Action 4 invoked!"),
            icon="4️⃣",
            angle=270  # Left
        ),
    ]

    # Show menu at screen center
    manager = get_manager()

    # Get screen center
    screen = QApplication.primaryScreen()
    screen_geom = screen.geometry()
    center_x = screen_geom.center().x()
    center_y = screen_geom.center().y()

    from PySide6.QtCore import QPoint
    pos = QPoint(center_x, center_y)

    print(f"[Test] Showing menu at ({center_x}, {center_y})")
    manager.show_menu(items, pos)

    print("[Test] Menu displayed. Move mouse to highlight items, press key to invoke.")
    print("[Test] Press Escape to close without invoking.")


def main():
    """Main entry point."""
    # Configure OpenGL before QApplication
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)

    # Create QApplication
    app = QApplication(["-no-opengl"])

    # Show menu
    test_simple_menu()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
